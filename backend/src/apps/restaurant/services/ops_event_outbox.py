from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

from sqlmodel import select

from src.apps.restaurant.models import OpsEventOutbox, OpsEventOutboxStatus
from src.apps.websocket.manager import manager as ws_manager
from src.db.session import async_session_factory


class OpsEventOutboxDispatcher:
    """Background worker that delivers restaurant websocket outbox events."""

    def __init__(self, poll_interval_seconds: float = 1.5, batch_size: int = 25):
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def dispatch_once(self) -> int:
        """Drain one batch of due outbox rows. Returns processed row count."""
        now = datetime.utcnow()
        async with async_session_factory() as db:
            rows = (
                await db.execute(
                    select(OpsEventOutbox)
                    .where(
                        OpsEventOutbox.status.in_(
                            [OpsEventOutboxStatus.PENDING, OpsEventOutboxStatus.RETRY]
                        ),
                        OpsEventOutbox.next_attempt_at <= now,
                    )
                    .order_by(OpsEventOutbox.id.asc())
                    .limit(self._batch_size)
                )
            ).scalars().all()

            processed = 0
            for row in rows:
                processed += 1
                await self._deliver_row(db, row)

            await db.commit()
            return processed

    async def _run_loop(self) -> None:
        while not self._stopped.is_set():
            try:
                await self.dispatch_once()
            except Exception:
                # best-effort background worker
                pass
            await asyncio.sleep(self._poll_interval_seconds)

    async def _deliver_row(self, db, row: OpsEventOutbox) -> None:
        row.status = OpsEventOutboxStatus.IN_PROGRESS
        row.updated_at = datetime.utcnow()
        await db.flush()

        data = {
            "branch_id": row.branch_id,
            "severity": row.severity.value if hasattr(row.severity, "value") else str(row.severity),
            "payload": json.loads(row.payload_json or "{}"),
        }

        try:
            await ws_manager.push_event_to_room(
                room=row.room,
                event=row.event_name,
                data=data,
                event_id=row.event_id,
                occurred_at=row.occurred_at.isoformat(),
                attempt=row.attempt_count + 1,
            )
        except Exception as exc:
            row.attempt_count += 1
            row.last_error = str(exc)[:1000]
            row.updated_at = datetime.utcnow()
            if row.attempt_count >= row.max_attempts:
                row.status = OpsEventOutboxStatus.DEAD_LETTER
                row.dead_lettered_at = datetime.utcnow()
            else:
                delay = min(300, 2 ** row.attempt_count)
                row.status = OpsEventOutboxStatus.RETRY
                row.next_attempt_at = datetime.utcnow() + timedelta(seconds=delay)
            return

        row.attempt_count += 1
        row.status = OpsEventOutboxStatus.SENT
        row.sent_at = datetime.utcnow()
        row.updated_at = datetime.utcnow()
        row.last_error = None


ops_event_outbox_dispatcher = OpsEventOutboxDispatcher()

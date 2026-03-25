import base64
import json
import logging
from typing import Any

import httpx

from src.apps.analytics.interface import AnalyticsProvider
from src.apps.core.http import default_timeout, retry_async

logger = logging.getLogger(__name__)


class MixpanelAdapter(AnalyticsProvider):
    def __init__(self, project_token: str, host: str) -> None:
        self.project_token = project_token
        self.host = host.rstrip("/")

    async def capture(
        self,
        distinct_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "event": event,
            "properties": {
                "token": self.project_token,
                "distinct_id": distinct_id,
                **(properties or {}),
            },
        }
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        async with httpx.AsyncClient() as client:
            await retry_async(
                lambda: client.post(
                    f"{self.host}/track",
                    data={"data": encoded},
                    timeout=default_timeout(),
                )
            )

    async def identify(
        self,
        distinct_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        await self.capture(distinct_id, "$identify", properties or {})

    async def alias(self, distinct_id: str, alias: str) -> None:
        await self.capture(distinct_id, "$create_alias", {"alias": alias, "distinct_id": distinct_id})

    async def group(
        self,
        distinct_id: str,
        group_type: str,
        group_key: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        await self.capture(
            distinct_id,
            "$group_identify",
            {
                "$group_key": group_key,
                "$group_id": group_type,
                **(properties or {}),
            },
        )

    async def page(
        self,
        distinct_id: str,
        path: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        await self.capture(distinct_id, "$pageview", {"path": path, **(properties or {})})

    async def get_feature_flag(
        self,
        distinct_id: str,
        flag_key: str,
        default: bool = False,
    ) -> bool | str:
        return default

    async def get_all_feature_flags(self, distinct_id: str) -> dict[str, bool | str]:
        return {}

    async def flush(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core.config import (
    NON_RUNTIME_EDITABLE_SETTING_KEYS,
    PUBLIC_GENERAL_SETTING_KEYS,
    get_environment_settings_snapshot,
    settings,
)
from src.apps.core.models import GeneralSetting


async def sync_general_settings(session: AsyncSession) -> None:
    env_snapshot = get_environment_settings_snapshot()
    result = await session.execute(select(GeneralSetting))
    existing_settings = {item.key: item for item in result.scalars().all()}
    now = datetime.now()

    for key, env_value in env_snapshot.items():
        general_setting = existing_settings.get(key)
        if general_setting is None:
            session.add(
                GeneralSetting(
                    key=key,
                    env_value=env_value,
                    is_runtime_editable=key not in NON_RUNTIME_EDITABLE_SETTING_KEYS,
                )
            )
            continue

        general_setting.env_value = env_value
        general_setting.is_runtime_editable = key not in NON_RUNTIME_EDITABLE_SETTING_KEYS
        general_setting.updated_at = now
        session.add(general_setting)

    await session.commit()
    settings.refresh_from_database(force=True)


async def get_general_settings(session: AsyncSession) -> list[GeneralSetting]:
    result = await session.execute(select(GeneralSetting))
    return list(result.scalars().all())


def build_general_setting_payload(
    rows: Iterable[GeneralSetting],
    *,
    public_only: bool = False,
) -> list[dict[str, Any]]:
    env_snapshot = get_environment_settings_snapshot()
    rows_by_key = {row.key: row for row in rows}
    keys = PUBLIC_GENERAL_SETTING_KEYS if public_only else set(env_snapshot)
    payload: list[dict[str, Any]] = []

    for key in sorted(keys):
        row = rows_by_key.get(key)
        env_value = env_snapshot.get(key)
        db_value = row.db_value if row else None
        is_runtime_editable = (
            row.is_runtime_editable
            if row is not None
            else key not in NON_RUNTIME_EDITABLE_SETTING_KEYS
        )
        use_db_value = bool(
            row is not None
            and row.use_db_value
            and is_runtime_editable
            and db_value is not None
        )
        effective_value = db_value if use_db_value else env_value

        payload.append(
            {
                "key": key,
                "env_value": env_value,
                "db_value": db_value,
                "effective_value": effective_value,
                "source": "database" if use_db_value else "environment",
                "use_db_value": use_db_value,
                "is_runtime_editable": is_runtime_editable,
            }
        )

    return payload

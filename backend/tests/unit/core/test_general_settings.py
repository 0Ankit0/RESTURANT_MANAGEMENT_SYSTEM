from src.apps.core.config import (
    NON_RUNTIME_EDITABLE_SETTING_KEYS,
    PUBLIC_GENERAL_SETTING_KEYS,
    build_effective_settings,
    get_environment_settings_snapshot,
)
from src.apps.core.models import GeneralSetting
from src.apps.core.settings_store import build_general_setting_payload


def test_general_settings_snapshot_includes_all_known_settings() -> None:
    snapshot = get_environment_settings_snapshot()

    assert "PROJECT_NAME" in snapshot
    assert "APP_ENV" in snapshot
    assert "DATABASE_URL" in snapshot
    assert snapshot["PROJECT_NAME"] is not None


def test_build_effective_settings_prefers_enabled_database_value() -> None:
    resolved_settings = build_effective_settings(
        [
            {
                "key": "PROJECT_NAME",
                "db_value": "Database Project Name",
                "use_db_value": True,
                "is_runtime_editable": True,
            }
        ]
    )

    assert resolved_settings.PROJECT_NAME == "Database Project Name"


def test_build_effective_settings_ignores_non_runtime_editable_keys() -> None:
    resolved_settings = build_effective_settings(
        [
            {
                "key": "DATABASE_URL",
                "db_value": "sqlite+aiosqlite:///./override.db",
                "use_db_value": True,
                "is_runtime_editable": True,
            }
        ]
    )

    assert "DATABASE_URL" in NON_RUNTIME_EDITABLE_SETTING_KEYS
    assert "SECRET_KEY" in NON_RUNTIME_EDITABLE_SETTING_KEYS
    assert resolved_settings.DATABASE_URL != "sqlite+aiosqlite:///./override.db"


def test_public_general_settings_payload_uses_safe_allowlist() -> None:
    payload = build_general_setting_payload(
        [
            GeneralSetting(
                key="PROJECT_NAME",
                env_value="FastAPI Template",
                db_value="Runtime Project",
                use_db_value=True,
            )
        ],
        public_only=True,
    )

    keys = {item["key"] for item in payload}

    assert keys == PUBLIC_GENERAL_SETTING_KEYS
    assert "APP_ENV" in keys
    project_name = next(item for item in payload if item["key"] == "PROJECT_NAME")
    assert project_name["effective_value"] == "Runtime Project"
    assert project_name["source"] == "database"

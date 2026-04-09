import pytest

from src.db import session as db_session


@pytest.mark.asyncio
async def test_init_db_uses_migration_guard_outside_dev(monkeypatch):
    called = {"migration": False, "create_all": False, "sync": False}

    async def fake_assert() -> None:
        called["migration"] = True

    async def fake_sync(_session) -> None:
        called["sync"] = True

    class _Conn:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def run_sync(self, fn):
            called["create_all"] = True
            return fn(None)

    class _BeginCtx:
        async def __aenter__(self):
            return _Conn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(db_session.settings, "TESTING", False)
    monkeypatch.setattr(db_session.settings, "DEBUG", False)
    monkeypatch.setattr(db_session, "_assert_migrations_applied", fake_assert)
    monkeypatch.setattr(db_session, "sync_general_settings", fake_sync)
    monkeypatch.setattr(db_session.engine, "begin", lambda: _BeginCtx())

    await db_session.init_db()

    assert called["migration"] is True
    assert called["create_all"] is False
    assert called["sync"] is True

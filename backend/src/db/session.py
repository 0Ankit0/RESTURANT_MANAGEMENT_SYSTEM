from pathlib import Path
from typing import AsyncGenerator

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlmodel import SQLModel

from src.apps.core.config import settings
from src.apps.core.settings_store import sync_general_settings

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the configuration")

engine_kwargs: dict[str, object] = {
    "url": settings.DATABASE_URL,
    "echo": settings.LOG_SQL_QUERIES,
    "future": True,
    "poolclass": AsyncAdaptedQueuePool,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    "pool_timeout": settings.DB_POOL_TIMEOUT,
    "pool_recycle": settings.DB_POOL_RECYCLE,
}

engine = create_async_engine(**engine_kwargs)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


def _alembic_script_directory() -> ScriptDirectory:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    return ScriptDirectory.from_config(config)


async def _assert_migrations_applied() -> None:
    """Fail fast outside test/dev when DB is not on Alembic head."""
    script = _alembic_script_directory()
    head_revision = script.get_current_head()

    async with engine.connect() as conn:
        def _get_db_revision(sync_conn) -> str | None:
            context = MigrationContext.configure(sync_conn)
            return context.get_current_revision()

        db_revision = await conn.run_sync(_get_db_revision)

    if db_revision != head_revision:
        raise RuntimeError(
            "Database migrations are not up to date. "
            f"Expected Alembic head '{head_revision}', found '{db_revision}'. "
            "Run `alembic upgrade head` before starting the service."
        )


async def init_db() -> None:
    # Import all models so SQLModel.metadata knows about every table
    import src.apps.core.models  # noqa: F401
    import src.apps.finance.models  # noqa: F401
    import src.apps.iam.models  # noqa: F401
    import src.apps.multitenancy.models  # noqa: F401
    import src.apps.notification.models  # noqa: F401
    import src.apps.observability.models  # noqa: F401
    import src.apps.restaurant.models  # noqa: F401
    import src.apps.websocket.models  # noqa: F401

    # Keep create_all only for tests and local debug workflows.
    if settings.TESTING or settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    else:
        await _assert_migrations_applied()

    async with async_session_factory() as session:
        await sync_general_settings(session)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

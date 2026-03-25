from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlmodel import SQLModel
from src.apps.core.config import settings
from src.apps.core.settings_store import sync_general_settings

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the configuration")

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs: dict[str, object] = {
    "url": settings.DATABASE_URL,
    "echo": settings.LOG_SQL_QUERIES,
    "future": True,
    "poolclass": NullPool if _is_sqlite else AsyncAdaptedQueuePool,
}

if not _is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
    )

engine = create_async_engine(**engine_kwargs)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    # Import all models so SQLModel.metadata knows about every table
    import src.apps.core.models  # noqa: F401
    import src.apps.iam.models  # noqa: F401
    import src.apps.notification.models  # noqa: F401
    import src.apps.multitenancy.models  # noqa: F401
    import src.apps.finance.models  # noqa: F401
    import src.apps.websocket.models  # noqa: F401
    import src.apps.observability.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_factory() as session:
        await sync_general_settings(session)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

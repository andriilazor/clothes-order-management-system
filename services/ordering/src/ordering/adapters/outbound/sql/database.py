from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool


def create_engine(database_url: str) -> AsyncEngine:
    if database_url.startswith("sqlite"):
        # One shared connection, otherwise every session sees its own empty in-memory database.
        return create_async_engine(
            database_url, poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
    return create_async_engine(database_url)

import asyncio
import os

from alembic import context
from ordering.adapters.outbound.sql.tables import metadata
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine


def database_url() -> str:
    url = context.config.attributes.get("database_url") or os.environ.get("ORDERING_DATABASE_URL")
    if not url:
        raise RuntimeError("Set ORDERING_DATABASE_URL to run migrations")
    return str(url)


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(database_url())
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


asyncio.run(run_online())

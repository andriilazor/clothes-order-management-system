from collections.abc import AsyncIterator, Iterator

import pytest
from ordering.adapters.outbound.sql.database import create_engine
from ordering.adapters.outbound.sql.schema import prepare_schema
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="module")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17", driver="asyncpg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture
async def sessions(database_url: str) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(database_url)
    await prepare_schema(engine)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()

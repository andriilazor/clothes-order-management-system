import pytest
from ordering.adapters.outbound.sql.seeder import DEMO_CART_ID, seed_demo_carts
from ordering.adapters.outbound.sql.tables import carts
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration


# Seeding twice on a migrated database leaves exactly the 2 demo carts.
async def test_seeding_twice_does_not_duplicate_carts(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    # Act
    async with sessions() as session:
        await seed_demo_carts(session)
    async with sessions() as session:
        await seed_demo_carts(session)

    # Assert
    async with sessions() as session:
        count = await session.scalar(select(func.count()).select_from(carts))
        demo = await session.scalar(select(carts.c.id).where(carts.c.id == DEMO_CART_ID))
    assert count == 2
    assert demo == DEMO_CART_ID

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ordering.adapters.outbound.sql.repositories import SqlCartRepository
from ordering.adapters.outbound.sql.tables import carts
from ordering.domain.cart import Cart
from ordering.domain.value_objects import Quantity, Sku

DEMO_CART_ID = UUID("11111111-1111-1111-1111-111111111111")
EMPTY_CART_ID = UUID("22222222-2222-2222-2222-222222222222")

logger = logging.getLogger(__name__)


async def seed_demo_carts(session: AsyncSession) -> None:
    if await session.scalar(select(carts.c.id).limit(1)) is not None:
        logger.info("Database already contains carts; skipping seeding")
        return

    demo_cart = Cart(DEMO_CART_ID)
    demo_cart.add_item(Sku("DRESS-RED-M"), Quantity(4))
    demo_cart.add_item(Sku("JEANS-BLUE-32"), Quantity(1))
    empty_cart = Cart(EMPTY_CART_ID)

    repository = SqlCartRepository(session)
    await repository.save(demo_cart)
    await repository.save(empty_cart)
    logger.info("Seeded demo carts %s and %s", DEMO_CART_ID, EMPTY_CART_ID)

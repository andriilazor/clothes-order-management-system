from uuid import uuid4

import pytest
from ordering.adapters.outbound.sql.repositories import SqlCartRepository, SqlOrderRepository
from ordering.domain.cart import Cart, CartItem
from ordering.domain.order import Order, OrderStatus
from ordering.domain.value_objects import Quantity, Sku
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = pytest.mark.integration

DRESS = Sku("DRESS-RED-M")
JEANS = Sku("JEANS-BLUE-32")


# A saved cart is read back whole, with its items.
async def test_cart_is_saved_and_read_back(sessions: async_sessionmaker[AsyncSession]) -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(DRESS, Quantity(2))
    cart.add_item(JEANS, Quantity(1))
    async with sessions() as session:
        await SqlCartRepository(session).save(cart)

    # Act
    async with sessions() as session:
        loaded = await SqlCartRepository(session).get(cart.id)

    # Assert
    assert loaded is not None
    assert loaded.items == (CartItem(DRESS, Quantity(2)), CartItem(JEANS, Quantity(1)))


# "Item removed from cart" is persisted on the next save.
async def test_removed_item_is_gone_after_save(sessions: async_sessionmaker[AsyncSession]) -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(DRESS, Quantity(2))
    async with sessions() as session:
        await SqlCartRepository(session).save(cart)

    # Act
    async with sessions() as session:
        carts = SqlCartRepository(session)
        loaded = await carts.get(cart.id)
        assert loaded is not None
        loaded.remove_item(DRESS)
        await carts.save(loaded)
    async with sessions() as session:
        reloaded = await SqlCartRepository(session).get(cart.id)

    # Assert
    assert reloaded is not None
    assert reloaded.items == ()


# An order keeps its items and status; it is found by cart and listed.
async def test_order_is_saved_found_and_listed(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(DRESS, Quantity(2))
    order = Order.place(cart)
    async with sessions() as session:
        await SqlOrderRepository(session).add(order)

    # Act
    async with sessions() as session:
        orders = SqlOrderRepository(session)
        found = await orders.get_by_cart_id(cart.id)
        listed = await orders.list_all()

    # Assert
    assert found is not None
    assert found.status == OrderStatus.PLACED
    assert found.items == order.items
    assert order.id in {o.id for o in listed}

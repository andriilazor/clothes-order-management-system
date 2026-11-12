from collections import defaultdict
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from ordering.adapters.outbound.sql.tables import cart_items, carts, order_items, orders
from ordering.domain.cart import Cart, CartItem
from ordering.domain.order import Order


class SqlCartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, cart_id: UUID) -> Cart | None:
        rows = await self._session.execute(
            select(carts.c.id, cart_items.c.sku, cart_items.c.quantity)
            .select_from(carts.outerjoin(cart_items))
            .where(carts.c.id == cart_id)
            .order_by(cart_items.c.sku)
        )
        found = rows.all()
        if not found:
            return None
        cart = Cart(cart_id)
        for _, sku, quantity in found:
            if sku is not None:
                cart.add_item(sku, quantity)
        return cart

    async def save(self, cart: Cart) -> None:
        exists = await self._session.scalar(select(carts.c.id).where(carts.c.id == cart.id))
        if exists is None:
            await self._session.execute(insert(carts).values(id=cart.id))
        await self._session.execute(delete(cart_items).where(cart_items.c.cart_id == cart.id))
        if cart.items:
            await self._session.execute(
                insert(cart_items),
                [{"cart_id": cart.id, "sku": i.sku, "quantity": i.quantity} for i in cart.items],
            )
        await self._session.commit()


class SqlOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_cart_id(self, cart_id: UUID) -> Order | None:
        rows = await self._session.execute(select(orders).where(orders.c.cart_id == cart_id))
        found = await self._with_items(rows.all())
        return found[0] if found else None

    async def add(self, order: Order) -> None:
        await self._session.execute(
            insert(orders).values(id=order.id, cart_id=order.cart_id, status=order.status)
        )
        await self._session.execute(
            insert(order_items),
            [{"order_id": order.id, "sku": i.sku, "quantity": i.quantity} for i in order.items],
        )
        await self._session.commit()

    async def list_all(self) -> tuple[Order, ...]:
        rows = await self._session.execute(select(orders).order_by(orders.c.id))
        return await self._with_items(rows.all())

    async def _with_items(self, order_rows: Sequence[Row[Any]]) -> tuple[Order, ...]:
        if not order_rows:
            return ()
        item_rows = await self._session.execute(
            select(order_items)
            .where(order_items.c.order_id.in_([row.id for row in order_rows]))
            .order_by(order_items.c.sku)
        )
        items: defaultdict[UUID, list[CartItem]] = defaultdict(list)
        for item in item_rows:
            items[item.order_id].append(CartItem(item.sku, item.quantity))
        return tuple(
            Order(row.id, row.cart_id, tuple(items[row.id]), row.status) for row in order_rows
        )

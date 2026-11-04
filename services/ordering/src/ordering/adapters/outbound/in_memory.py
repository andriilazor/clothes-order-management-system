from uuid import UUID

from ordering.domain.cart import Cart
from ordering.domain.order import Order


class InMemoryCartRepository:
    def __init__(self) -> None:
        self._carts: dict[UUID, Cart] = {}

    async def get(self, cart_id: UUID) -> Cart | None:
        return self._carts.get(cart_id)

    async def save(self, cart: Cart) -> None:
        self._carts[cart.id] = cart


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders_by_cart: dict[UUID, Order] = {}

    async def get_by_cart_id(self, cart_id: UUID) -> Order | None:
        return self._orders_by_cart.get(cart_id)

    async def add(self, order: Order) -> None:
        self._orders_by_cart[order.cart_id] = order

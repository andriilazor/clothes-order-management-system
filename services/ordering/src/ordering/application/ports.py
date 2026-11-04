from typing import Protocol
from uuid import UUID

from ordering.domain.cart import Cart
from ordering.domain.order import Order


class CartRepository(Protocol):
    async def get(self, cart_id: UUID) -> Cart | None: ...


class OrderRepository(Protocol):
    async def get_by_cart_id(self, cart_id: UUID) -> Order | None: ...

    async def add(self, order: Order) -> None: ...

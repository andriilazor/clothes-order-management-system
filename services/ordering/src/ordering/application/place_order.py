from uuid import UUID

from ordering.application.ports import CartRepository, OrderRepository
from ordering.domain.order import Order


class PlaceOrder:
    def __init__(self, carts: CartRepository, orders: OrderRepository) -> None:
        self._carts = carts
        self._orders = orders

    async def execute(self, cart_id: UUID) -> Order:
        raise NotImplementedError

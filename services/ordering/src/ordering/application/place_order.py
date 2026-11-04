from uuid import UUID

from ordering.application.ports import CartRepository, OrderRepository
from ordering.domain.order import Order
from ordering.domain.errors import CartNotFound


class PlaceOrder:
    def __init__(self, carts: CartRepository, orders: OrderRepository) -> None:
        self._carts = carts
        self._orders = orders

    async def execute(self, cart_id: UUID) -> Order:
        cart = await self._carts.get(cart_id)
        if cart is None:
            raise CartNotFound(cart_id)
        return Order.place(cart)
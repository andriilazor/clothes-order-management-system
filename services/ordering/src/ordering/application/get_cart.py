from uuid import UUID

from ordering.application.ports import CartRepository
from ordering.domain.cart import Cart
from ordering.domain.errors import CartNotFound


class GetCart:
    def __init__(self, carts: CartRepository) -> None:
        self._carts = carts

    async def execute(self, cart_id: UUID) -> Cart:
        cart = await self._carts.get(cart_id)
        if cart is None:
            raise CartNotFound(cart_id)
        return cart

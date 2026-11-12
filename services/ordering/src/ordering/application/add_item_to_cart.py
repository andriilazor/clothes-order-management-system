from uuid import UUID

from ordering.application.ports import CartRepository
from ordering.domain.cart import Cart
from ordering.domain.value_objects import Quantity, Sku


class AddItemToCart:
    def __init__(self, carts: CartRepository) -> None:
        self._carts = carts

    async def execute(self, cart_id: UUID, sku: Sku, quantity: Quantity) -> Cart:
        cart = await self._carts.get(cart_id)
        if cart is None:
            cart = Cart(cart_id)
        cart.add_item(sku, quantity)
        await self._carts.save(cart)
        return cart

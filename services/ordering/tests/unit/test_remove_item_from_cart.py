from uuid import UUID, uuid4

import pytest
from ordering.application.remove_item_from_cart import RemoveItemFromCart
from ordering.domain.cart import Cart
from ordering.domain.errors import CartNotFound, ItemNotInCart
from ordering.domain.value_objects import Quantity, Sku

DRESS = Sku("DRESS-RED-M")


class FakeCartRepository:
    def __init__(self, *carts: Cart) -> None:
        self.saved = {cart.id: cart for cart in carts}
        self.save_calls = 0

    async def get(self, cart_id: UUID) -> Cart | None:
        return self.saved.get(cart_id)

    async def save(self, cart: Cart) -> None:
        self.saved[cart.id] = cart
        self.save_calls += 1


# "Item removed from cart": the item is gone and the cart is saved.
async def test_remove_item_takes_item_out_and_saves_cart() -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(DRESS, Quantity(2))
    carts = FakeCartRepository(cart)

    # Act
    result = await RemoveItemFromCart(carts).execute(cart.id, DRESS)

    # Assert
    assert result.items == ()
    assert carts.save_calls == 1


# "Removal rejected, item not in cart"; nothing is saved.
async def test_remove_item_rejects_sku_not_in_cart() -> None:
    # Arrange
    cart = Cart(uuid4())
    carts = FakeCartRepository(cart)

    # Act & Assert
    with pytest.raises(ItemNotInCart):
        await RemoveItemFromCart(carts).execute(cart.id, DRESS)
    assert carts.save_calls == 0


# An unknown cart is reported.
async def test_remove_item_rejects_unknown_cart() -> None:
    # Act & Assert
    with pytest.raises(CartNotFound):
        await RemoveItemFromCart(FakeCartRepository()).execute(uuid4(), DRESS)

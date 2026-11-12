from uuid import UUID, uuid4

import pytest
from ordering.application.get_cart import GetCart
from ordering.domain.cart import Cart
from ordering.domain.errors import CartNotFound


class FakeCartRepository:
    def __init__(self, *carts: Cart) -> None:
        self.saved = {cart.id: cart for cart in carts}

    async def get(self, cart_id: UUID) -> Cart | None:
        return self.saved.get(cart_id)

    async def save(self, cart: Cart) -> None:
        self.saved[cart.id] = cart


# "Cart summary": an existing cart is returned.
async def test_get_cart_returns_existing_cart() -> None:
    # Arrange
    cart = Cart(uuid4())

    # Act
    result = await GetCart(FakeCartRepository(cart)).execute(cart.id)

    # Assert
    assert result is cart


# An unknown cart is reported.
async def test_get_cart_rejects_unknown_cart() -> None:
    # Act & Assert
    with pytest.raises(CartNotFound):
        await GetCart(FakeCartRepository()).execute(uuid4())

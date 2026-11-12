from uuid import UUID, uuid4

import pytest
from ordering.application.add_item_to_cart import AddItemToCart
from ordering.domain.cart import Cart
from ordering.domain.errors import QuantityLimitExceeded
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


# "Add item to cart" on a new cart: the cart is created and saved.
async def test_add_item_creates_and_saves_new_cart() -> None:
    # Arrange
    carts = FakeCartRepository()
    cart_id = uuid4()

    # Act
    cart = await AddItemToCart(carts).execute(cart_id, DRESS, Quantity(2))

    # Assert
    assert carts.saved[cart_id] is cart
    assert cart.items[0].quantity == Quantity(2)


# Adding to an existing cart keeps what is already there.
async def test_add_item_updates_existing_cart() -> None:
    # Arrange
    existing = Cart(uuid4())
    existing.add_item(DRESS, Quantity(2))
    carts = FakeCartRepository(existing)

    # Act
    cart = await AddItemToCart(carts).execute(existing.id, DRESS, Quantity(3))

    # Assert
    assert cart is existing
    assert cart.items[0].quantity == Quantity(5)


# The 5-unit limit surfaces through the service; nothing is saved.
async def test_add_item_rejects_more_than_five_units() -> None:
    # Arrange
    existing = Cart(uuid4())
    existing.add_item(DRESS, Quantity(4))
    carts = FakeCartRepository(existing)

    # Act & Assert
    with pytest.raises(QuantityLimitExceeded):
        await AddItemToCart(carts).execute(existing.id, DRESS, Quantity(2))
    assert carts.save_calls == 0

from uuid import UUID, uuid4

import pytest
from ordering.application.add_item_to_cart import AddItemToCart
from ordering.domain.cart import Cart
from ordering.domain.errors import InvalidQuantity


class FakeCartRepository:
    def __init__(self, *carts: Cart) -> None:
        self.saved = {cart.id: cart for cart in carts}

    async def get(self, cart_id: UUID) -> Cart | None:
        return self.saved.get(cart_id)

    async def save(self, cart: Cart) -> None:
        self.saved[cart.id] = cart


# "Add item to cart" on a new cart: the cart is created and saved.
async def test_add_item_creates_and_saves_new_cart() -> None:
    # Arrange
    carts = FakeCartRepository()
    cart_id = uuid4()

    # Act
    cart = await AddItemToCart(carts).execute(cart_id, "SKU-1", 2)

    # Assert
    assert carts.saved[cart_id] is cart
    assert cart.items[0].quantity == 2


# Adding to an existing cart keeps what is already there.
async def test_add_item_updates_existing_cart() -> None:
    # Arrange
    existing = Cart(uuid4())
    existing.add_item("SKU-1", 2)
    carts = FakeCartRepository(existing)

    # Act
    cart = await AddItemToCart(carts).execute(existing.id, "SKU-1", 3)

    # Assert
    assert cart is existing
    assert cart.items[0].quantity == 5


# The domain rule on quantity surfaces through the service; nothing is saved.
async def test_add_item_rejects_invalid_quantity() -> None:
    # Arrange
    carts = FakeCartRepository()

    # Act & Assert
    with pytest.raises(InvalidQuantity):
        await AddItemToCart(carts).execute(uuid4(), "SKU-1", 0)
    assert carts.saved == {}

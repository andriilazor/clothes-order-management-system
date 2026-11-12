from uuid import uuid4

import pytest
from ordering.domain.cart import Cart
from ordering.domain.errors import ItemNotInCart, QuantityLimitExceeded
from ordering.domain.value_objects import Quantity, Sku

DRESS = Sku("DRESS-RED-M")


@pytest.fixture
def cart() -> Cart:
    return Cart(uuid4())


# "Add item to cart": the item lands in the cart with its quantity.
def test_add_item_puts_item_in_cart(cart: Cart) -> None:
    # Act
    cart.add_item(DRESS, Quantity(2))

    # Assert
    assert len(cart.items) == 1
    assert cart.items[0].sku == DRESS
    assert cart.items[0].quantity == Quantity(2)


# The same SKU never appears twice.
def test_adding_same_sku_twice_merges_quantities(cart: Cart) -> None:
    # Arrange
    cart.add_item(DRESS, Quantity(2))

    # Act
    cart.add_item(DRESS, Quantity(3))

    # Assert
    assert len(cart.items) == 1
    assert cart.items[0].quantity == Quantity(5)


# "At most 5 units of one size and colour per order"; the cart keeps its line.
def test_add_item_rejects_more_than_five_units_of_one_sku(cart: Cart) -> None:
    # Arrange
    cart.add_item(DRESS, Quantity(4))

    # Act & Assert
    with pytest.raises(QuantityLimitExceeded):
        cart.add_item(DRESS, Quantity(2))
    assert cart.items[0].quantity == Quantity(4)


# "Item removed from cart": the item disappears from the cart.
def test_remove_item_takes_item_out_of_cart(cart: Cart) -> None:
    # Arrange
    cart.add_item(DRESS, Quantity(2))

    # Act
    cart.remove_item(DRESS)

    # Assert
    assert cart.items == ()


# Only an item that is in the cart can be removed.
def test_remove_item_rejects_sku_not_in_cart(cart: Cart) -> None:
    # Act & Assert
    with pytest.raises(ItemNotInCart):
        cart.remove_item(Sku("SKU-9"))


# Items is read-only, there is no setter.
def test_items_cannot_be_assigned(cart: Cart) -> None:
    # Act & Assert
    with pytest.raises(AttributeError):
        cart.items = ()  # type: ignore[misc]

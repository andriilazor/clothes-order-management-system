from uuid import uuid4

import pytest
from ordering.domain.cart import Cart
from ordering.domain.errors import InvalidQuantity, ItemNotInCart


@pytest.fixture
def cart() -> Cart:
    return Cart(uuid4())


# "Add item to cart": the item lands in the cart with its quantity.
def test_add_item_puts_item_in_cart(cart: Cart) -> None:
    # Act
    cart.add_item("SKU-1", 2)

    # Assert
    assert len(cart.items) == 1
    assert cart.items[0].sku == "SKU-1"
    assert cart.items[0].quantity == 2


# The same SKU never appears twice.
def test_adding_same_sku_twice_merges_quantities(cart: Cart) -> None:
    # Arrange
    cart.add_item("SKU-1", 2)

    # Act
    cart.add_item("SKU-1", 3)

    # Assert
    assert len(cart.items) == 1
    assert cart.items[0].quantity == 5


# Quantity must be positive; one rule, several invalid values.
@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_add_item_rejects_non_positive_quantity(cart: Cart, quantity: int) -> None:
    # Act & Assert
    with pytest.raises(InvalidQuantity):
        cart.add_item("SKU-1", quantity)


# "Item removed from cart": the item disappears from the cart.
def test_remove_item_takes_item_out_of_cart(cart: Cart) -> None:
    # Arrange
    cart.add_item("SKU-1", 2)

    # Act
    cart.remove_item("SKU-1")

    # Assert
    assert cart.items == ()


# Only an item that is in the cart can be removed.
def test_remove_item_rejects_sku_not_in_cart(cart: Cart) -> None:
    # Act & Assert
    with pytest.raises(ItemNotInCart):
        cart.remove_item("SKU-9")


# Items is read-only, there is no setter.
def test_items_cannot_be_assigned(cart: Cart) -> None:
    # Act & Assert
    with pytest.raises(AttributeError):
        cart.items = ()  # type: ignore[misc]

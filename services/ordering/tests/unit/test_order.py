from uuid import uuid4

import pytest
from ordering.domain.cart import Cart
from ordering.domain.errors import EmptyCart, InvalidOrderTransition
from ordering.domain.order import Order, OrderStatus
from ordering.domain.value_objects import Quantity, Sku


@pytest.fixture
def order() -> Order:
    cart = Cart(uuid4())
    cart.add_item(Sku("SKU-1"), Quantity(2))
    return Order.place(cart)


# "Place order": a new order starts as placed and carries the cart items.
def test_place_creates_placed_order_with_cart_items() -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(Sku("SKU-1"), Quantity(2))

    # Act
    order = Order.place(cart)

    # Assert
    assert order.status == OrderStatus.PLACED
    assert order.items == cart.items
    assert order.cart_id == cart.id


# An empty cart cannot become an order.
def test_place_rejects_empty_cart() -> None:
    # Arrange
    empty_cart = Cart(uuid4())

    # Act & Assert
    with pytest.raises(EmptyCart):
        Order.place(empty_cart)


# Placed -> confirmed -> completed.
def test_confirm_then_complete_finishes_order(order: Order) -> None:
    # Act
    order.confirm()
    order.complete()

    # Assert
    assert order.status == OrderStatus.COMPLETED


# Statuses move only forward in order; every other move is forbidden.
@pytest.mark.parametrize(
    ("steps", "action"),
    [
        ([], "complete"),
        (["confirm"], "confirm"),
        (["confirm", "complete"], "confirm"),
        (["confirm", "complete"], "complete"),
    ],
)
def test_invalid_transition_is_rejected(order: Order, steps: list[str], action: str) -> None:
    # Arrange
    for step in steps:
        getattr(order, step)()

    # Act & Assert
    with pytest.raises(InvalidOrderTransition):
        getattr(order, action)()


# An order read back from storage keeps the status it was saved with.
def test_order_restored_with_status_keeps_it(order: Order) -> None:
    # Act
    restored = Order(order.id, order.cart_id, order.items, OrderStatus.CONFIRMED)

    # Assert
    assert restored.status == OrderStatus.CONFIRMED


# Status changes only through behaviour, there is no setter.
def test_status_cannot_be_assigned(order: Order) -> None:
    # Act & Assert
    with pytest.raises(AttributeError):
        order.status = OrderStatus.COMPLETED  # type: ignore[misc]

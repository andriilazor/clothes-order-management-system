from uuid import UUID, uuid4

from ordering.application.list_orders import ListOrders
from ordering.domain.cart import Cart
from ordering.domain.order import Order
from ordering.domain.value_objects import Quantity, Sku


class FakeOrderRepository:
    def __init__(self, *orders: Order) -> None:
        self.saved = {order.id: order for order in orders}

    async def get_by_cart_id(self, cart_id: UUID) -> Order | None:
        return next((o for o in self.saved.values() if o.cart_id == cart_id), None)

    async def add(self, order: Order) -> None:
        self.saved[order.id] = order

    async def list_all(self) -> tuple[Order, ...]:
        return tuple(self.saved.values())


# "Order status for the customer": every saved order is listed.
async def test_list_orders_returns_all_orders() -> None:
    # Arrange
    cart = Cart(uuid4())
    cart.add_item(Sku("DRESS-RED-M"), Quantity(1))
    order = Order.place(cart)

    # Act
    result = await ListOrders(FakeOrderRepository(order)).execute()

    # Assert
    assert result == (order,)

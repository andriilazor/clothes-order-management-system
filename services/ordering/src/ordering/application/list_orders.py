from ordering.application.ports import OrderRepository
from ordering.domain.order import Order


class ListOrders:
    def __init__(self, orders: OrderRepository) -> None:
        self._orders = orders

    async def execute(self) -> tuple[Order, ...]:
        return await self._orders.list_all()

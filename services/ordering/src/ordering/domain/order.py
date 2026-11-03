from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from ordering.domain.cart import Cart, CartItem
from ordering.domain.errors import EmptyCart, InvalidOrderTransition


class OrderStatus(StrEnum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"


class Order:
    def __init__(self, id: UUID, items: tuple[CartItem, ...]) -> None:
        self._id = id
        self._items = items
        self._status = OrderStatus.PLACED

    @classmethod
    def place(cls, cart: Cart) -> Self:
        if not cart.items:
            raise EmptyCart
        return cls(uuid4(), cart.items)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def items(self) -> tuple[CartItem, ...]:
        return self._items

    @property
    def status(self) -> OrderStatus:
        return self._status

    def confirm(self) -> None:
        self._transition(OrderStatus.PLACED, OrderStatus.CONFIRMED)

    def complete(self) -> None:
        self._transition(OrderStatus.CONFIRMED, OrderStatus.COMPLETED)

    def _transition(self, expected: OrderStatus, new: OrderStatus) -> None:
        if self._status != expected:
            raise InvalidOrderTransition(f"{self._status} -> {new}")
        self._status = new

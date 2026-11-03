from enum import StrEnum
from typing import Self
from uuid import UUID


class ReservationStatus(StrEnum):
    RESERVED = "reserved"


class StockReservation:
    def __init__(self, order_id: UUID, items: dict[str, int]) -> None:
        self._order_id = order_id
        self._items = dict(items)
        self._status: ReservationStatus | None = None

    @classmethod
    def reserve(cls, order_id: UUID, items: dict[str, int]) -> Self:
        reservation = cls(order_id, items)
        reservation._status = ReservationStatus.RESERVED
        return reservation

    @property
    def order_id(self) -> UUID:
        return self._order_id

    @property
    def status(self) -> ReservationStatus | None:
        return self._status

from enum import StrEnum
from uuid import UUID


class ShipmentStatus(StrEnum):
    CREATED = "created"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"


class Shipment:
    def __init__(self, id: UUID, order_id: UUID) -> None:
        self._id = id
        self._order_id = order_id
        self._status = ShipmentStatus.CREATED

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def order_id(self) -> UUID:
        return self._order_id

    @property
    def status(self) -> ShipmentStatus:
        return self._status

    def hand_over_to_carrier(self) -> None:
        self._status = ShipmentStatus.DISPATCHED

    def confirm_delivery(self) -> None:
        self._status = ShipmentStatus.DELIVERED

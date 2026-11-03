from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class PaymentStatus(StrEnum):
    PENDING = "pending"
    AUTHORISED = "authorised"
    REJECTED = "rejected"


class Payment:
    def __init__(self, id: UUID, order_id: UUID, amount: Decimal) -> None:
        self._id = id
        self._order_id = order_id
        self._amount = amount
        self._status = PaymentStatus.PENDING

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def status(self) -> PaymentStatus:
        return self._status

    def authorise(self) -> None:
        self._status = PaymentStatus.AUTHORISED

    def reject(self) -> None:
        self._status = PaymentStatus.REJECTED

from dataclasses import dataclass
from typing import Self

from ordering.domain.errors import InvalidQuantity, InvalidSku, QuantityLimitExceeded

MAX_UNITS_PER_SKU = 5


@dataclass(frozen=True)
class Sku:
    code: str

    def __post_init__(self) -> None:
        if not self.code or self.code != self.code.upper() or any(c.isspace() for c in self.code):
            raise InvalidSku(self.code)

    @classmethod
    def parse(cls, raw: str) -> Self:
        return cls(raw.upper())


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if not 1 <= self.value <= MAX_UNITS_PER_SKU:
            raise InvalidQuantity(self.value)

    def add(self, other: Self) -> Self:
        total = self.value + other.value
        if total > MAX_UNITS_PER_SKU:
            raise QuantityLimitExceeded(total)
        return type(self)(total)

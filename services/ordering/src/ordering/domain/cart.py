from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class CartItem:
    sku: str
    quantity: int

class Cart:
    def __init__(self, id: UUID) -> None:
        self._id = id
        self._quantities: dict[str, int] = {}

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(CartItem(sku, quantity) for sku, quantity in self._quantities.items())

    def add_item(self, sku: str, quantity: int) -> None:
        self._quantities[sku] = self._quantities.get(sku, 0) + quantity
        
    def remove_item(self, sku: str) -> None:
        self._quantities.pop(sku, None)

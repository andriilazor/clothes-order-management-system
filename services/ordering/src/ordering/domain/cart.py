from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CartItem:
    sku: str
    quantity: int


class Cart:
    def __init__(self, id: UUID) -> None:
        self._id = id
        self._items: list[CartItem] = []

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(self._items)

    def add_item(self, sku: str, quantity: int) -> None:
        self._items.append(CartItem(sku, quantity))

    def remove_item(self, sku: str) -> None:
        self._items = [item for item in self._items if item.sku != sku]

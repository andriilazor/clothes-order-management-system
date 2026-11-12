from dataclasses import dataclass
from uuid import UUID

from ordering.domain.errors import ItemNotInCart
from ordering.domain.value_objects import Quantity, Sku


@dataclass(frozen=True)
class CartItem:
    sku: Sku
    quantity: Quantity


class Cart:
    def __init__(self, id: UUID) -> None:
        self._id = id
        self._quantities: dict[Sku, Quantity] = {}

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(CartItem(sku, quantity) for sku, quantity in self._quantities.items())

    def add_item(self, sku: Sku, quantity: Quantity) -> None:
        current = self._quantities.get(sku)
        self._quantities[sku] = quantity if current is None else current.add(quantity)

    def remove_item(self, sku: Sku) -> None:
        if sku not in self._quantities:
            raise ItemNotInCart(sku.code)
        del self._quantities[sku]

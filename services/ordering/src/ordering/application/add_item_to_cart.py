from uuid import UUID

from ordering.application.ports import CartRepository
from ordering.domain.cart import Cart

class AddItemToCart:
  def __init__(self, carts: CartRepository) -> None:
    self._carts = carts
    
  async def execute(self, cart_id: UUID, sku: str, quantity: int) -> Cart:
    raise NotImplementedError
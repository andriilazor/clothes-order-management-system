from uuid import UUID, uuid4
import pytest

from ordering.application.place_order import PlaceOrder
from ordering.domain.cart import Cart
from ordering.domain.errors import CartNotFound, EmptyCart
from ordering.domain.order import Order, OrderStatus


class FakeCartRepository:
  def __init__(self, *carts: Cart) -> None:
    self._carts = {cart.id: cart for cart in carts}
    
  async def get(self, cart_id: UUID) -> Cart | None:
    return self._carts.get(cart_id)
  
    
class FakeOrderRepository:
  def __init__(self) -> None:
      self.saved: dict[UUID, Order] = {}

  async def get_by_cart_id(self, cart_id: UUID) -> Order | None:
      return self.saved.get(cart_id)

  async def add(self, order: Order) -> None:
      self.saved[order.cart_id] = order
      
      
@pytest.fixture
def cart() -> Cart:
  cart = Cart(uuid4())
  cart.add_item("SKU-1", 2)
  return cart

@pytest.fixture
def orders() -> FakeOrderRepository:
  return FakeOrderRepository()


@pytest.fixture
def place_order(cart: Cart, orders: FakeOrderRepository) -> PlaceOrder:
    return PlaceOrder(FakeCartRepository(cart), orders)
  

# "Place order": the order is created from the cart's items.
async def test_place_order_creates_placed_order_from_cart(place_order: PlaceOrder, cart: Cart) -> None:
    # Act
    order = await place_order.execute(cart.id)

    # Assert
    assert order.status == OrderStatus.PLACED
    assert order.items == cart.items
    

# The service hands the order to the repository.
async def test_place_order_saves_order(place_order: PlaceOrder, cart: Cart, orders: FakeOrderRepository) -> None:
    # Act
    order = await place_order.execute(cart.id)

    # Assert
    assert orders.saved[cart.id] is order
    
    
# An unknown cart is reported; nothing is saved.
async def test_place_order_rejects_unknown_cart(place_order: PlaceOrder, orders: FakeOrderRepository) -> None:
    # Act & Assert
    with pytest.raises(CartNotFound):
        await place_order.execute(uuid4())
    assert orders.saved == {}


# Forbids "empty cart" to be placed; nothing is saved.
async def test_place_order_rejects_empty_cart(orders: FakeOrderRepository) -> None:
    # Arrange
    empty_cart = Cart(uuid4())
    place_order = PlaceOrder(FakeCartRepository(empty_cart), orders)

    # Act & Assert
    with pytest.raises(EmptyCart):
        await place_order.execute(empty_cart.id)
    assert orders.saved == {}


# "Duplicate order submission ignored": the second call returns the first order.
async def test_duplicate_submission_returns_existing_order(place_order: PlaceOrder, cart: Cart, orders: FakeOrderRepository) -> None:
    # Arrange
    first = await place_order.execute(cart.id)

    # Act
    second = await place_order.execute(cart.id)

    # Assert
    assert second is first
    assert len(orders.saved) == 1
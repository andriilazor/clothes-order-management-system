from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from ordering.application.add_item_to_cart import AddItemToCart
from ordering.application.place_order import PlaceOrder
from ordering.domain.cart import CartItem


class AddItemRequest(BaseModel):
    sku: str
    quantity: int


class ItemResponse(BaseModel):
    sku: str
    quantity: int


class CartResponse(BaseModel):
    id: UUID
    items: list[ItemResponse]


class PlaceOrderRequest(BaseModel):
    cart_id: UUID


class OrderResponse(BaseModel):
    id: UUID
    cart_id: UUID
    status: str
    items: list[ItemResponse]


def item_responses(items: tuple[CartItem, ...]) -> list[ItemResponse]:
    return [ItemResponse(sku=item.sku, quantity=item.quantity) for item in items]


def create_router(add_item_to_cart: AddItemToCart, place_order: PlaceOrder) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post("/carts/{cart_id}/items")
    async def add_item(cart_id: UUID, request: AddItemRequest) -> CartResponse:
        cart = await add_item_to_cart.execute(cart_id, request.sku, request.quantity)
        return CartResponse(id=cart.id, items=item_responses(cart.items))

    @router.post("/orders", status_code=status.HTTP_201_CREATED)
    async def create_order(request: PlaceOrderRequest) -> OrderResponse:
        order = await place_order.execute(request.cart_id)
        return OrderResponse(
            id=order.id,
            cart_id=order.cart_id,
            status=order.status,
            items=item_responses(order.items),
        )

    return router

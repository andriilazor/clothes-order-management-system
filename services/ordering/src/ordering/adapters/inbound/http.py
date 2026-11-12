from collections.abc import AsyncIterator, Callable
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from ordering.application.add_item_to_cart import AddItemToCart
from ordering.application.get_cart import GetCart
from ordering.application.list_orders import ListOrders
from ordering.application.place_order import PlaceOrder
from ordering.application.ports import Repositories
from ordering.application.remove_item_from_cart import RemoveItemFromCart
from ordering.domain.cart import Cart, CartItem
from ordering.domain.order import Order
from ordering.domain.value_objects import Quantity, Sku


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
    return [ItemResponse(sku=item.sku.code, quantity=item.quantity.value) for item in items]


def cart_response(cart: Cart) -> CartResponse:
    return CartResponse(id=cart.id, items=item_responses(cart.items))


def order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id, cart_id=order.cart_id, status=order.status, items=item_responses(order.items)
    )


def create_router(get_repositories: Callable[[], AsyncIterator[Repositories]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    repositories_per_request = Depends(get_repositories)

    @router.get("/carts/{cart_id}")
    async def get_cart(
        cart_id: UUID, repositories: Repositories = repositories_per_request
    ) -> CartResponse:
        cart = await GetCart(repositories.carts).execute(cart_id)
        return cart_response(cart)

    @router.post("/carts/{cart_id}/items")
    async def add_item(
        cart_id: UUID,
        request: AddItemRequest,
        repositories: Repositories = repositories_per_request,
    ) -> CartResponse:
        cart = await AddItemToCart(repositories.carts).execute(
            cart_id, Sku.parse(request.sku), Quantity(request.quantity)
        )
        return cart_response(cart)

    @router.delete("/carts/{cart_id}/items/{sku}")
    async def remove_item(
        cart_id: UUID, sku: str, repositories: Repositories = repositories_per_request
    ) -> CartResponse:
        cart = await RemoveItemFromCart(repositories.carts).execute(cart_id, Sku.parse(sku))
        return cart_response(cart)

    @router.post("/orders", status_code=status.HTTP_201_CREATED)
    async def create_order(
        request: PlaceOrderRequest, repositories: Repositories = repositories_per_request
    ) -> OrderResponse:
        order = await PlaceOrder(repositories.carts, repositories.orders).execute(request.cart_id)
        return order_response(order)

    @router.get("/orders")
    async def list_orders(
        repositories: Repositories = repositories_per_request,
    ) -> list[OrderResponse]:
        return [order_response(o) for o in await ListOrders(repositories.orders).execute()]

    return router

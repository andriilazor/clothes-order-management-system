from fastapi import FastAPI

from ordering.adapters.inbound.errors import handle_domain_error
from ordering.adapters.inbound.http import create_router
from ordering.adapters.outbound.in_memory import InMemoryCartRepository, InMemoryOrderRepository
from ordering.application.add_item_to_cart import AddItemToCart
from ordering.application.place_order import PlaceOrder
from ordering.domain.errors import DomainError


def create_app() -> FastAPI:
    carts = InMemoryCartRepository()
    orders = InMemoryOrderRepository()
    app = FastAPI(title="Ordering")
    app.include_router(create_router(AddItemToCart(carts), PlaceOrder(carts, orders)))
    app.add_exception_handler(DomainError, handle_domain_error)
    return app

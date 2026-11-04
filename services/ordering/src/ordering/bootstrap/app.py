from fastapi import FastAPI

from ordering.adapters.inbound.http import create_router
from ordering.adapters.outbound.in_memory import InMemoryCartRepository
from ordering.application.add_item_to_cart import AddItemToCart


def create_app() -> FastAPI:
    carts = InMemoryCartRepository()
    app = FastAPI(title="Ordering")
    app.include_router(create_router(AddItemToCart(carts)))
    return app

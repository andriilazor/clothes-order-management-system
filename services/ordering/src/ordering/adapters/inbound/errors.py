from fastapi import Request
from fastapi.responses import JSONResponse

from ordering.domain.errors import (
    CartNotFound,
    EmptyCart,
    InvalidOrderTransition,
    InvalidQuantity,
    ItemNotInCart,
)

STATUS_BY_ERROR: dict[type[Exception], int] = {
    CartNotFound: 404,
    ItemNotInCart: 404,
    InvalidQuantity: 422,
    EmptyCart: 422,
    InvalidOrderTransition: 409,
}


async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
    status_code = STATUS_BY_ERROR.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"status": status_code, "code": type(exc).__name__, "detail": str(exc)},
        media_type="application/problem+json",
    )

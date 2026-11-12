from sqlalchemy import Column, Dialect, Enum, ForeignKey, Integer, MetaData, String, Table, Uuid
from sqlalchemy.types import TypeDecorator

from ordering.domain.order import OrderStatus
from ordering.domain.value_objects import Quantity, Sku


class SkuType(TypeDecorator[Sku]):
    impl = String(64)
    cache_ok = True

    def process_bind_param(self, value: Sku | None, dialect: Dialect) -> str | None:
        return None if value is None else value.code

    def process_result_value(self, value: str | None, dialect: Dialect) -> Sku | None:
        return None if value is None else Sku(value)


class QuantityType(TypeDecorator[Quantity]):
    impl = Integer
    cache_ok = True

    def process_bind_param(self, value: Quantity | None, dialect: Dialect) -> int | None:
        return None if value is None else value.value

    def process_result_value(self, value: int | None, dialect: Dialect) -> Quantity | None:
        return None if value is None else Quantity(value)


order_status = Enum(
    OrderStatus,
    native_enum=False,
    length=32,
    values_callable=lambda statuses: [status.value for status in statuses],
)

metadata = MetaData()

carts = Table(
    "carts",
    metadata,
    Column("id", Uuid, primary_key=True),
)

cart_items = Table(
    "cart_items",
    metadata,
    Column("cart_id", Uuid, ForeignKey("carts.id", ondelete="CASCADE"), primary_key=True),
    Column("sku", SkuType, primary_key=True),
    Column("quantity", QuantityType, nullable=False),
)

orders = Table(
    "orders",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("cart_id", Uuid, nullable=False, unique=True),
    Column("status", order_status, nullable=False),
)

order_items = Table(
    "order_items",
    metadata,
    Column("order_id", Uuid, ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("sku", SkuType, primary_key=True),
    Column("quantity", QuantityType, nullable=False),
)

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Address:
    id: UUID
    user_id: UUID
    street: str
    postal_code: str
    city: str
    is_default: bool


class AddressNotFound(Exception):
    pass

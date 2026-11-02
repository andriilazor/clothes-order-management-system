from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    CUSTOMER = "customer"
    OPERATIONS = "operations"
    FINANCE = "finance"


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    password_hash: str
    role: Role
    created_at: datetime


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass

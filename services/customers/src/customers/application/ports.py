from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from customers.domain.address import Address
from customers.domain.profile import Profile
from customers.domain.user import User


@dataclass(frozen=True)
class AccessToken:
    value: str
    expires_in: int


class UserRepository(Protocol):
    async def find_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenIssuer(Protocol):
    def issue(self, user: User) -> AccessToken: ...


class AddressRepository(Protocol):
    async def list(self, user_id: UUID) -> list[Address]: ...

    async def find(self, address_id: UUID, user_id: UUID) -> Address | None: ...

    async def save(self, address: Address) -> None: ...

    async def delete(self, address_id: UUID) -> None: ...


class ProfileRepository(Protocol):
    async def find(self, user_id: UUID) -> Profile | None: ...

    async def save(self, profile: Profile) -> None: ...

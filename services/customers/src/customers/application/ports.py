from dataclasses import dataclass
from typing import Protocol

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

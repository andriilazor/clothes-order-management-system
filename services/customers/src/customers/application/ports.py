from typing import Protocol

from customers.domain.user import User


class UserRepository(Protocol):
    async def find_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

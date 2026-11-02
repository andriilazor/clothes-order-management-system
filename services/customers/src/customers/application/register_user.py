from datetime import UTC, datetime
from uuid import uuid4

from customers.application.ports import PasswordHasher, UserRepository
from customers.domain.user import EmailAlreadyRegistered, Role, User


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, email: str, password: str) -> User:
        email = email.lower()
        if await self._users.find_by_email(email):
            raise EmailAlreadyRegistered(email)
        user = User(
            id=uuid4(),
            email=email,
            password_hash=self._hasher.hash(password),
            role=Role.CUSTOMER,
            created_at=datetime.now(UTC),
        )
        await self._users.add(user)
        return user

import pytest
from customers.application.ports import AccessToken, PasswordHasher, TokenIssuer, UserRepository
from customers.domain.user import User


class InMemoryUsers:
    def __init__(self) -> None:
        self.by_email: dict[str, User] = {}

    async def find_by_email(self, email: str) -> User | None:
        return self.by_email.get(email)

    async def add(self, user: User) -> None:
        self.by_email[user.email] = user


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return self.hash(password) == password_hash


class FakeTokens:
    def issue(self, user: User) -> AccessToken:
        return AccessToken(value=str(user.id), expires_in=900)


@pytest.fixture
def users() -> UserRepository:
    return InMemoryUsers()


@pytest.fixture
def hasher() -> PasswordHasher:
    return FakeHasher()


@pytest.fixture
def tokens() -> TokenIssuer:
    return FakeTokens()

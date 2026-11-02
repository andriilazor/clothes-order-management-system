from uuid import UUID

import pytest
from customers.application.ports import (
    AccessToken,
    AddressRepository,
    PasswordHasher,
    ProfileRepository,
    TokenIssuer,
    UserRepository,
)
from customers.domain.address import Address
from customers.domain.profile import Profile
from customers.domain.user import User


class InMemoryUsers:
    def __init__(self) -> None:
        self.by_email: dict[str, User] = {}

    async def find_by_email(self, email: str) -> User | None:
        return self.by_email.get(email)

    async def add(self, user: User) -> None:
        self.by_email[user.email] = user


class InMemoryAddresses:
    def __init__(self) -> None:
        self.by_id: dict[UUID, Address] = {}

    async def list(self, user_id: UUID) -> list[Address]:
        return [a for a in self.by_id.values() if a.user_id == user_id]

    async def find(self, address_id: UUID, user_id: UUID) -> Address | None:
        address = self.by_id.get(address_id)
        return address if address and address.user_id == user_id else None

    async def save(self, address: Address) -> None:
        self.by_id[address.id] = address

    async def delete(self, address_id: UUID) -> None:
        del self.by_id[address_id]


class InMemoryProfiles:
    def __init__(self) -> None:
        self.by_user_id: dict[UUID, Profile] = {}

    async def find(self, user_id: UUID) -> Profile | None:
        return self.by_user_id.get(user_id)

    async def save(self, profile: Profile) -> None:
        self.by_user_id[profile.user_id] = profile


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


@pytest.fixture
def addresses() -> AddressRepository:
    return InMemoryAddresses()


@pytest.fixture
def profiles() -> ProfileRepository:
    return InMemoryProfiles()

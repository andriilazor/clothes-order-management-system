import pytest
from customers.application.register_user import RegisterUser
from customers.domain.user import EmailAlreadyRegistered, Role, User


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


@pytest.fixture
def users() -> InMemoryUsers:
    return InMemoryUsers()


@pytest.fixture
def register(users: InMemoryUsers) -> RegisterUser:
    return RegisterUser(users, FakeHasher())


@pytest.mark.req("FR-CUS-01", "US-01")
async def test_registers_a_customer_with_a_hashed_password(
    register: RegisterUser, users: InMemoryUsers
) -> None:
    user = await register.execute("anna@example.com", "secret")

    assert user.role is Role.CUSTOMER
    assert user.password_hash == "hashed:secret"
    assert users.by_email["anna@example.com"] == user


@pytest.mark.req("FR-CUS-01", "US-01")
async def test_refuses_an_email_that_is_already_registered(register: RegisterUser) -> None:
    await register.execute("anna@example.com", "secret")

    with pytest.raises(EmailAlreadyRegistered):
        await register.execute("Anna@Example.com", "other")

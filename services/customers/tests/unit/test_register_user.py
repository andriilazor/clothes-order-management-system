import pytest
from customers.application.ports import PasswordHasher, UserRepository
from customers.application.register_user import RegisterUser
from customers.domain.user import EmailAlreadyRegistered, Role


@pytest.mark.req("FR-CUS-01", "US-01")
async def test_registers_a_customer_with_a_hashed_password(
    users: UserRepository, hasher: PasswordHasher
) -> None:
    user = await RegisterUser(users, hasher).execute("anna@example.com", "secret")

    assert user.role is Role.CUSTOMER
    assert user.password_hash != "secret"
    assert hasher.verify("secret", user.password_hash)
    assert await users.find_by_email("anna@example.com") == user


@pytest.mark.req("FR-CUS-01", "US-01")
async def test_refuses_an_email_that_is_already_registered(
    users: UserRepository, hasher: PasswordHasher
) -> None:
    register = RegisterUser(users, hasher)
    await register.execute("anna@example.com", "secret")

    with pytest.raises(EmailAlreadyRegistered):
        await register.execute("Anna@Example.com", "other")

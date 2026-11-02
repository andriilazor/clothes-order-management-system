import pytest
from customers.application.login_user import LoginUser
from customers.application.ports import PasswordHasher, TokenIssuer, UserRepository
from customers.application.register_user import RegisterUser
from customers.domain.user import InvalidCredentials


@pytest.fixture
def login(users: UserRepository, hasher: PasswordHasher, tokens: TokenIssuer) -> LoginUser:
    return LoginUser(users, hasher, tokens)


@pytest.fixture(autouse=True)
async def registered_user(users: UserRepository, hasher: PasswordHasher) -> None:
    await RegisterUser(users, hasher).execute("anna@example.com", "secret")


@pytest.mark.req("FR-CUS-02", "US-01")
async def test_returns_an_expiring_token_for_correct_credentials(
    login: LoginUser, users: UserRepository
) -> None:
    token = await login.execute("Anna@example.com", "secret")

    user = await users.find_by_email("anna@example.com")
    assert user is not None
    assert token.value == str(user.id)
    assert token.expires_in > 0


@pytest.mark.req("FR-CUS-02", "US-01")
@pytest.mark.parametrize(
    ("email", "password"),
    [("anna@example.com", "wrong"), ("nobody@example.com", "secret")],
)
async def test_refuses_wrong_credentials_without_saying_which_was_wrong(
    login: LoginUser, email: str, password: str
) -> None:
    with pytest.raises(InvalidCredentials):
        await login.execute(email, password)

from customers.application.ports import AccessToken, PasswordHasher, TokenIssuer, UserRepository
from customers.domain.user import InvalidCredentials


class LoginUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenIssuer) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def execute(self, email: str, password: str) -> AccessToken:
        user = await self._users.find_by_email(email.lower())
        if user is None or not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentials
        return self._tokens.issue(user)

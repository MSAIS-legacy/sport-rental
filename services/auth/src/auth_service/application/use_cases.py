from uuid import uuid4

from ..domain.entities import AuthError, DuplicateUser, InvalidCredentials, User
from .ports import PasswordHasher, TokenIssuer


class Service:
    def __init__(self, uow_factory, hasher: PasswordHasher, issuer: TokenIssuer):
        self.uow_factory, self.hasher, self.issuer = uow_factory, hasher, issuer
        self.dummy_hash = hasher.hash("dummy-password-for-timing-only")

    def register(self, username, password, role="reader"):
        if len(password) < 12 or len(password) > 128:
            raise AuthError("Пароль должен содержать от 12 до 128 символов")
        user = User(str(uuid4()), username, self.hasher.hash(password), role)
        with self.uow_factory() as uow:
            if any(x.username == user.username for x in uow.repository.list("users", User)):
                raise DuplicateUser("Пользователь уже существует")
            uow.repository.save("users", user)
        return user

    def login(self, username, password):
        with self.uow_factory() as uow:
            user = next(
                (x for x in uow.repository.list("users", User) if x.username == username.strip().lower()),
                None,
            )
        verified = self.hasher.verify(user.password_hash if user else self.dummy_hash, password)
        if not user or not verified:
            raise InvalidCredentials("Неверное имя пользователя или пароль")
        return self.issuer.issue(user)

    def change_role(self, identifier, role):
        with self.uow_factory() as uow:
            user = uow.repository.get("users", identifier, User)
            user.change_role(role)
            uow.repository.save("users", user)
            return user

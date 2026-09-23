from dataclasses import dataclass


class AuthError(Exception):
    pass


class DuplicateUser(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


@dataclass
class User:
    id: str
    username: str
    password_hash: str
    role: str = "reader"

    def __post_init__(self):
        self.username = self.username.strip().lower()
        if not self.username:
            raise AuthError("Имя пользователя не может быть пустым")
        self.change_role(self.role)

    def change_role(self, role):
        if role not in {"reader", "operator", "admin"}:
            raise AuthError("Неизвестная роль")
        self.role = role

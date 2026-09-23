from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password_hash: str, password: str) -> bool: ...


class TokenIssuer(Protocol):
    def issue(self, user) -> str: ...


class UnitOfWork(Protocol):
    repository: object

    def __enter__(self): ...
    def __exit__(self, exc_type, exc, traceback): ...

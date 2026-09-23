from typing import Any, Protocol, Self


class Repository(Protocol):
    def get(self, kind: str, identifier: str, entity_type: type) -> Any: ...
    def list(self, kind: str, entity_type: type) -> list[Any]: ...
    def save(self, kind: str, entity: Any) -> None: ...


class UnitOfWork(Protocol):
    repository: Repository

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...


class CustomerGateway(Protocol):
    def validate_customer(self, customer_id: str) -> None: ...


class DependencyUnavailable(Exception):
    pass

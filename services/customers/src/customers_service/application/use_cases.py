from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import Customer
from .ports import UnitOfWork

KINDS = {"customers": Customer}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_customer(self, full_name, phone, email=None):
        with self.uow_factory() as uow:
            entity = Customer(str(uuid4()), full_name, phone, email)
            uow.repository.save("customers", entity)
            return entity

    def block_customer(self, identifier, reason):
        with self.uow_factory() as uow:
            entity = uow.repository.get("customers", identifier, Customer)
            entity.block(reason)
            uow.repository.save("customers", entity)
            return entity

    def unblock_customer(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("customers", identifier, Customer)
            entity.unblock()
            uow.repository.save("customers", entity)
            return entity

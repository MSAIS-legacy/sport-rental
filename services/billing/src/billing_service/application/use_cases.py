from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import Deposit, Payment
from ..domain.errors import Conflict
from .ports import UnitOfWork

KINDS = {"payments": Payment, "deposits": Deposit}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_payment(self, contract_id, amount, reference):
        with self.uow_factory() as uow:
            entity = Payment(str(uuid4()), contract_id, amount, reference)
            for existing in uow.repository.list("payments", Payment):
                if existing.reference == entity.reference:
                    if existing.contract_id == contract_id and existing.amount == amount:
                        return existing
                    raise Conflict("Номер операции уже использован с другими параметрами")
            uow.repository.save("payments", entity)
            return entity

    def confirm_payment(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("payments", identifier, Payment)
            entity.confirm()
            uow.repository.save("payments", entity)
            return entity

    def refund_payment(self, identifier, amount):
        with self.uow_factory() as uow:
            entity = uow.repository.get("payments", identifier, Payment)
            entity.refund(amount)
            uow.repository.save("payments", entity)
            return entity

    def create_deposit(self, contract_id, amount):
        with self.uow_factory() as uow:
            entity = Deposit(str(uuid4()), contract_id, amount)
            if any(x.contract_id == contract_id for x in uow.repository.list("deposits", Deposit)):
                raise Conflict("Для договора уже существует залог")
            uow.repository.save("deposits", entity)
            return entity

    def settle_deposit(self, identifier, amount, kind, reason=None):
        with self.uow_factory() as uow:
            entity = uow.repository.get("deposits", identifier, Deposit)
            entity.settle(amount, kind, reason)
            uow.repository.save("deposits", entity)
            return entity

from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import DamageReport, ServiceOrder
from ..domain.errors import Conflict
from .ports import UnitOfWork

KINDS = {"orders": ServiceOrder, "damage-reports": DamageReport}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_order(self, item_id, description):
        with self.uow_factory() as uow:
            if any(
                x.item_id == item_id and x.status == "open"
                for x in uow.repository.list("orders", ServiceOrder)
            ):
                raise Conflict("Для экземпляра уже открыт заказ на обслуживание")
            entity = ServiceOrder(str(uuid4()), item_id, description)
            uow.repository.save("orders", entity)
            return entity

    def complete_order(self, identifier, result):
        with self.uow_factory() as uow:
            entity = uow.repository.get("orders", identifier, ServiceOrder)
            entity.complete(result)
            uow.repository.save("orders", entity)
            return entity

    def create_damage_report(self, item_id, description, estimated_cost, contract_id=None):
        with self.uow_factory() as uow:
            entity = DamageReport(str(uuid4()), item_id, description, estimated_cost, contract_id)
            uow.repository.save("damage-reports", entity)
            return entity

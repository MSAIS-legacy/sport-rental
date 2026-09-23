from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import InventoryItem, RentalPoint, Transfer
from ..domain.errors import Conflict
from .ports import UnitOfWork

KINDS = {"points": RentalPoint, "items": InventoryItem, "transfers": Transfer}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_point(self, name, address):
        with self.uow_factory() as uow:
            entity = RentalPoint(str(uuid4()), name, address)
            uow.repository.save("points", entity)
            return entity

    def create_item(self, model_id, inventory_number, point_id):
        with self.uow_factory() as uow:
            uow.repository.get("points", point_id, RentalPoint)
            entity = InventoryItem(str(uuid4()), model_id, inventory_number, point_id)
            if any(
                item.inventory_number == entity.inventory_number
                for item in uow.repository.list("items", InventoryItem)
            ):
                raise Conflict("Инвентарный номер уже существует")
            uow.repository.save("items", entity)
            return entity

    def change_item_status(self, identifier, status):
        with self.uow_factory() as uow:
            entity = uow.repository.get("items", identifier, InventoryItem)
            if entity.status == "in_transit" or status == "in_transit":
                raise Conflict("Для перемещения используйте API transfers")
            entity.change_status(status)
            uow.repository.save("items", entity)
            return entity

    def create_transfer(self, item_ids, source_point_id, destination_point_id):
        with self.uow_factory() as uow:
            uow.repository.get("points", source_point_id, RentalPoint)
            uow.repository.get("points", destination_point_id, RentalPoint)
            entity = Transfer(str(uuid4()), item_ids, source_point_id, destination_point_id)
            for item_id in entity.item_ids:
                item = uow.repository.get("items", item_id, InventoryItem)
                if item.point_id != source_point_id or item.status != "available":
                    raise Conflict("Инвентарь недоступен в пункте отправления")
                item.change_status("in_transit")
                uow.repository.save("items", item)
            uow.repository.save("transfers", entity)
            return entity

    def complete_transfer(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("transfers", identifier, Transfer)
            entity.complete()
            for item_id in entity.item_ids:
                item = uow.repository.get("items", item_id, InventoryItem)
                item.change_status("available")
                item.point_id = entity.destination_point_id
                uow.repository.save("items", item)
            uow.repository.save("transfers", entity)
            return entity

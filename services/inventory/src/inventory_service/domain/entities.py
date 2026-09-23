from dataclasses import dataclass

from .errors import Conflict
from .values import require, text


@dataclass
class RentalPoint:
    id: str
    name: str
    address: str

    def __post_init__(self):
        self.name = text(self.name)
        self.address = text(self.address, "Адрес")


@dataclass
class InventoryItem:
    id: str
    model_id: str
    inventory_number: str
    point_id: str
    status: str = "available"

    def __post_init__(self):
        self.inventory_number = text(self.inventory_number, "Инвентарный номер")

    def change_status(self, target: str):
        allowed = {
            "available": {"rented", "maintenance", "in_transit"},
            "rented": {"available"},
            "maintenance": {"available"},
            "in_transit": {"available"},
        }
        if target not in allowed.get(self.status, set()):
            raise Conflict(f"Недопустимый переход {self.status} → {target}")
        self.status = target


@dataclass
class Transfer:
    id: str
    item_ids: list[str]
    source_point_id: str
    destination_point_id: str
    status: str = "in_transit"

    def __post_init__(self):
        require(bool(self.item_ids), "Перемещение должно содержать инвентарь")
        require(len(self.item_ids) == len(set(self.item_ids)), "Экземпляры не должны повторяться")
        require(self.source_point_id != self.destination_point_id, "Пункты должны отличаться")

    def complete(self):
        if self.status != "in_transit":
            raise Conflict("Перемещение уже завершено")
        self.status = "completed"

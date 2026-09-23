from dataclasses import dataclass

from .errors import Conflict
from .values import Money, text


@dataclass
class ServiceOrder:
    id: str
    item_id: str
    description: str
    status: str = "open"
    result: str | None = None

    def __post_init__(self):
        self.description = text(self.description, "Описание работ")

    def complete(self, result: str):
        if self.status != "open":
            raise Conflict("Заказ уже завершён")
        self.result = text(result, "Результат обслуживания")
        self.status = "completed"


@dataclass
class DamageReport:
    id: str
    item_id: str
    description: str
    estimated_cost: int
    contract_id: str | None = None

    def __post_init__(self):
        self.description = text(self.description, "Описание повреждения")
        Money(self.estimated_cost)

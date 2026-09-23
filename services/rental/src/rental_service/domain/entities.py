from dataclasses import dataclass

from .errors import Conflict
from .values import Money, Period, require, text


@dataclass
class Tariff:
    id: str
    name: str
    daily_rate: int

    def __post_init__(self):
        self.name = text(self.name)
        Money(self.daily_rate)
        require(self.daily_rate > 0, "Ставка должна быть положительной")

    def calculate(self, period: Period, item_count: int) -> int:
        return self.daily_rate * period.days() * item_count


@dataclass
class Booking:
    id: str
    customer_id: str
    item_ids: list[str]
    start: str
    end: str
    tariff_id: str
    total: int
    status: str = "confirmed"

    def __post_init__(self):
        Period(self.start, self.end)
        Money(self.total)
        require(bool(self.item_ids), "Бронирование должно содержать инвентарь")
        require(len(self.item_ids) == len(set(self.item_ids)), "Экземпляры не должны повторяться")

    def cancel(self):
        if self.status != "confirmed":
            raise Conflict("Можно отменить только подтверждённое бронирование")
        self.status = "cancelled"

    def convert(self):
        if self.status != "confirmed":
            raise Conflict("По этому бронированию нельзя оформить договор")
        self.status = "converted"


@dataclass
class RentalContract:
    id: str
    booking_id: str
    customer_id: str
    item_ids: list[str]
    start: str
    end: str
    total: int
    status: str = "active"

    def close(self):
        if self.status != "active":
            raise Conflict("Договор уже закрыт")
        self.status = "closed"

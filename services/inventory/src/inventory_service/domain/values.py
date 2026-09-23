from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import DomainError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DomainError(message)


def text(value: str, field: str = "Значение") -> str:
    value = value.strip()
    require(bool(value), f"{field} не может быть пустым")
    return value


@dataclass(frozen=True)
class Money:
    # Целые копейки, одна валюта RUB для учебной версии.
    amount: int

    def __post_init__(self):
        require(
            type(self.amount) is int and self.amount >= 0,
            "Сумма должна быть неотрицательным целым числом копеек",
        )


@dataclass(frozen=True)
class Period:
    start: str
    end: str

    def __post_init__(self):
        start, end = self.datetimes()
        require(start < end, "Начало периода должно предшествовать окончанию")

    def datetimes(self):
        try:
            start = datetime.fromisoformat(self.start)
            end = datetime.fromisoformat(self.end)
        except ValueError as error:
            raise DomainError("Некорректный формат даты") from error
        require(start.tzinfo is not None and end.tzinfo is not None, "Время должно содержать часовой пояс")
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    def overlaps(self, other: "Period") -> bool:
        start, end = self.datetimes()
        other_start, other_end = other.datetimes()
        return start < other_end and other_start < end

    def days(self) -> int:
        import math

        start, end = self.datetimes()
        return math.ceil((end - start).total_seconds() / 86400)

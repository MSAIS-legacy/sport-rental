from dataclasses import dataclass, field

from .errors import Conflict
from .values import Money, require, text


@dataclass
class Payment:
    id: str
    contract_id: str
    amount: int
    reference: str
    status: str = "pending"
    refunded: int = 0

    def __post_init__(self):
        Money(self.amount)
        require(self.amount > 0, "Платёж должен быть положительным")
        self.reference = text(self.reference, "Номер операции")

    def confirm(self):
        # Повторное подтверждение не создаёт новый платёж.
        self.status = "succeeded"

    def refund(self, amount: int):
        Money(amount)
        require(amount > 0, "Возврат должен быть положительным")
        if self.status != "succeeded":
            raise Conflict("Нельзя вернуть неподтверждённый платёж")
        if self.refunded + amount > self.amount:
            raise Conflict("Возврат превышает оплаченную сумму")
        self.refunded += amount


@dataclass
class Deposit:
    id: str
    contract_id: str
    amount: int
    returned: int = 0
    withheld: int = 0
    operations: list[dict] = field(default_factory=list)

    def __post_init__(self):
        Money(self.amount)
        require(self.amount > 0, "Залог должен быть положительным")

    def settle(self, amount: int, kind: str, reason: str | None = None):
        Money(amount)
        require(amount > 0, "Сумма операции должна быть положительной")
        require(kind in {"return", "withhold"}, "Неизвестный вид операции")
        if self.returned + self.withheld + amount > self.amount:
            raise Conflict("Недостаточно средств залога")
        if kind == "withhold":
            reason = text(reason or "", "Основание удержания")
            self.withheld += amount
        else:
            self.returned += amount
        self.operations.append({"kind": kind, "amount": amount, "reason": reason})

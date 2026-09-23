from dataclasses import dataclass

from .errors import Conflict


@dataclass
class Checkout:
    """Состояние процесса saga, а не новый бизнес-контекст."""

    id: str
    booking_id: str
    contract_id: str
    item_ids: list[str]
    amount: int
    payment_token: str
    status: str = "reserving"
    error: str | None = None

    def transition(self, expected, target):
        if self.status != expected:
            raise Conflict(f"Ожидалось {expected}, текущее состояние {self.status}")
        self.status = target

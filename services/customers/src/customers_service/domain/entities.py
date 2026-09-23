from dataclasses import dataclass

from .values import text


@dataclass
class Customer:
    id: str
    full_name: str
    phone: str
    email: str | None = None
    blocked: bool = False
    block_reason: str | None = None

    def __post_init__(self):
        self.full_name = text(self.full_name, "ФИО")
        self.phone = text(self.phone, "Телефон")

    def block(self, reason: str):
        self.block_reason = text(reason, "Причина ограничения")
        self.blocked = True

    def unblock(self):
        self.blocked = False
        self.block_reason = None

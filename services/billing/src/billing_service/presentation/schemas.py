from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaymentCreate(Input):
    contract_id: UUID
    amount: PositiveAmount
    reference: Name


class RefundPayment(Input):
    amount: PositiveAmount


class DepositCreate(Input):
    contract_id: UUID
    amount: PositiveAmount


class DepositSettlement(Input):
    amount: PositiveAmount
    kind: Literal["return", "withhold"]
    reason: Name | None = None

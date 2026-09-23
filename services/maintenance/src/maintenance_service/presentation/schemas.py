from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrderCreate(Input):
    item_id: UUID
    description: Name


class CompleteOrder(Input):
    result: Name


class DamageReportCreate(Input):
    item_id: UUID
    description: Name
    estimated_cost: Annotated[int, Field(ge=0, strict=True)]
    contract_id: UUID | None = None

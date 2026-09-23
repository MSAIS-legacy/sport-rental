from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TariffCreate(Input):
    name: Name
    daily_rate: PositiveAmount


class BookingCreate(Input):
    customer_id: UUID
    item_ids: list[UUID] = Field(min_length=1)
    start: AwareDatetime
    end: AwareDatetime
    tariff_id: UUID


class ContractCreate(Input):
    booking_id: UUID

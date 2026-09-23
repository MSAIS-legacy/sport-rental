from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PointCreate(Input):
    name: Name
    address: Name


class ItemCreate(Input):
    model_id: UUID
    inventory_number: Name
    point_id: UUID


class ItemStatus(Input):
    status: Literal["available", "rented", "maintenance"]


class TransferCreate(Input):
    item_ids: list[UUID] = Field(min_length=1)
    source_point_id: UUID
    destination_point_id: UUID

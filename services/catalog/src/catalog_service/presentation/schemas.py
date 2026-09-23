from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CategoryCreate(Input):
    name: Name
    parent_id: UUID | None = None


class ModelCreate(Input):
    name: Name
    manufacturer: Name
    category_id: UUID
    specifications: dict[str, str] = Field(default_factory=dict)

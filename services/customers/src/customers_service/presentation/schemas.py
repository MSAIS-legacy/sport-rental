from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PositiveAmount = Annotated[int, Field(gt=0, strict=True)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CustomerCreate(Input):
    full_name: Name
    phone: Name
    email: str | None = Field(default=None, max_length=254)


class BlockCustomer(Input):
    reason: Name

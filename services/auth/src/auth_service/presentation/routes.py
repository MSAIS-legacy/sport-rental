from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from rental_runtime.security import require_admin


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=80)]
    password: str = Field(min_length=12, max_length=128)


class UserView(BaseModel):
    id: str
    username: str
    role: str


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["reader", "operator", "admin"]


class TokenView(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


def create_router(service):
    router = APIRouter()

    @router.post("/register", response_model=UserView, status_code=201)
    def register(body: Credentials):
        return service.register(body.username, body.password)

    @router.post("/token", response_model=TokenView)
    def login(body: Credentials):
        return {"access_token": service.login(body.username, body.password)}

    @router.patch("/users/{identifier}/role", response_model=UserView, dependencies=[Depends(require_admin)])
    def change_role(identifier: UUID, body: RoleChange):
        return service.change_role(str(identifier), body.role)

    return router

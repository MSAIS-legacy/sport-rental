from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.entities import Customer
from .schemas import BlockCustomer, CustomerCreate


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/customers", response_model=list[Customer], tags=["customers"])
    def list_customers():
        return service.list("customers")

    @router.get("/customers/{identifier}", response_model=Customer, tags=["customers"])
    def get_customers(identifier: UUID):
        return service.get("customers", str(identifier))

    @router.post("/customers", response_model=Customer, status_code=201, tags=["customers"])
    def create_customer(body: CustomerCreate):
        return service.create_customer(**body.model_dump(mode="json"))

    @router.post(
        "/customers/{identifier}/block", response_model=Customer, status_code=200, tags=["customers"]
    )
    def block_customer(identifier: UUID, body: BlockCustomer):
        return service.block_customer(str(identifier), **body.model_dump(mode="json"))

    @router.post(
        "/customers/{identifier}/unblock", response_model=Customer, status_code=200, tags=["customers"]
    )
    def unblock_customer(identifier: UUID):
        return service.unblock_customer(str(identifier))

    return router

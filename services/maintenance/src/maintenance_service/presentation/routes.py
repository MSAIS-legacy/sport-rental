from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.entities import DamageReport, ServiceOrder
from .schemas import CompleteOrder, DamageReportCreate, OrderCreate


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/orders", response_model=list[ServiceOrder], tags=["orders"])
    def list_orders():
        return service.list("orders")

    @router.get("/orders/{identifier}", response_model=ServiceOrder, tags=["orders"])
    def get_orders(identifier: UUID):
        return service.get("orders", str(identifier))

    @router.get("/damage-reports", response_model=list[DamageReport], tags=["damage-reports"])
    def list_damage_reports():
        return service.list("damage-reports")

    @router.get("/damage-reports/{identifier}", response_model=DamageReport, tags=["damage-reports"])
    def get_damage_reports(identifier: UUID):
        return service.get("damage-reports", str(identifier))

    @router.post("/orders", response_model=ServiceOrder, status_code=201, tags=["orders"])
    def create_order(body: OrderCreate):
        return service.create_order(**body.model_dump(mode="json"))

    @router.post(
        "/orders/{identifier}/complete", response_model=ServiceOrder, status_code=200, tags=["orders"]
    )
    def complete_order(identifier: UUID, body: CompleteOrder):
        return service.complete_order(str(identifier), **body.model_dump(mode="json"))

    @router.post("/damage-reports", response_model=DamageReport, status_code=201, tags=["damage-reports"])
    def create_damage_report(body: DamageReportCreate):
        return service.create_damage_report(**body.model_dump(mode="json"))

    return router

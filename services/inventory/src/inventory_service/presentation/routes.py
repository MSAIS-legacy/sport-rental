from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.entities import InventoryItem, RentalPoint, Transfer
from .schemas import ItemCreate, ItemStatus, PointCreate, TransferCreate


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/points", response_model=list[RentalPoint], tags=["points"])
    def list_points():
        return service.list("points")

    @router.get("/points/{identifier}", response_model=RentalPoint, tags=["points"])
    def get_points(identifier: UUID):
        return service.get("points", str(identifier))

    @router.get("/items", response_model=list[InventoryItem], tags=["items"])
    def list_items():
        return service.list("items")

    @router.get("/items/{identifier}", response_model=InventoryItem, tags=["items"])
    def get_items(identifier: UUID):
        return service.get("items", str(identifier))

    @router.get("/transfers", response_model=list[Transfer], tags=["transfers"])
    def list_transfers():
        return service.list("transfers")

    @router.get("/transfers/{identifier}", response_model=Transfer, tags=["transfers"])
    def get_transfers(identifier: UUID):
        return service.get("transfers", str(identifier))

    @router.post("/points", response_model=RentalPoint, status_code=201, tags=["points"])
    def create_point(body: PointCreate):
        return service.create_point(**body.model_dump(mode="json"))

    @router.post("/items", response_model=InventoryItem, status_code=201, tags=["items"])
    def create_item(body: ItemCreate):
        return service.create_item(**body.model_dump(mode="json"))

    @router.patch("/items/{identifier}/status", response_model=InventoryItem, status_code=200, tags=["items"])
    def change_item_status(identifier: UUID, body: ItemStatus):
        return service.change_item_status(str(identifier), **body.model_dump(mode="json"))

    @router.post("/transfers", response_model=Transfer, status_code=201, tags=["transfers"])
    def create_transfer(body: TransferCreate):
        return service.create_transfer(**body.model_dump(mode="json"))

    @router.post(
        "/transfers/{identifier}/complete", response_model=Transfer, status_code=200, tags=["transfers"]
    )
    def complete_transfer(identifier: UUID):
        return service.complete_transfer(str(identifier))

    return router

from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.entities import Category, EquipmentModel
from .schemas import CategoryCreate, ModelCreate


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/categories", response_model=list[Category], tags=["categories"])
    def list_categories():
        return service.list("categories")

    @router.get("/categories/{identifier}", response_model=Category, tags=["categories"])
    def get_categories(identifier: UUID):
        return service.get("categories", str(identifier))

    @router.get("/models", response_model=list[EquipmentModel], tags=["models"])
    def list_models():
        return service.list("models")

    @router.get("/models/{identifier}", response_model=EquipmentModel, tags=["models"])
    def get_models(identifier: UUID):
        return service.get("models", str(identifier))

    @router.post("/categories", response_model=Category, status_code=201, tags=["categories"])
    def create_category(body: CategoryCreate):
        return service.create_category(**body.model_dump(mode="json"))

    @router.post("/models", response_model=EquipmentModel, status_code=201, tags=["models"])
    def create_model(body: ModelCreate):
        return service.create_model(**body.model_dump(mode="json"))

    @router.post(
        "/models/{identifier}/unpublish", response_model=EquipmentModel, status_code=200, tags=["models"]
    )
    def unpublish_model(identifier: UUID):
        return service.unpublish_model(str(identifier))

    return router

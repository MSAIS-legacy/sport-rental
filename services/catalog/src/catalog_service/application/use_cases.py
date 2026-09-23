from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import Category, EquipmentModel
from .ports import UnitOfWork

KINDS = {"categories": Category, "models": EquipmentModel}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self.uow_factory = uow_factory

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_category(self, name, parent_id=None):
        with self.uow_factory() as uow:
            if parent_id:
                uow.repository.get("categories", parent_id, Category)
            entity = Category(str(uuid4()), name, parent_id)
            uow.repository.save("categories", entity)
            return entity

    def create_model(self, name, manufacturer, category_id, specifications):
        with self.uow_factory() as uow:
            uow.repository.get("categories", category_id, Category)
            entity = EquipmentModel(str(uuid4()), name, manufacturer, category_id, specifications)
            uow.repository.save("models", entity)
            return entity

    def unpublish_model(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("models", identifier, EquipmentModel)
            entity.unpublish()
            uow.repository.save("models", entity)
            return entity

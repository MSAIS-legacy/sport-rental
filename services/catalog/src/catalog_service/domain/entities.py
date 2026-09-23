from dataclasses import dataclass, field

from .values import text


@dataclass
class Category:
    id: str
    name: str
    parent_id: str | None = None

    def __post_init__(self):
        self.name = text(self.name, "Название категории")


@dataclass
class EquipmentModel:
    id: str
    name: str
    manufacturer: str
    category_id: str
    specifications: dict[str, str] = field(default_factory=dict)
    published: bool = True

    def __post_init__(self):
        self.name = text(self.name, "Название модели")
        self.manufacturer = text(self.manufacturer, "Производитель")

    def unpublish(self):
        self.published = False

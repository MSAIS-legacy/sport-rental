"""Проверка направления зависимостей по импортам Python."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "services"


def test_clean_architecture_dependencies():
    forbidden = {
        "domain": {"application", "infrastructure", "presentation", "fastapi", "pydantic", "sqlite3"},
        "application": {"infrastructure", "presentation", "fastapi", "pydantic", "sqlite3"},
        "presentation": {"infrastructure", "sqlite3"},
    }
    for service in ROOT.iterdir():
        for layer, blocked in forbidden.items():
            for file in (service / "src" / f"{service.name}_service" / layer).glob("*.py"):
                for node in ast.walk(ast.parse(file.read_text())):
                    modules = []
                    if isinstance(node, ast.Import):
                        modules = [x.name for x in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        modules = [node.module or ""]
                    for module in modules:
                        assert not set(module.split(".")) & blocked, f"{file}: {module}"
                        assert not any(
                            part.endswith("_service") and part != f"{service.name}_service"
                            for part in module.split(".")
                        ), f"Межсервисный импорт: {file}"

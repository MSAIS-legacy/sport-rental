import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
for service in (ROOT / "services").iterdir():
    sys.path.insert(0, str(service / "src"))


@pytest.fixture
def client_factory(tmp_path):
    clients = []

    def factory(service):
        module = importlib.import_module(f"{service}_service.main")
        client = TestClient(module.create_app(str(tmp_path / f"{service}.sqlite3")))
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.close()

import os

import httpx
import pytest


@pytest.fixture(scope="session")
def api():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Full-stack integration tests require RUN_INTEGRATION=1 and Compose")
    template = os.getenv("SERVICE_URL_TEMPLATE", "http://{service}:8000")
    clients = {
        name: httpx.Client(base_url=template.format(service=name), timeout=10)
        for name in ["catalog", "inventory", "rental", "customers", "billing", "maintenance", "auth"]
    }
    response = clients["auth"].post(
        "/api/v1/auth/token",
        json={"username": os.environ["ADMIN_USERNAME"], "password": os.environ["ADMIN_PASSWORD"]},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    for client in clients.values():
        client.headers["Authorization"] = f"Bearer {token}"
    yield clients
    for client in clients.values():
        client.close()

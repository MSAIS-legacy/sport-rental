import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/runtime/src"))
for service in (ROOT / "services").iterdir():
    sys.path.insert(0, str(service / "src"))


@pytest.fixture
def jwt_keys(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    private.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        )
    )
    public.write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
    monkeypatch.setenv("JWT_PUBLIC_KEY_PATH", str(public))
    monkeypatch.setenv("JWT_PRIVATE_KEY_PATH", str(private))
    return private, public


@pytest.fixture
def client_factory(tmp_path, jwt_keys):
    clients = []

    def factory(service):
        module = importlib.import_module(f"{service}_service.main")
        client = TestClient(module.create_app(str(tmp_path / f"{service}.sqlite3")))
        from types import SimpleNamespace

        from rental_runtime.security import TokenIssuer

        token = TokenIssuer(str(jwt_keys[0])).issue(SimpleNamespace(id="test-admin", role="admin"))
        client.headers["Authorization"] = f"Bearer {token}"
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.close()

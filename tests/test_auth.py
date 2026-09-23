from types import SimpleNamespace

import jwt
from rental_runtime.security import AUDIENCE, ISSUER, TokenIssuer


def test_public_registration_login_and_roles(client_factory):
    auth = client_factory("auth")
    body = {"username": "Reader", "password": "a-long-test-password"}
    result = auth.post("/api/v1/auth/register", json=body)
    assert result.status_code == 201
    assert "password_hash" not in result.json()
    assert result.json()["role"] == "reader"
    assert auth.post("/api/v1/auth/register", json=body).status_code == 409
    assert auth.post("/api/v1/auth/register", json={**body, "role": "admin"}).status_code == 422
    assert auth.post("/api/v1/auth/token", json={**body, "password": "wrong-password"}).status_code == 401
    token = auth.post("/api/v1/auth/token", json=body).json()["access_token"]
    catalog = client_factory("catalog")
    catalog.headers["Authorization"] = f"Bearer {token}"
    assert catalog.get("/api/v1/categories").status_code == 200
    assert catalog.post("/api/v1/categories", json={"name": "Bikes"}).status_code == 403
    role = auth.patch(f"/api/v1/auth/users/{result.json()['id']}/role", json={"role": "operator"})
    assert role.status_code == 200
    token = auth.post("/api/v1/auth/token", json=body).json()["access_token"]
    catalog.headers["Authorization"] = f"Bearer {token}"
    assert catalog.post("/api/v1/categories", json={"name": "Bikes"}).status_code == 201
    auth.headers["Authorization"] = f"Bearer {token}"
    assert (
        auth.patch(f"/api/v1/auth/users/{result.json()['id']}/role", json={"role": "admin"}).status_code
        == 403
    )


def test_missing_forged_expired_and_wrong_audience_tokens(client_factory, jwt_keys):
    catalog = client_factory("catalog")
    catalog.headers.pop("Authorization")
    assert catalog.get("/api/v1/categories").status_code == 401
    catalog.headers["Authorization"] = "Bearer nonsense"
    assert catalog.get("/api/v1/categories").status_code == 401
    claims = {"sub": "123", "role": "admin", "iss": ISSUER, "aud": AUDIENCE, "iat": 1, "exp": 2, "jti": "x"}
    for body in [claims, {**claims, "exp": 4102444800, "aud": "wrong"}]:
        token = jwt.encode(body, jwt_keys[0].read_text(), algorithm="RS256")
        catalog.headers["Authorization"] = f"Bearer {token}"
        assert catalog.get("/api/v1/categories").status_code == 401
    token = TokenIssuer(str(jwt_keys[0])).issue(SimpleNamespace(id="123", role="admin"))
    header, payload, signature = token.split(".")
    catalog.headers["Authorization"] = f"Bearer {header}.{payload}.AAAA{signature[4:]}"
    assert catalog.get("/api/v1/categories").status_code == 401

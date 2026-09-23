import json
import os
import time
from uuid import uuid4

import pika
import pytest
import redis
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


def create(client, resource, body, status=201):
    result = client.post(f"/api/v1/{resource}", json=body)
    assert result.status_code == status, result.text
    return result.json()


def setup_rental(api):
    category = create(api["catalog"], "categories", {"name": "Bikes"})
    model = create(
        api["catalog"], "models", {"name": "Bike", "manufacturer": "Trek", "category_id": category["id"]}
    )
    point = create(api["inventory"], "points", {"name": "A", "address": "A street"})
    item = create(
        api["inventory"],
        "items",
        {"model_id": model["id"], "inventory_number": str(uuid4()), "point_id": point["id"]},
    )
    customer = create(api["customers"], "customers", {"full_name": "Test customer", "phone": "123"})
    tariff = create(api["rental"], "tariffs", {"name": "Daily", "daily_rate": 10000})
    body = {
        "customer_id": customer["id"],
        "item_ids": [item["id"]],
        "start": "2027-01-01T00:00:00Z",
        "end": "2027-01-02T00:00:00Z",
        "tariff_id": tariff["id"],
    }
    return item, customer, body


def wait_for(callback, predicate, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = callback()
        if predicate(result):
            return result
        time.sleep(0.2)
    pytest.fail(f"Timeout waiting for state; last result: {result}")


def engine(service):
    return create_engine(
        f"postgresql+psycopg://{service}:{os.environ['POSTGRES_PASSWORD']}@postgres:5432/{service}"
    )


def test_postgres_and_redis_cache_invalidation(api):
    category = create(api["catalog"], "categories", {"name": "Cache test"})
    model = create(
        api["catalog"],
        "models",
        {"name": "Cached model", "manufacturer": "Brand", "category_id": category["id"]},
    )
    path = f"/api/v1/models/{model['id']}"
    assert api["catalog"].get(path).json()["published"] is True
    cache = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    keys = list(cache.scan_iter(f"catalog:models:*:{model['id']}"))
    assert keys and json.loads(cache.get(keys[0]))["published"] is True
    assert api["catalog"].post(path + "/unpublish").status_code == 200
    assert api["catalog"].get(path).json()["published"] is False
    db = engine("catalog")
    with db.connect() as connection:
        row = connection.execute(
            text("SELECT payload FROM aggregates WHERE kind='models' AND id=:id"), {"id": model["id"]}
        ).scalar_one()
        assert json.loads(row)["published"] is False
    db.dispose()
    cache.close()


def test_grpc_rejects_blocked_and_unknown_customer(api):
    item, customer, body = setup_rental(api)
    result = api["customers"].post(
        f"/api/v1/customers/{customer['id']}/block", json={"reason": "Blocked in integration test"}
    )
    assert result.status_code == 200
    assert api["rental"].post("/api/v1/bookings", json=body).status_code == 409
    assert (
        api["rental"].post("/api/v1/bookings", json={**body, "customer_id": str(uuid4())}).status_code == 404
    )


@pytest.mark.parametrize(
    "payment_token, expected", [("demo-approved", "completed"), ("demo-declined", "compensated")]
)
def test_distributed_checkout_and_message_redelivery(api, payment_token, expected):
    item, _, body = setup_rental(api)
    booking = create(api["rental"], "bookings", body)
    command = {"booking_id": booking["id"], "payment_token": payment_token}
    checkout = create(api["rental"], "checkouts", command, 202)
    assert create(api["rental"], "checkouts", command, 202)["id"] == checkout["id"]
    path = f"/api/v1/checkouts/{checkout['id']}"
    result = wait_for(lambda: api["rental"].get(path).json(), lambda x: x["status"] == expected)
    stored_item = api["inventory"].get(f"/api/v1/items/{item['id']}").json()
    if expected == "completed":
        assert stored_item["status"] == "rented"
        contract = api["rental"].get(f"/api/v1/contracts/{result['contract_id']}")
        assert contract.status_code == 200
        # Повтор реального сообщения через RabbitMQ не создаёт второй платёж.
        db = engine("rental")
        with db.connect() as connection:
            envelopes = [
                json.loads(x) for x in connection.execute(text("SELECT envelope FROM outbox")).scalars()
            ]
        db.dispose()
        event = next(
            x
            for x in envelopes
            if x["type"] == "billing.charge" and x["payload"]["saga_id"] == checkout["id"]
        )
        conn = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
        channel = conn.channel()
        channel.confirm_delivery()
        channel.basic_publish(
            "rental.events",
            "billing",
            json.dumps(event).encode(),
            mandatory=True,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
        db = engine("billing")
        with db.connect() as connection:
            payments = [
                json.loads(x)
                for x in connection.execute(
                    text("SELECT payload FROM aggregates WHERE kind='payments'")
                ).scalars()
            ]
            assert len([p for p in payments if p["reference"] == f"saga:{checkout['id']}"]) == 1
            assert (
                connection.execute(
                    text("SELECT count(*) FROM inbox WHERE id=:id"), {"id": event["id"]}
                ).scalar_one()
                == 1
            )
        db.dispose()
        assert api["rental"].post(f"/api/v1/contracts/{result['contract_id']}/close").status_code == 200
        wait_for(
            lambda: api["inventory"].get(f"/api/v1/items/{item['id']}").json(),
            lambda x: x["status"] == "available",
        )
    else:
        assert stored_item["status"] == "available"
        assert stored_item["allocation_id"] is None
        assert api["rental"].get(f"/api/v1/bookings/{booking['id']}").json()["status"] == "cancelled"


def test_jwt_required_and_self_registration_cannot_write(api):
    assert (
        api["inventory"].get("/api/v1/items", headers={"Authorization": "Bearer invalid"}).status_code == 401
    )
    credentials = {"username": "reader-" + str(uuid4()), "password": "a-test-password-long-enough"}
    user = api["auth"].post("/api/v1/auth/register", json=credentials)
    assert user.status_code == 201
    token = api["auth"].post("/api/v1/auth/token", json=credentials).json()["access_token"]
    response = api["catalog"].post(
        "/api/v1/categories", headers={"Authorization": f"Bearer {token}"}, json={"name": "Forbidden"}
    )
    assert response.status_code == 403

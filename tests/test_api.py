from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

SERVICES = ["catalog", "inventory", "rental", "customers", "billing", "maintenance"]


def uid():
    return str(uuid4())


def post(client, path, data=None, expected=201):
    response = client.post(f"/api/v1/{path}", json=data)
    assert response.status_code == expected, response.text
    return response.json()


@pytest.mark.parametrize("service", SERVICES)
def test_health_and_openapi(client_factory, service):
    client = client_factory(service)
    assert client.get("/health").json() == {"status": "ok", "service": service}
    schema = client.get("/openapi.json").json()
    assert schema["paths"]
    assert client.get("/docs").status_code == 200


def test_catalog_rules_and_persistence(client_factory):
    client = client_factory("catalog")
    category = post(client, "categories", {"name": " Велосипеды "})
    assert category["name"] == "Велосипеды"
    post(client, "categories", {"name": " "}, 422)
    post(client, "categories", {"name": "Дочерняя", "parent_id": uid()}, 404)
    model = post(client, "models", {"name": "Marlin", "manufacturer": "Trek", "category_id": category["id"]})
    changed = post(client, f"models/{model['id']}/unpublish", expected=200)
    assert changed["published"] is False
    reopened = client_factory("catalog")
    assert reopened.get(f"/api/v1/models/{model['id']}").json()["published"] is False
    assert len(reopened.get("/api/v1/categories").json()) == 1
    assert client.get(f"/api/v1/models/{uid()}").status_code == 404
    assert client.get("/api/v1/models/not-a-uuid").status_code == 422


def inventory(client):
    source = post(client, "points", {"name": "Центр", "address": "Улица 1"})
    destination = post(client, "points", {"name": "Парк", "address": "Улица 2"})
    body = {"model_id": uid(), "inventory_number": uid(), "point_id": source["id"]}
    item = post(client, "items", body)
    return source, destination, body, item


def test_inventory_transfer_and_duplicates(client_factory):
    client = client_factory("inventory")
    source, destination, body, item = inventory(client)
    post(client, "items", body, 409)
    transfer = post(
        client,
        "transfers",
        {
            "source_point_id": source["id"],
            "destination_point_id": destination["id"],
            "item_ids": [item["id"]],
        },
    )
    assert client.patch(f"/api/v1/items/{item['id']}/status", json={"status": "available"}).status_code == 409
    post(client, f"transfers/{transfer['id']}/complete", expected=200)
    moved = client.get(f"/api/v1/items/{item['id']}").json()
    assert moved["point_id"] == destination["id"]
    assert moved["status"] == "available"
    post(client, f"transfers/{transfer['id']}/complete", expected=409)


def test_transfer_rolls_back_all_items_on_failure(client_factory):
    client = client_factory("inventory")
    source, destination, _, item = inventory(client)
    post(
        client,
        "transfers",
        {
            "source_point_id": source["id"],
            "destination_point_id": destination["id"],
            "item_ids": [item["id"], uid()],
        },
        404,
    )
    assert client.get(f"/api/v1/items/{item['id']}").json()["status"] == "available"
    assert client.get("/api/v1/transfers").json() == []


def test_rented_item_cannot_be_transferred(client_factory):
    client = client_factory("inventory")
    source, destination, _, item = inventory(client)
    assert client.patch(f"/api/v1/items/{item['id']}/status", json={"status": "rented"}).status_code == 200
    post(
        client,
        "transfers",
        {
            "source_point_id": source["id"],
            "destination_point_id": destination["id"],
            "item_ids": [item["id"]],
        },
        409,
    )


def booking_body(client):
    tariff = post(client, "tariffs", {"name": "Сутки", "daily_rate": 10000})
    return {
        "customer_id": uid(),
        "item_ids": [uid()],
        "tariff_id": tariff["id"],
        "start": "2027-01-01T12:00:00+00:00",
        "end": "2027-01-03T12:00:00+00:00",
    }


def test_rental_overlap_cancel_and_contract_lifecycle(client_factory):
    client = client_factory("rental")
    body = booking_body(client)
    booking = post(client, "bookings", body)
    assert booking["total"] == 20000
    post(client, "bookings", body, 409)
    post(client, f"bookings/{booking['id']}/cancel", expected=200)
    booking = post(client, "bookings", body)
    contract = post(client, "contracts", {"booking_id": booking["id"]})
    assert contract["total"] == booking["total"]
    post(client, "contracts", {"booking_id": booking["id"]}, 409)
    post(client, f"bookings/{booking['id']}/cancel", expected=409)
    post(client, "bookings", body, 409)
    post(client, f"contracts/{contract['id']}/close", expected=200)
    post(client, f"contracts/{contract['id']}/close", expected=409)
    post(client, "bookings", body)


def test_rental_boundary_and_timezone_validation(client_factory):
    client = client_factory("rental")
    body = booking_body(client)
    post(client, "bookings", body)
    post(client, "bookings", {**body, "start": body["end"], "end": "2027-01-04T12:00:00Z"})
    post(client, "bookings", {**body, "end": body["start"]}, 422)
    post(client, "bookings", {**body, "start": "2027-01-01T12:00:00"}, 422)
    post(client, "bookings", {**body, "item_ids": [body["item_ids"][0]] * 2}, 422)


def test_concurrent_booking_is_atomic(client_factory):
    client = client_factory("rental")
    body = booking_body(client)
    clients = [client_factory("rental"), client_factory("rental")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda c: c.post("/api/v1/bookings", json=body).status_code, clients))
    assert sorted(results) == [201, 409]


def test_customer_blocking(client_factory):
    client = client_factory("customers")
    customer = post(client, "customers", {"full_name": "Иван Иванов", "phone": "+70000000000"})
    post(client, f"customers/{customer['id']}/block", {"reason": " "}, 422)
    blocked = post(client, f"customers/{customer['id']}/block", {"reason": "Нарушение условий"}, 200)
    assert blocked["blocked"] is True
    unblocked = post(client, f"customers/{customer['id']}/unblock", expected=200)
    assert unblocked["blocked"] is False
    assert unblocked["block_reason"] is None


def test_payment_idempotency_and_refund_limits(client_factory):
    client = client_factory("billing")
    body = {"contract_id": uid(), "amount": 10000, "reference": "operation-1"}
    payment = post(client, "payments", body)
    assert post(client, "payments", body)["id"] == payment["id"]
    post(client, "payments", {**body, "amount": 20000}, 409)
    post(client, f"payments/{payment['id']}/refunds", {"amount": 100}, 409)
    post(client, f"payments/{payment['id']}/confirm", expected=200)
    post(client, f"payments/{payment['id']}/confirm", expected=200)
    post(client, f"payments/{payment['id']}/refunds", {"amount": 4000}, 200)
    post(client, f"payments/{payment['id']}/refunds", {"amount": 6001}, 409)
    result = post(client, f"payments/{payment['id']}/refunds", {"amount": 6000}, 200)
    assert result["refunded"] == 10000
    post(client, "payments", {**body, "amount": 1.5}, 422)
    post(client, "payments", {**body, "amount": True}, 422)


def test_deposit_settlement(client_factory):
    client = client_factory("billing")
    body = {"contract_id": uid(), "amount": 50000}
    deposit = post(client, "deposits", body)
    post(client, "deposits", body, 409)
    path = f"deposits/{deposit['id']}/settlements"
    post(client, path, {"amount": 10000, "kind": "withhold"}, 422)
    post(client, path, {"amount": 10000, "kind": "withhold", "reason": "Ущерб"}, 200)
    post(client, path, {"amount": 40001, "kind": "return"}, 409)
    settled = post(client, path, {"amount": 40000, "kind": "return"}, 200)
    assert settled["returned"] + settled["withheld"] == settled["amount"]
    assert len(settled["operations"]) == 2


def test_maintenance_lifecycle(client_factory):
    client = client_factory("maintenance")
    body = {"item_id": uid(), "description": "Замена цепи"}
    order = post(client, "orders", body)
    post(client, "orders", body, 409)
    post(client, f"orders/{order['id']}/complete", {"result": " "}, 422)
    post(client, f"orders/{order['id']}/complete", {"result": "Цепь заменена"}, 200)
    post(client, f"orders/{order['id']}/complete", {"result": "Повтор"}, 409)
    post(client, "orders", body)
    post(client, "damage-reports", {**body, "estimated_cost": -1}, 422)
    post(client, "damage-reports", {**body, "estimated_cost": 5000})

"""Демо создаёт тестовые данные во всех шести запущенных сервисах."""

import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from uuid import uuid4


def request(port, path, body=None, method="POST"):
    req = Request(
        f"http://127.0.0.1:{port}/api/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(req, timeout=10) as response:
        result = json.load(response)
    print(f"{port} {method} {path}: {result.get('id', 'ok')}")
    return result


def main():
    category = request(8001, "categories", {"name": "Велосипеды"})
    model = request(
        8001, "models", {"name": "Marlin 5", "manufacturer": "Trek", "category_id": category["id"]}
    )
    point = request(8002, "points", {"name": "Центральный", "address": "Саратов, ул. Спортивная, 1"})
    other = request(8002, "points", {"name": "Парк", "address": "Саратов, городской парк"})
    item = request(
        8002, "items", {"model_id": model["id"], "inventory_number": str(uuid4()), "point_id": point["id"]}
    )
    transfer = request(
        8002,
        "transfers",
        {"item_ids": [item["id"]], "source_point_id": point["id"], "destination_point_id": other["id"]},
    )
    request(8002, f"transfers/{transfer['id']}/complete")
    customer = request(8004, "customers", {"full_name": "Учебный клиент", "phone": "+7 000 000-00-00"})
    tariff = request(8003, "tariffs", {"name": "Посуточный", "daily_rate": 100000})
    start = datetime.now(timezone.utc) + timedelta(days=1)
    booking = request(
        8003,
        "bookings",
        {
            "customer_id": customer["id"],
            "item_ids": [item["id"]],
            "tariff_id": tariff["id"],
            "start": start.isoformat(),
            "end": (start + timedelta(days=2)).isoformat(),
        },
    )
    contract = request(8003, "contracts", {"booking_id": booking["id"]})
    payment = request(
        8005,
        "payments",
        {"contract_id": contract["id"], "amount": contract["total"], "reference": str(uuid4())},
    )
    request(8005, f"payments/{payment['id']}/confirm")
    deposit = request(8005, "deposits", {"contract_id": contract["id"], "amount": 500000})
    # Межконтекстная координация в учебном демо выполняется клиентом явно.
    request(8002, f"items/{item['id']}/status", {"status": "rented"}, "PATCH")
    request(8003, f"contracts/{contract['id']}/close")
    request(8002, f"items/{item['id']}/status", {"status": "available"}, "PATCH")
    request(
        8006,
        "damage-reports",
        {
            "item_id": item["id"],
            "contract_id": contract["id"],
            "description": "Повреждена ручка",
            "estimated_cost": 25000,
        },
    )
    request(
        8005,
        f"deposits/{deposit['id']}/settlements",
        {"kind": "withhold", "amount": 25000, "reason": "Согласованный ущерб: ручка"},
    )
    request(8005, f"deposits/{deposit['id']}/settlements", {"kind": "return", "amount": 475000})
    request(8002, f"items/{item['id']}/status", {"status": "maintenance"}, "PATCH")
    order = request(8006, "orders", {"item_id": item["id"], "description": "Замена ручки"})
    request(8006, f"orders/{order['id']}/complete", {"result": "Ручка заменена"})
    request(8002, f"items/{item['id']}/status", {"status": "available"}, "PATCH")
    print("Демо завершено: созданы все 13 видов агрегатов.")


if __name__ == "__main__":
    main()

"""Успешная saga и компенсация через реальные REST API и RabbitMQ."""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    token = None

    def request(port, path, body=None, method="POST"):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(
            f"http://127.0.0.1:{port}/api/v1/{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    token = request(
        8007, "auth/token", {"username": config["ADMIN_USERNAME"], "password": config["ADMIN_PASSWORD"]}
    )["access_token"]
    category = request(8001, "categories", {"name": "Велосипеды"})
    model = request(
        8001, "models", {"name": "Marlin 5", "manufacturer": "Trek", "category_id": category["id"]}
    )
    point = request(8002, "points", {"name": "Центральный", "address": "Саратов, Спортивная, 1"})
    item = request(
        8002, "items", {"model_id": model["id"], "inventory_number": str(uuid4()), "point_id": point["id"]}
    )
    customer = request(8004, "customers", {"full_name": "Учебный клиент", "phone": "+70000000000"})
    tariff = request(8003, "tariffs", {"name": "Посуточный", "daily_rate": 100000})
    start = datetime.now(timezone.utc) + timedelta(days=1)
    body = {
        "customer_id": customer["id"],
        "item_ids": [item["id"]],
        "tariff_id": tariff["id"],
        "start": start.isoformat(),
        "end": (start + timedelta(days=2)).isoformat(),
    }

    def wait(port, path, expected):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            value = request(port, path, method="GET")
            if value["status"] == expected:
                return value
            time.sleep(0.2)
        raise RuntimeError(f"Не дождались {expected}: {value}")

    for payment_token, expected in [("demo-approved", "completed"), ("demo-declined", "compensated")]:
        booking = request(8003, "bookings", body)
        checkout = request(8003, "checkouts", {"booking_id": booking["id"], "payment_token": payment_token})
        result = wait(8003, f"checkouts/{checkout['id']}", expected)
        print(f"Saga {result['id']}: {result['status']}")
        if expected == "completed":
            request(8003, f"contracts/{result['contract_id']}/close")
            wait(8002, f"items/{item['id']}", "available")
    print("Успешная аренда, возврат и компенсация проверены.")


if __name__ == "__main__":
    main()

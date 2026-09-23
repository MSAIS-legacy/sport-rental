from types import SimpleNamespace
from uuid import uuid4

import pytest
from billing_service.application.event_handlers import handle as billing_handler
from billing_service.infrastructure.persistence import create_uow_factory as billing_factory
from inventory_service.application.event_handlers import handle as inventory_handler
from inventory_service.application.use_cases import Service as Inventory
from inventory_service.infrastructure.persistence import create_uow_factory as inventory_factory
from rental_runtime.messaging import consume_event
from rental_service.application.event_handlers import handle as rental_handler
from rental_service.application.use_cases import Service as Rental
from rental_service.infrastructure.persistence import create_uow_factory as rental_factory


@pytest.mark.parametrize(
    "payment_token, final_status, item_status",
    [("demo-approved", "completed", "rented"), ("demo-declined", "compensated", "available")],
)
def test_saga_success_and_compensation_with_duplicate_deliveries(
    tmp_path, payment_token, final_status, item_status
):
    factories = {
        "rental": rental_factory(str(tmp_path / "rental.db")),
        "inventory": inventory_factory(str(tmp_path / "inventory.db")),
        "billing": billing_factory(str(tmp_path / "billing.db")),
    }
    handlers = {"rental": rental_handler, "inventory": inventory_handler, "billing": billing_handler}
    inventory = Inventory(factories["inventory"])
    rental = Rental(factories["rental"], SimpleNamespace(validate_customer=lambda _: None))
    point = inventory.create_point("Пункт", "Адрес")
    item = inventory.create_item(str(uuid4()), str(uuid4()), point.id)
    tariff = rental.create_tariff("Сутки", 10000)
    booking = rental.create_booking(
        str(uuid4()), [item.id], "2027-01-01T00:00:00Z", "2027-01-02T00:00:00Z", tariff.id
    )
    checkout = rental.start_checkout(booking.id, payment_token)
    assert rental.start_checkout(booking.id, payment_token).id == checkout.id

    def drain():
        for _ in range(20):
            delivered = 0
            for factory in factories.values():
                with factory() as uow:
                    events = uow.pending_events()
                    for event in events:
                        uow.mark_published(event["id"])
                for event in events:
                    target = event["target"]
                    consume_event(factories[target], handlers[target], event)
                    consume_event(factories[target], handlers[target], event)
                    delivered += 1
            if delivered == 0:
                return
        pytest.fail("Saga did not quiesce")

    drain()
    result = rental.get("checkouts", checkout.id)
    assert result.status == final_status
    assert inventory.get("items", item.id).status == item_status
    assert len(rental.list("contracts")) == (1 if final_status == "completed" else 0)
    if final_status == "completed":
        rental.close_contract(result.contract_id)
        drain()
        returned = inventory.get("items", item.id)
        assert returned.status == "available"
        assert returned.allocation_id is None
    else:
        assert rental.get("bookings", booking.id).status == "cancelled"
        assert inventory.get("items", item.id).allocation_id is None

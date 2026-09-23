from ..domain.checkout import Checkout
from ..domain.entities import Booking, RentalContract


def handle(uow, event):
    payload, kind = event["payload"], event["type"]
    checkout = uow.repository.get("checkouts", payload["saga_id"], Checkout)
    booking = uow.repository.get("bookings", checkout.booking_id, Booking)
    if kind == "inventory.reserved" and checkout.status == "reserving":
        checkout.transition("reserving", "paying")
        uow.enqueue(
            "billing",
            "billing.charge",
            {
                "saga_id": checkout.id,
                "contract_id": checkout.contract_id,
                "amount": checkout.amount,
                "payment_token": checkout.payment_token,
            },
        )
    elif kind == "inventory.rejected" and checkout.status == "reserving":
        checkout.transition("reserving", "rejected")
        checkout.error = payload["reason"]
        booking.status = "cancelled"
    elif kind == "billing.paid" and checkout.status == "paying":
        checkout.transition("paying", "issuing")
        uow.enqueue("inventory", "inventory.issue", {"saga_id": checkout.id})
    elif kind == "billing.failed" and checkout.status == "paying":
        checkout.transition("paying", "compensating")
        checkout.error = payload["reason"]
        uow.enqueue("inventory", "inventory.release", {"saga_id": checkout.id})
    elif kind == "inventory.released" and checkout.status == "compensating":
        checkout.transition("compensating", "compensated")
        booking.status = "cancelled"
    elif kind == "inventory.issued" and checkout.status == "issuing":
        checkout.transition("issuing", "completed")
        booking.status = "converted"
        contract = RentalContract(
            checkout.contract_id,
            booking.id,
            booking.customer_id,
            booking.item_ids.copy(),
            booking.start,
            booking.end,
            booking.total,
        )
        uow.repository.save("contracts", contract)
    elif kind in {
        "inventory.reserved",
        "inventory.rejected",
        "billing.paid",
        "billing.failed",
        "inventory.released",
        "inventory.issued",
    }:
        # Семантический повтор уже пройденного шага безопасен.
        return
    else:
        raise ValueError(f"Unsupported event: {kind}")
    uow.repository.save("bookings", booking)
    uow.repository.save("checkouts", checkout)

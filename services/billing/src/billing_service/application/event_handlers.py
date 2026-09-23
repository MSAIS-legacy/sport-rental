from uuid import uuid4

from ..domain.entities import Payment


def handle(uow, event):
    if event["type"] != "billing.charge":
        raise ValueError(f"Unsupported event: {event['type']}")
    payload = event["payload"]
    reply = {"saga_id": payload["saga_id"]}
    if payload["payment_token"] != "demo-approved":
        reply["reason"] = "Демонстрационный платёж отклонён"
        uow.enqueue("rental", "billing.failed", reply)
        return
    reference = f"saga:{payload['saga_id']}"
    existing = next((p for p in uow.repository.list("payments", Payment) if p.reference == reference), None)
    if existing is None:
        payment = Payment(str(uuid4()), payload["contract_id"], payload["amount"], reference)
        payment.confirm()
        uow.repository.save("payments", payment)
    elif existing.amount != payload["amount"] or existing.contract_id != payload["contract_id"]:
        raise ValueError("Idempotency reference was reused with different payment data")
    uow.enqueue("rental", "billing.paid", reply)

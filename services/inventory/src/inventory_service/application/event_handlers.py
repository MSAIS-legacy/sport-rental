from ..domain.entities import Allocation, InventoryItem
from ..domain.errors import NotFound


def handle(uow, event):
    payload, kind = event["payload"], event["type"]
    saga_id = payload["saga_id"]
    reply = {"saga_id": saga_id}
    if kind == "inventory.reserve":
        existing = next((x for x in uow.repository.list("allocations", Allocation) if x.id == saga_id), None)
        if existing:
            return
        items = []
        try:
            for identifier in payload["item_ids"]:
                item = uow.repository.get("items", identifier, InventoryItem)
                if item.status != "available" or item.allocation_id:
                    reply["reason"] = "Инвентарь недоступен для выдачи"
                    uow.enqueue("rental", "inventory.rejected", reply)
                    return
                items.append(item)
        except NotFound:
            reply["reason"] = "Инвентарь не найден"
            uow.enqueue("rental", "inventory.rejected", reply)
            return
        for item in items:
            item.status, item.allocation_id = "reserved", saga_id
            uow.repository.save("items", item)
        uow.repository.save("allocations", Allocation(saga_id, payload["item_ids"]))
        uow.enqueue("rental", "inventory.reserved", reply)
    elif kind in {"inventory.issue", "inventory.release", "inventory.return"}:
        allocation = uow.repository.get("allocations", saga_id, Allocation)
        expected = "issued" if kind == "inventory.return" else "reserved"
        target = {
            "inventory.issue": "issued",
            "inventory.release": "released",
            "inventory.return": "returned",
        }[kind]
        if allocation.status == target:
            return
        if allocation.status != expected:
            raise ValueError("Allocation is in an incompatible state")
        for identifier in allocation.item_ids:
            item = uow.repository.get("items", identifier, InventoryItem)
            if item.allocation_id != saga_id:
                raise ValueError("Allocation owner mismatch")
            item.status = "rented" if kind == "inventory.issue" else "available"
            if kind != "inventory.issue":
                item.allocation_id = None
            uow.repository.save("items", item)
        allocation.status = target
        uow.repository.save("allocations", allocation)
        if kind != "inventory.return":
            uow.enqueue(
                "rental", "inventory.issued" if kind == "inventory.issue" else "inventory.released", reply
            )
    else:
        raise ValueError(f"Unsupported event: {kind}")

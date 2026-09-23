from types import SimpleNamespace

import pytest


def test_catalog_requires_existing_category(memory_factory):
    from catalog_service.application.use_cases import Service

    service = Service(memory_factory)
    with pytest.raises(LookupError):
        service.create_model("Bike", "Trek", "missing", {})
    category = service.create_category("Bikes")
    model = service.create_model("Bike", "Trek", category.id, {})
    assert service.unpublish_model(model.id).published is False


def test_inventory_uniqueness_and_transfer(memory_factory):
    from inventory_service.application.use_cases import Service
    from inventory_service.domain.errors import Conflict

    service = Service(memory_factory)
    a, b = service.create_point("A", "Street A"), service.create_point("B", "Street B")
    item = service.create_item("model", "unique", a.id)
    with pytest.raises(Conflict):
        service.create_item("model", "unique", a.id)
    transfer = service.create_transfer([item.id], a.id, b.id)
    service.complete_transfer(transfer.id)
    assert service.get("items", item.id).point_id == b.id


def test_inventory_transfer_rollback(memory_factory):
    from inventory_service.application.use_cases import Service

    service = Service(memory_factory)
    a, b = service.create_point("A", "A"), service.create_point("B", "B")
    item = service.create_item("model", "unique", a.id)
    with pytest.raises(LookupError):
        service.create_transfer([item.id, "missing"], a.id, b.id)
    assert service.get("items", item.id).status == "available"


def test_customer_block_requires_reason(memory_factory):
    from customers_service.application.use_cases import Service
    from customers_service.domain.errors import DomainError

    service = Service(memory_factory)
    customer = service.create_customer("Иван", "123")
    with pytest.raises(DomainError):
        service.block_customer(customer.id, " ")
    assert service.block_customer(customer.id, "Причина").blocked
    assert not service.unblock_customer(customer.id).blocked


def test_rental_checks_gateway_and_conflicting_dates(memory_factory):
    from rental_service.application.use_cases import Service
    from rental_service.domain.errors import Conflict

    checked = []
    service = Service(memory_factory, SimpleNamespace(validate_customer=checked.append))
    tariff = service.create_tariff("Daily", 10000)
    args = ("customer", ["item"], "2027-01-01T00:00:00Z", "2027-01-02T01:00:00Z", tariff.id)
    booking = service.create_booking(*args)
    assert checked == ["customer"]
    assert booking.total == 20000
    with pytest.raises(Conflict):
        service.create_booking(*args)
    service.cancel_booking(booking.id)
    assert service.create_booking(*args).status == "confirmed"


def test_gateway_failure_prevents_booking(memory_factory):
    from rental_service.application.use_cases import Service

    def unavailable(identifier):
        raise ConnectionError("customers unavailable")

    service = Service(memory_factory, SimpleNamespace(validate_customer=unavailable))
    tariff = service.create_tariff("Daily", 100)
    with pytest.raises(ConnectionError):
        service.create_booking(
            "customer", ["item"], "2027-01-01T00:00:00Z", "2027-01-02T00:00:00Z", tariff.id
        )
    assert service.list("bookings") == []


def test_billing_idempotency_refunds_and_deposit(memory_factory):
    from billing_service.application.use_cases import Service
    from billing_service.domain.errors import Conflict, DomainError

    service = Service(memory_factory)
    payment = service.create_payment("contract", 100, "reference")
    assert service.create_payment("contract", 100, "reference").id == payment.id
    service.confirm_payment(payment.id)
    service.refund_payment(payment.id, 40)
    with pytest.raises(Conflict):
        service.refund_payment(payment.id, 61)
    assert service.get("payments", payment.id).refunded == 40
    deposit = service.create_deposit("contract", 100)
    with pytest.raises(DomainError):
        service.settle_deposit(deposit.id, 20, "withhold")
    assert service.settle_deposit(deposit.id, 100, "return").returned == 100


def test_maintenance_complete_and_duplicate_order(memory_factory):
    from maintenance_service.application.use_cases import Service
    from maintenance_service.domain.errors import Conflict, DomainError

    service = Service(memory_factory)
    order = service.create_order("item", "Repair")
    with pytest.raises(Conflict):
        service.create_order("item", "Another repair")
    with pytest.raises(DomainError):
        service.complete_order(order.id, " ")
    assert service.complete_order(order.id, "Done").status == "completed"
    with pytest.raises(Conflict):
        service.complete_order(order.id, "Again")


def test_auth_unique_user_password_and_role(memory_factory):
    from auth_service.application.use_cases import Service
    from auth_service.domain.entities import DuplicateUser, InvalidCredentials

    # Подменены только внешние порты; тест не требует криптографии или БД.
    hasher = SimpleNamespace(hash=lambda p: "hash:" + p, verify=lambda h, p: h == "hash:" + p)
    issuer = SimpleNamespace(issue=lambda u: "token:" + u.role)
    service = Service(memory_factory, hasher, issuer)
    user = service.register("Alice", "strong-test-password")
    assert user.role == "reader"
    assert user.password_hash != "strong-test-password"
    with pytest.raises(DuplicateUser):
        service.register("alice", "strong-test-password")
    with pytest.raises(InvalidCredentials):
        service.login("alice", "incorrect-password")
    assert service.login("alice", "strong-test-password") == "token:reader"
    service.change_role(user.id, "operator")
    assert service.login("alice", "strong-test-password") == "token:operator"

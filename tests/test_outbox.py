from dataclasses import dataclass

import pytest
from rental_runtime.database import Database, SQLUnitOfWork
from rental_runtime.messaging import consume_event, publish_pending


@dataclass
class Counter:
    id: str
    value: int


def test_aggregate_and_outbox_rollback_together(tmp_path):
    db = Database(str(tmp_path / "outbox.sqlite3"))

    def factory():
        return SQLUnitOfWork(db, LookupError)

    with pytest.raises(RuntimeError):
        with factory() as uow:
            uow.repository.save("counter", Counter("one", 1))
            uow.enqueue("billing", "charge", {"amount": 1})
            raise RuntimeError("simulated crash")
    with factory() as uow:
        assert uow.pending_events() == []
        assert uow.repository.list("counter", Counter) == []


def test_inbox_deduplicates_and_rolls_back_on_failure(tmp_path):
    db = Database(str(tmp_path / "inbox.sqlite3"))

    def factory():
        return SQLUnitOfWork(db, LookupError)

    event = {"id": "event1", "type": "increment", "target": "billing", "payload": {}}

    def handler(uow, event):
        values = uow.repository.list("counter", Counter)
        uow.repository.save("counter", Counter("one", values[0].value + 1 if values else 1))

    def failed(uow, event):
        handler(uow, event)
        raise RuntimeError("retry")

    with pytest.raises(RuntimeError):
        consume_event(factory, failed, event)
    consume_event(factory, handler, event)
    consume_event(factory, handler, event)
    with factory() as uow:
        assert uow.repository.get("counter", "one", Counter).value == 1
        assert uow.seen("event1")


def test_broker_failure_leaves_outbox_pending(tmp_path):
    db = Database(str(tmp_path / "publisher.sqlite3"))

    def factory():
        return SQLUnitOfWork(db, LookupError)

    with factory() as uow:
        uow.enqueue("billing", "charge", {})

    class UnavailableBroker:
        def basic_publish(self, **kwargs):
            raise ConnectionError("broker down")

    with pytest.raises(ConnectionError):
        publish_pending(factory, UnavailableBroker())
    with factory() as uow:
        assert len(uow.pending_events()) == 1

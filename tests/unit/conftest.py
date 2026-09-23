from copy import deepcopy
from types import SimpleNamespace

import pytest


@pytest.fixture
def memory_factory():
    state = {}

    class Repository:
        def __init__(self, data):
            self.data = data

        def get(self, kind, identifier, entity_type):
            if (kind, identifier) not in self.data:
                raise LookupError(identifier)
            return deepcopy(self.data[kind, identifier])

        def list(self, kind, entity_type):
            return [deepcopy(v) for (k, _), v in self.data.items() if k == kind]

        def save(self, kind, entity):
            self.data[kind, entity.id] = deepcopy(entity)

    class Uow:
        def __enter__(self):
            self.data = deepcopy(state)
            self.repository = Repository(self.data)
            self.events = []
            return self

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                state.clear()
                state.update(self.data)

        def enqueue(self, target, kind, payload):
            self.events.append(SimpleNamespace(target=target, type=kind, payload=payload))

    return Uow

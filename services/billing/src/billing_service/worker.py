import os

from rental_runtime.messaging import run_worker

from .application.event_handlers import handle
from .infrastructure.persistence import create_uow_factory

if __name__ == "__main__":
    run_worker("billing", create_uow_factory(os.getenv("DATABASE_URL", "data/billing.sqlite3")), handle)

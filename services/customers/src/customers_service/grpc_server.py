import os

from .application.use_cases import Service
from .infrastructure.grpc_api import start_server
from .infrastructure.persistence import create_uow_factory


def main():
    service = Service(create_uow_factory(os.getenv("DATABASE_URL", "data/customers.sqlite3")))
    server, _ = start_server(
        service, os.environ["INTERNAL_RPC_TOKEN"], os.getenv("GRPC_BIND_ADDRESS", "[::]:50051")
    )
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(3).wait()


if __name__ == "__main__":
    main()

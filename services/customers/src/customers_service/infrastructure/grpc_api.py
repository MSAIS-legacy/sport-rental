import hmac
from concurrent.futures import ThreadPoolExecutor

import grpc
from rental_runtime.proto import customers_pb2, customers_pb2_grpc

from ..domain.errors import NotFound


class CustomersRPC(customers_pb2_grpc.CustomersServicer):
    def __init__(self, service, service_token):
        if not service_token:
            raise ValueError("INTERNAL_RPC_TOKEN is required")
        self.service, self.service_token = service, service_token

    def CheckEligibility(self, request, context):
        token = dict(context.invocation_metadata()).get("x-service-token", "")
        if not hmac.compare_digest(token, self.service_token):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid service token")
        try:
            customer = self.service.get("customers", request.customer_id)
        except NotFound:
            return customers_pb2.EligibilityReply(exists=False, allowed=False, reason="Клиент не найден")
        return customers_pb2.EligibilityReply(
            exists=True, allowed=not customer.blocked, reason=customer.block_reason or ""
        )


def start_server(service, service_token, address):
    server = grpc.server(ThreadPoolExecutor(max_workers=4))
    customers_pb2_grpc.add_CustomersServicer_to_server(CustomersRPC(service, service_token), server)
    port = server.add_insecure_port(address)
    if not port:
        raise RuntimeError(f"Cannot bind gRPC: {address}")
    server.start()
    return server, port

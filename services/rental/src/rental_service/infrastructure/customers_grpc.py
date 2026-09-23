import grpc
from rental_runtime.proto import customers_pb2, customers_pb2_grpc

from ..application.ports import DependencyUnavailable
from ..domain.errors import Conflict, NotFound


class GrpcCustomerGateway:
    def __init__(self, address, service_token):
        self.address, self.service_token = address, service_token

    def validate_customer(self, customer_id):
        if not self.service_token:
            raise DependencyUnavailable("INTERNAL_RPC_TOKEN не настроен")
        try:
            with grpc.insecure_channel(self.address) as channel:
                reply = customers_pb2_grpc.CustomersStub(channel).CheckEligibility(
                    customers_pb2.EligibilityRequest(customer_id=customer_id),
                    timeout=2,
                    metadata=(("x-service-token", self.service_token),),
                )
        except grpc.RpcError as exc:
            raise DependencyUnavailable("Сервис клиентов недоступен") from exc
        if not reply.exists:
            raise NotFound("Клиент не найден")
        if not reply.allowed:
            raise Conflict(f"Клиенту запрещена аренда: {reply.reason}")

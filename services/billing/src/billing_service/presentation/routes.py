from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.entities import Deposit, Payment
from .schemas import DepositCreate, DepositSettlement, PaymentCreate, RefundPayment


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/payments", response_model=list[Payment], tags=["payments"])
    def list_payments():
        return service.list("payments")

    @router.get("/payments/{identifier}", response_model=Payment, tags=["payments"])
    def get_payments(identifier: UUID):
        return service.get("payments", str(identifier))

    @router.get("/deposits", response_model=list[Deposit], tags=["deposits"])
    def list_deposits():
        return service.list("deposits")

    @router.get("/deposits/{identifier}", response_model=Deposit, tags=["deposits"])
    def get_deposits(identifier: UUID):
        return service.get("deposits", str(identifier))

    @router.post("/payments", response_model=Payment, status_code=201, tags=["payments"])
    def create_payment(body: PaymentCreate):
        return service.create_payment(**body.model_dump(mode="json"))

    @router.post("/payments/{identifier}/confirm", response_model=Payment, status_code=200, tags=["payments"])
    def confirm_payment(identifier: UUID):
        return service.confirm_payment(str(identifier))

    @router.post("/payments/{identifier}/refunds", response_model=Payment, status_code=200, tags=["payments"])
    def refund_payment(identifier: UUID, body: RefundPayment):
        return service.refund_payment(str(identifier), **body.model_dump(mode="json"))

    @router.post("/deposits", response_model=Deposit, status_code=201, tags=["deposits"])
    def create_deposit(body: DepositCreate):
        return service.create_deposit(**body.model_dump(mode="json"))

    @router.post(
        "/deposits/{identifier}/settlements", response_model=Deposit, status_code=200, tags=["deposits"]
    )
    def settle_deposit(identifier: UUID, body: DepositSettlement):
        return service.settle_deposit(str(identifier), **body.model_dump(mode="json"))

    return router

from uuid import UUID

from fastapi import APIRouter

from ..application.use_cases import Service
from ..domain.checkout import Checkout
from ..domain.entities import Booking, RentalContract, Tariff
from .schemas import BookingCreate, CheckoutCreate, ContractCreate, TariffCreate


def create_router(service: Service) -> APIRouter:
    router = APIRouter()

    @router.get("/tariffs", response_model=list[Tariff], tags=["tariffs"])
    def list_tariffs():
        return service.list("tariffs")

    @router.get("/tariffs/{identifier}", response_model=Tariff, tags=["tariffs"])
    def get_tariffs(identifier: UUID):
        return service.get("tariffs", str(identifier))

    @router.get("/bookings", response_model=list[Booking], tags=["bookings"])
    def list_bookings():
        return service.list("bookings")

    @router.get("/bookings/{identifier}", response_model=Booking, tags=["bookings"])
    def get_bookings(identifier: UUID):
        return service.get("bookings", str(identifier))

    @router.get("/contracts", response_model=list[RentalContract], tags=["contracts"])
    def list_contracts():
        return service.list("contracts")

    @router.get("/contracts/{identifier}", response_model=RentalContract, tags=["contracts"])
    def get_contracts(identifier: UUID):
        return service.get("contracts", str(identifier))

    @router.post("/tariffs", response_model=Tariff, status_code=201, tags=["tariffs"])
    def create_tariff(body: TariffCreate):
        return service.create_tariff(**body.model_dump(mode="json"))

    @router.post("/bookings", response_model=Booking, status_code=201, tags=["bookings"])
    def create_booking(body: BookingCreate):
        return service.create_booking(**body.model_dump(mode="json"))

    @router.post("/bookings/{identifier}/cancel", response_model=Booking, status_code=200, tags=["bookings"])
    def cancel_booking(identifier: UUID):
        return service.cancel_booking(str(identifier))

    @router.post("/contracts", response_model=RentalContract, status_code=201, tags=["contracts"])
    def create_contract(body: ContractCreate):
        return service.create_contract(**body.model_dump(mode="json"))

    @router.post(
        "/contracts/{identifier}/close", response_model=RentalContract, status_code=200, tags=["contracts"]
    )
    def close_contract(identifier: UUID):
        return service.close_contract(str(identifier))

    @router.post("/checkouts", response_model=Checkout, status_code=202, tags=["saga"])
    def start_checkout(body: CheckoutCreate):
        return service.start_checkout(**body.model_dump(mode="json"))

    @router.get("/checkouts/{identifier}", response_model=Checkout, tags=["saga"])
    def get_checkout(identifier: UUID):
        return service.get("checkouts", str(identifier))

    return router

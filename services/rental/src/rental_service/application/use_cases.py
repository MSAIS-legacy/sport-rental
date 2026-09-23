from collections.abc import Callable
from uuid import uuid4

from ..domain.entities import Booking, RentalContract, Tariff
from ..domain.errors import Conflict
from ..domain.values import Period
from .ports import UnitOfWork

KINDS = {"tariffs": Tariff, "bookings": Booking, "contracts": RentalContract}


class Service:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], customer_gateway=None):
        self.uow_factory = uow_factory
        self.customer_gateway = customer_gateway

    def get(self, kind: str, identifier: str):
        with self.uow_factory() as uow:
            return uow.repository.get(kind, identifier, KINDS[kind])

    def list(self, kind: str):
        with self.uow_factory() as uow:
            return uow.repository.list(kind, KINDS[kind])

    def create_tariff(self, name, daily_rate):
        with self.uow_factory() as uow:
            entity = Tariff(str(uuid4()), name, daily_rate)
            uow.repository.save("tariffs", entity)
            return entity

    def create_booking(self, customer_id, item_ids, start, end, tariff_id):
        if self.customer_gateway:
            self.customer_gateway.validate_customer(customer_id)
        period = Period(start, end)
        with self.uow_factory() as uow:
            tariff = uow.repository.get("tariffs", tariff_id, Tariff)
            entity = Booking(
                str(uuid4()),
                customer_id,
                item_ids,
                start,
                end,
                tariff_id,
                tariff.calculate(period, len(item_ids)),
            )
            # Бронирования converted сохраняют резерв до закрытия договора.
            for existing in uow.repository.list("bookings", Booking):
                if (
                    existing.status in {"confirmed", "converted"}
                    and set(existing.item_ids).intersection(item_ids)
                    and period.overlaps(Period(existing.start, existing.end))
                ):
                    raise Conflict("Инвентарь уже забронирован на этот период")
            uow.repository.save("bookings", entity)
            return entity

    def cancel_booking(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("bookings", identifier, Booking)
            entity.cancel()
            uow.repository.save("bookings", entity)
            return entity

    def create_contract(self, booking_id):
        with self.uow_factory() as uow:
            booking = uow.repository.get("bookings", booking_id, Booking)
            booking.convert()
            entity = RentalContract(
                str(uuid4()),
                booking.id,
                booking.customer_id,
                booking.item_ids.copy(),
                booking.start,
                booking.end,
                booking.total,
            )
            uow.repository.save("bookings", booking)
            uow.repository.save("contracts", entity)
            return entity

    def close_contract(self, identifier):
        with self.uow_factory() as uow:
            entity = uow.repository.get("contracts", identifier, RentalContract)
            entity.close()
            booking = uow.repository.get("bookings", entity.booking_id, Booking)
            booking.status = "completed"
            uow.repository.save("bookings", booking)
            uow.repository.save("contracts", entity)
            return entity

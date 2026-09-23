"""Composition root: связывает порты приложения с адаптерами."""

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .application.use_cases import Service
from .domain.errors import Conflict, DomainError, NotFound
from .infrastructure.persistence import create_uow_factory
from .presentation.routes import create_router


def create_app(database_path: str | None = None) -> FastAPI:
    path = database_path or os.getenv("DATABASE_URL") or os.getenv("DATABASE_PATH", "data/rental.sqlite3")
    service = Service(create_uow_factory(path, None if database_path else os.getenv("REDIS_URL")))
    app = FastAPI(title="Аренда — Sport Rental", version="0.1.0")

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=409 if isinstance(exc, Conflict) else 422, content={"detail": str(exc)}
        )

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "service": "rental"}

    app.include_router(create_router(service), prefix="/api/v1")
    return app


app = create_app()

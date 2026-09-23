import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from rental_runtime.database import Database, SQLUnitOfWork
from rental_runtime.security import TokenIssuer, TokenVerifier

from .application.use_cases import Service
from .domain.entities import AuthError, DuplicateUser, InvalidCredentials
from .infrastructure.passwords import ArgonHasher
from .presentation.routes import create_router


class NotFound(Exception):
    pass


def create_app(database_path=None):
    database = Database(database_path or os.getenv("DATABASE_URL", "data/auth.sqlite3"))
    service = Service(
        lambda: SQLUnitOfWork(database, NotFound),
        ArgonHasher(),
        TokenIssuer(os.getenv("JWT_PRIVATE_KEY_PATH", ".secrets/private.pem")),
    )

    @asynccontextmanager
    async def lifespan(app):
        if os.getenv("ADMIN_USERNAME") and os.getenv("ADMIN_PASSWORD"):
            try:
                service.register(os.environ["ADMIN_USERNAME"], os.environ["ADMIN_PASSWORD"], "admin")
            except DuplicateUser:
                pass
        yield
        database.close()

    app = FastAPI(title="Авторизация — Sport Rental", version="0.2.0", lifespan=lifespan)
    app.state.token_verifier = TokenVerifier()

    @app.exception_handler(AuthError)
    async def auth_error(request: Request, exc: AuthError):
        status = (
            401 if isinstance(exc, InvalidCredentials) else 409 if isinstance(exc, DuplicateUser) else 422
        )
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "auth"}

    app.include_router(create_router(service), prefix="/api/v1/auth", tags=["auth"])
    return app


app = create_app()

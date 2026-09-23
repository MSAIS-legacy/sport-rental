import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)
ISSUER = "sport-rental-auth"
AUDIENCE = "sport-rental"


class TokenIssuer:
    def __init__(self, private_key_path):
        self.private_key_path = private_key_path

    def issue(self, user):
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": user.id,
                "role": user.role,
                "iss": ISSUER,
                "aud": AUDIENCE,
                "iat": now,
                "exp": now + timedelta(minutes=15),
                "jti": str(uuid4()),
            },
            Path(self.private_key_path).read_text(),
            algorithm="RS256",
        )


class TokenVerifier:
    def __init__(self, public_key_path=None):
        self.public_key_path = public_key_path or os.getenv("JWT_PUBLIC_KEY_PATH", ".secrets/public.pem")

    def verify(self, token):
        claims = jwt.decode(
            token,
            Path(self.public_key_path).read_text(),
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"require": ["sub", "exp", "iat", "iss", "aud", "role", "jti"]},
        )
        if claims["role"] not in {"reader", "operator", "admin"}:
            raise jwt.InvalidTokenError("Unknown role")
        return claims


def require_access(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None:
        raise HTTPException(401, "Требуется Bearer JWT", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = request.app.state.token_verifier.verify(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(
            401, "Недействительный или истёкший токен", headers={"WWW-Authenticate": "Bearer"}
        ) from None
    except OSError:
        raise HTTPException(503, "Публичный ключ авторизации не настроен") from None
    if request.method not in {"GET", "HEAD", "OPTIONS"} and claims["role"] not in {"operator", "admin"}:
        raise HTTPException(403, "Для изменения данных нужна роль operator или admin")
    return claims


def require_admin(claims=Depends(require_access)):
    if claims["role"] != "admin":
        raise HTTPException(403, "Требуется роль admin")
    return claims

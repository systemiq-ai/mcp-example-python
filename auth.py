import contextvars
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt
from starlette.config import Config
from starlette.responses import JSONResponse


auth_token = contextvars.ContextVar[str | None]("auth_token", default=None)
auth_payload = contextvars.ContextVar[dict]("auth_payload", default={})

config = Config(env_file=None)
PUBLIC_KEY = config("PUBLIC_KEY")
CLIENT_IDS = config(
    "CLIENT_IDS",
    cast=lambda v: [int(x) for x in v.split(",")] if v else [],
    default="",
)
ALGORITHM = "RS256"


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        client_id = payload.get("client_id")
        token_type = payload.get("type")
        scopes = payload.get("scopes", [])

        if CLIENT_IDS and client_id not in CLIENT_IDS:
            raise ValueError("Unauthorized client ID")
        if "client_super" not in scopes:
            raise ValueError("Insufficient token scopes")
        if token_type != "access":
            raise ValueError("Invalid token type")
        return payload

    except ExpiredSignatureError:
        raise ValueError("Access token has expired")
    except JWTError:
        raise ValueError("Invalid token")


class AuthMiddleware:
    """ASGI middleware that validates JWT on plain HTTP requests.
       Uses ContextVars so each concurrent request gets its own values."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization")
        if not auth_header or not auth_header.startswith(b"Bearer "):
            return await JSONResponse({"detail": "Unauthorized"}, status_code=401)(scope, receive, send)

        try:
            token = auth_header.split()[1].decode()
            payload = verify_token(token)
            auth_token.set(token)
            auth_payload.set(payload)
        except ValueError as exc:
            return await JSONResponse({"detail": str(exc)}, status_code=401)(scope, receive, send)

        await self.app(scope, receive, send)

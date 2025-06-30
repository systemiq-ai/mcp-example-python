import logging
import contextvars
from typing import Any
from starlette.responses import JSONResponse
from jose import jwt, ExpiredSignatureError, JWTError
from starlette.config import Config

auth_token: contextvars.ContextVar[str | None] = contextvars.ContextVar("auth_token", default=None)
auth_payload: contextvars.ContextVar[dict]     = contextvars.ContextVar("auth_payload", default={})

# Load environment variables
config = Config(env_file=None)
PUBLIC_KEY = config("PUBLIC_KEY")
CLIENT_IDS = config("CLIENT_IDS", cast=lambda v: [int(x) for x in v.split(",")] if v else [], default="")
ALGORITHM = "RS256"

# Function to verify the token and extract payload
def verify_token(token: str):
    try:
        # Decode the JWT using the public key
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])

        client_id = payload.get("client_id")
        token_type = payload.get("type")
        token_scopes = payload.get("scopes", [])

        if CLIENT_IDS and client_id not in CLIENT_IDS:
            logging.warning(f"Client ID {client_id} not allowed.")
            raise ValueError("Unauthorized client ID")

        if "client_super" not in token_scopes:
            logging.warning("Token scopes do not include 'client_super'.")
            raise ValueError("Insufficient token scopes")

        if token_type != "access":
            logging.warning("Invalid type for access.")
            raise ValueError("Invalid token type")

        return payload

    except ExpiredSignatureError:
        logging.warning("Expired token provided.")
        raise ValueError("Access token has expired")
    except JWTError:
        logging.warning("Invalid token provided.")
        raise ValueError("Invalid token")
    except Exception as e:
        logging.error(f"Unexpected error during token verification: {e}")
        raise ValueError(f"Unexpected error: {str(e)}")


class AuthMiddleware:
    """
    Lightweight ASGI middleware that performs JWT validation on pure HTTP requests.
    It bypasses non‑HTTP scopes (e.g. websocket, lifespan, sse streaming handled
    by StreamingResponse) and therefore avoids the assertion failure that occurs
    in Starlette's BaseHTTPMiddleware when used with streaming responses.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any):
        # Only act on regular HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract the 'Authorization' header (bytes -> str)
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization")

        if not auth_header or not auth_header.startswith(b"Bearer "):
            response = JSONResponse({"detail": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

        try:
            token = auth_header.split()[1].decode()
            payload = verify_token(token)

            # Make token & payload available via ContextVars
            auth_token.set(token)
            auth_payload.set(payload)

        except ValueError as exc:
            response = JSONResponse({"detail": str(exc)}, status_code=401)
            await response(scope, receive, send)
            return

        # All good, continue down the stack
        await self.app(scope, receive, send)
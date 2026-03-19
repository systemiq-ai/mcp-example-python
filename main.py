import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from auth import AuthMiddleware, auth_token, auth_payload

mcp = FastMCP(
    "My Tool Server",
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_origins=[],
    ),
)
mcp.settings.streamable_http_path = "/mcp"

@mcp.tool()
def greet(name: str) -> str:
    token = auth_token.get()
    payload = auth_payload.get()
    logging.info(f"Hello, {name}! Token: {token!r}, Payload: {payload}")
    return f"Hello, {name}!"

@mcp.tool()
def extension(config: object, data: list, action: str) -> bool:
    token = auth_token.get()
    payload = auth_payload.get()

    logging.info(f"Hello extension! Token: {token!r}, Payload: {payload}")
    logging.info(f"config: {config} data: {data} action: {action}")

    return

# Wrap the Starlette app
app = AuthMiddleware(mcp.streamable_http_app())

if __name__ == "__main__":
    # expose over HTTP. Map ports as you like (e.g., 8001:8000 in Docker)
    uvicorn.run(app, host="0.0.0.0", port=8000)

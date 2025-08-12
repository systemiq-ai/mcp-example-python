import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from auth import AuthMiddleware, auth_token, auth_payload

mcp = FastMCP("My Tool Server")

@mcp.tool()
def greet(name: str) -> str:
    token = auth_token.get()
    payload = auth_payload.get()
    logging.info(f"Hello, {name}! Token: {token!r}, Payload: {payload}")
    return f"Hello, {name}!"

# Wrap the Starlette app that serves SSE + POST /messages
app = AuthMiddleware(mcp.sse_app())

if __name__ == "__main__":
    # expose over HTTP(SSE). Map ports as you like (e.g., 8001:8000 in Docker)
    uvicorn.run(app, host="0.0.0.0", port=8000)
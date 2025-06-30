import logging
from fastapi import FastAPI
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

#from auth import AuthMiddleware
from auth import AuthMiddleware, auth_token, auth_payload

app = FastAPI()

# Initialize MCP server
mcp = FastMCP("My Tool Server")

@mcp.tool()
def greet(name: str) -> str:
    # If needed, grab the values from the ContextVars
    #token   = auth_token.get()
    payload = auth_payload.get()

    logging.info(f"Hello, {name}! Payload: {payload}")
    return f"Hello, {name}!"

protected_mcp_app = AuthMiddleware(mcp.sse_app())

# Register protected app
app.router.routes.append(
    Mount("/", app=protected_mcp_app)
)
# About MCP

MCP is an open protocol that standardizes how applications provide context to LLMs. Systemiq integrates MCP (Model Context Protocol) to enable secure, real-time interaction between agents and server-side resources. With MCP, models can dynamically fetch context-specific information or send data back to your backend for advanced processing and analysis. This interaction is governed by Systemiq’s robust authentication mechanism to ensure safe and reliable operations.

# MCP Example with Auth Integration

This repo shows how to run a **Model Context Protocol (MCP)** server over **SSE** and protect it with **JWT-based authentication**.
Authentication happens in a lightweight **ASGI middleware** that validates the incoming `Authorization: Bearer <token>` header and exposes the decoded payload to MCP tools safely via **ContextVars** (isolated per request).

* **Secure SSE**: Every MCP request must provide a valid bearer token
* **Tools**: Example `greet` tool that can read the token payload
* **Concurrency-safe auth**: Token & payload are stored in ContextVars (no cross-request leakage)

## Requirements

* Python 3.13+
* A valid RS256 JWT (must include:

  * `client_id` in `CLIENT_IDS`
  * `scopes` including `"client_super"`)
* Env vars:

  * `PUBLIC_KEY` (PEM string for RS256)
  * `CLIENT_IDS` (comma-separated IDs, e.g. `1,2,3`)

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Export environment variables:

```bash
export PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
...your RS256 public key...
-----END PUBLIC KEY-----"
export CLIENT_IDS="1,2,3"
```

## Run

You can run either way:

```bash
# direct
python main.py

# or with uvicorn (dev hot-reload)
ENVIRONMENT=development uvicorn main:app --reload
```

The app serves an **SSE endpoint** and a **messages endpoint** used by MCP clients:

* `GET /sse` – opens the SSE stream (must include `Authorization` header)
* `POST /messages/?session_id=...` – JSON-RPC messages for MCP (same auth header)

Both endpoints are protected by the JWT middleware.

## How Authentication Works

* A custom ASGI middleware validates the `Authorization: Bearer <token>` header:

  * Verifies RS256 signature using `PUBLIC_KEY`
  * Checks `client_id` ∈ `CLIENT_IDS`
  * Requires `"client_super"` in `scopes`
* On success, it stores the **raw token** and **decoded payload** in **ContextVars**:

  * `auth_token: ContextVar[str | None]`
  * `auth_payload: ContextVar[dict]`
* In your MCP tools, you read these without touching HTTP/Starlette objects:

  * This is **safe under concurrency**: ContextVars are isolated per request.

### Example Tool

```python
from mcp.server.fastmcp import FastMCP, Context
from auth import auth_token, auth_payload  # ContextVars set by middleware

mcp = FastMCP("My Tool Server")

@mcp.tool()
def greet(name: str, ctx: Context) -> str:
    token   = auth_token.get()
    payload = auth_payload.get()
    # Use payload as needed (e.g., enforce scopes, log client_id, etc.)
    # logging.info(f"greet -> token: {bool(token)}, payload: {payload}")
    return f"Hello, {name}!"
```

> Note: We do **not** rely on `ctx.session` or HTTP state; tools remain transport-agnostic.

## Connecting a Client

Any MCP client that supports SSE + JSON-RPC can connect. Be sure to pass the `Authorization` header. For example, using a custom client:

* Open SSE at `GET /sse` with `Authorization: Bearer <token>`
* Send MCP requests to `POST /messages/?session_id=<id>` with the same header

(If you’re using a higher-level MCP client library, set its **SSE headers** to include your bearer token.)

## Docker

A `Dockerfile` is included.

### Build

```bash
docker build -t mcp-example .
```

### Run

```bash
docker run --rm \
  -e PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----" \
  -e CLIENT_IDS="1" \
  -p 8000:8000 \
  mcp-example
```

## Notes & Guarantees

* **Isolation**: ContextVars ensure each request sees only its own `token`/`payload`.
* **No framework coupling**: Tools don’t need direct access to HTTP request objects.
* **Scopes**: By default, the middleware requires `"client_super"`; adapt as needed.

## Further Information

You can also find extended documentation at [Model Context Protocol](https://modelcontextprotocol.io).


## License

MIT © [systemiq.ai](https://systemiq.ai)

# MCP Example with Auth Integration

This repo shows how to run a **Model Context Protocol (MCP)** server over **streamable HTTP** and protect it with **JWT-based authentication**.
Authentication happens in a lightweight **ASGI middleware** that validates the incoming `Authorization: Bearer <token>` header and exposes the decoded payload to MCP tools safely via **ContextVars** (isolated per request).

* **Secure MCP over HTTP**: Every MCP request must provide a valid bearer token
* **Tools**: Example `greet` and `extension` tools that can read the token payload
* **Concurrency-safe auth**: Token & payload are stored in ContextVars (no cross-request leakage)
* **Host protection**: FastMCP transport security only allows local hosts such as `host.docker.internal`, `localhost`, and `127.0.0.1`

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

The app serves a **streamable HTTP MCP endpoint**:

* `POST /mcp` – JSON-RPC requests for MCP
* `GET /mcp` – optional long-lived stream / notifications when supported by the client library

All MCP HTTP requests are protected by the JWT middleware.

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

### Example Tools

```python
from mcp.server.fastmcp import FastMCP
from auth import auth_token, auth_payload  # ContextVars set by middleware

mcp = FastMCP("My Tool Server")

@mcp.tool()
def greet(name: str) -> str:
    token   = auth_token.get()
    payload = auth_payload.get()
    # Use payload as needed (e.g., enforce scopes, log client_id, etc.)
    return f"Hello, {name}!"
```

```python
@mcp.tool()
def extension(config: object, data: list, action: str) -> bool:
    token = auth_token.get()
    payload = auth_payload.get()
    return True
```

> Note: We do **not** rely on HTTP request objects in the tools; they remain transport-agnostic.


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
* **Host validation**: FastMCP rejects unexpected `Host` headers unless they are listed in `allowed_hosts`.

## Further Information

You can also find extended documentation at [Model Context Protocol](https://modelcontextprotocol.io).


## License

MIT © [systemiq.ai](https://systemiq.ai)

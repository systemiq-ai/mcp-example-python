# MCP Example with Auth Integration

MCP is an open protocol that standardizes how applications provide context to LLMs. Systemiq integrates MCP (Model Context Protocol) to enable secure, real-time interaction between agents and server-side resources. With MCP, models can dynamically fetch context-specific information or send data back to your backend for advanced processing and analysis. This interaction is governed by Systemiq’s robust authentication mechanism to ensure safe and reliable operations.

- **Fetch Data**: Expose server-side data sources that the model can query in real time, enabling dynamic context injection during reasoning or task execution.
- **Process Data**: Handle data transformations or trigger business logic, allowing the model to initiate actions or workflows on the backend.
- **Authentication**: Secure endpoints with Systemiq‘s robust authentication layer.

This project includes a Python example: the MCP Greeting Tool.

This example demonstrates a minimal FastAPI application using `FastMCP` with integrated JWT-based authentication middleware.

## Features

- Runs a FastAPI server with `FastMCP` integration
- Provides a simple tool endpoint (`/greet`) with token-protected SSE access
- Uses JWT validation middleware that checks client ID and scope

## Requirements

- Python 3.13+
- Valid JWT tokens with `client_super` scope
- Environment variables for `PUBLIC_KEY` and `CLIENT_IDS`

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set required environment variables:

```bash
export PUBLIC_KEY="your-RS256-public-key"
export CLIENT_IDS="1,2,3"
```

## Usage

Run the app:

```bash
python main.py
```

To start in development mode with hot-reload:

```bash
ENVIRONMENT=development uvicorn main:app --reload
```

## Docker

A `Dockerfile` is included for containerized execution.

### Build the image

```bash
docker build -t mcp-example .
```

### Run the container

```bash
docker run --rm \
  -e PUBLIC_KEY="your-RS256-public-key" \
  -e CLIENT_IDS="1" \
  -p 8000:8000 \
  mcp-example
```

## Endpoint

Once running, the following endpoint is available:

- `GET /` – Connects to the SSE interface, requires `Authorization: Bearer <token>` header

Example tool:

- `greet(name: str) -> str`: Returns a greeting using the authenticated token payload

## Token Authentication

The app uses a custom ASGI middleware that verifies JWTs passed in the `Authorization` header. Tokens must be signed with RS256 and include:

- `client_id` matching one of the `CLIENT_IDS`
- `scopes` including `"client_super"`

## Further Information

You can also find extended documentation at [Model Context Protocol](https://modelcontextprotocol.io).


## License

MIT © [systemiq.ai](https://systemiq.ai)

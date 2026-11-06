# Beszel MCP Server

A Model Context Protocol (MCP) server for the [Beszel](https://github.com/henrygd/beszel) system monitoring tool.

## Overview

This MCP server provides tools to interact with Beszel's PocketBase backend, allowing you to:

- List systems, containers, alerts, and alert history
- Query system statistics
- Query container statistics

**Built with [FastMCP](https://github.com/jlowin/fastmcp)** - A high-level Python framework for building MCP servers with minimal boilerplate. See [Why FastMCP?](docs/WHY_FASTMCP.md) for details.

**Works great with [uv](https://github.com/astral-sh/uv)** - The blazing-fast Python package manager. See [uv Quick Start](docs/UV_QUICKSTART.md) for a 2-minute setup!

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager that handles virtual environments automatically:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the project
uv pip install -e .

# Or run directly without installing
uv run python -m beszel_mcp
```

### Using pip

```bash
pip install -e .
```

Or install directly from the dependencies:

```bash
pip install fastmcp httpx
```

## Configuration

The server requires the following environment variables:

- `BESZEL_URL`: The URL of your Beszel/PocketBase instance (e.g., `http://localhost:8090`)
- `BESZEL_EMAIL` (optional): Admin email for authentication
- `BESZEL_PASSWORD` (optional): Admin password for authentication
- `BESZEL_SUPERUSER` (optional, default `false`): set to `true` to log in against PocketBase's `_superusers` collection instead of `users`. Required if the account is a superuser (Beszel 0.21+).
- `MCP_TRANSPORT` (optional): `stdio` (default) or `http` (Streamable HTTP)
- `MCP_PORT` (optional, default `8000`) and `MCP_HOST` (default `0.0.0.0`): HTTP listen address
- `MCP_AUTH_TOKEN` (optional): if set, every HTTP request except `/health` must send `Authorization: Bearer <token>`

## HTTP transport & Docker

With `MCP_TRANSPORT=http` the server exposes Streamable HTTP at `/mcp` and an unauthenticated `GET /health`.

```bash
docker run -p 8000:8000 \
  -e BESZEL_URL=http://beszel:8090 -e BESZEL_EMAIL=you@example.com \
  -e BESZEL_PASSWORD=secret -e BESZEL_SUPERUSER=true \
  -e MCP_AUTH_TOKEN=change-me \
  ghcr.io/matthiaslubbertsen/beszel-mcp:latest
```

The image defaults to `MCP_TRANSPORT=http`. See [docker-compose.example.yml](docker-compose.example.yml). Multi-arch (amd64/arm64) images are published to `ghcr.io/matthiaslubbertsen/beszel-mcp` by GitHub Actions on pushes to `master` and `v*` tags. Put the HTTP endpoint behind TLS if it is exposed beyond a trusted network.

## Usage

### With Claude Desktop

Add to your `claude_desktop_config.json`:

**Using uv (recommended):**
```json
{
  "mcpServers": {
    "beszel": {
      "command": "uvx",
      "args": ["--from", "/path/to/beszel-mcp", "beszel-mcp"],
      "env": {
        "BESZEL_URL": "http://localhost:8090",
        "BESZEL_EMAIL": "your-email@example.com",
        "BESZEL_PASSWORD": "your-password"
      }
    }
  }
}
```

**Or using Python directly:**
```json
{
  "mcpServers": {
    "beszel": {
      "command": "python",
      "args": ["-m", "beszel_mcp"],
      "env": {
        "BESZEL_URL": "http://localhost:8090",
        "BESZEL_EMAIL": "your-email@example.com",
        "BESZEL_PASSWORD": "your-password"
      }
    }
  }
}
```

### Standalone

```bash
export BESZEL_URL="http://localhost:8090"
export BESZEL_EMAIL="your-email@example.com"
export BESZEL_PASSWORD="your-password"

# Using uv (recommended)
uv run beszel-mcp

# Or with python -m
uv run python -m beszel_mcp

# Without uv
python -m beszel_mcp

# Or use fastmcp's CLI
fastmcp run src/beszel_mcp/server.py
```

## Available Tools

### list_systems
List all monitored systems.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 50)
- `filter` (optional): PocketBase filter string
- `sort` (optional): Sort order (e.g., "-created")

### list_containers
List all monitored containers.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 50)
- `filter` (optional): PocketBase filter string
- `sort` (optional): Sort order

### list_alerts
List all alerts.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 50)
- `filter` (optional): PocketBase filter string
- `sort` (optional): Sort order

### list_alert_history
List alert history.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 50)
- `filter` (optional): PocketBase filter string
- `sort` (optional): Sort order

### query_system_stats
Query statistics for a specific system.

**Parameters:**
- `system_id` (required): The system ID
- `start_time` (optional): Start time for statistics (ISO 8601 format)
- `end_time` (optional): End time for statistics (ISO 8601 format)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 100)

### query_container_stats
Query statistics for a specific container.

**Parameters:**
- `container_id` (required): The container ID
- `start_time` (optional): Start time for statistics (ISO 8601 format)
- `end_time` (optional): End time for statistics (ISO 8601 format)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page (default: 100)

## PocketBase Filter Examples

```python
# Filter by name
filter="name ~ 'server'"

# Filter by status
filter="status = 'active'"

# Filter by date range
filter="created >= '2024-01-01' && created <= '2024-12-31'"

# Complex filters
filter="(cpu > 80 || memory > 90) && status = 'active'"
```

## Why FastMCP?

This server is built with FastMCP instead of the raw MCP SDK for several reasons:

- **35% less code** - Focus on logic, not boilerplate
- **Automatic schema generation** - Type hints become JSON schemas
- **Clean decorators** - Simple `@mcp.tool()` instead of manual routing
- **Better DX** - Hot reloading, dev mode, and more

See [Why FastMCP?](docs/WHY_FASTMCP.md) for a detailed comparison.

## License

MIT

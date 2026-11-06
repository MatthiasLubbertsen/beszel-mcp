"""MCP server implementation for Beszel using FastMCP."""

import os
from typing import Optional
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .pocketbase_client import PocketBaseClient

# Initialize FastMCP server
mcp = FastMCP("beszel-mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Unauthenticated liveness probe (HTTP transport only)."""
    return JSONResponse({"status": "ok"})

# Global client instance
pb_client: Optional[PocketBaseClient] = None


def get_client() -> PocketBaseClient:
    """Get or create the PocketBase client."""
    global pb_client
    
    if pb_client is None:
        base_url = os.environ.get("BESZEL_URL")
        if not base_url:
            raise ValueError("BESZEL_URL environment variable is required")
        
        email = os.environ.get("BESZEL_EMAIL")
        password = os.environ.get("BESZEL_PASSWORD")
        
        superuser = os.environ.get("BESZEL_SUPERUSER", "").strip().lower() in (
            "1", "true", "yes", "on",
        )

        pb_client = PocketBaseClient(
            base_url, email, password, superuser, os.environ.get("BESZEL_TOKEN") or None
        )
    
    return pb_client


async def ensure_authenticated(client: PocketBaseClient) -> None:
    """Ensure the client is authenticated."""
    if client.email and client.password and not client.token:
        await client.authenticate()


@mcp.tool()
async def list_systems(
    page: int = 1,
    per_page: int = 50,
    filter: Optional[str] = None,
    sort: Optional[str] = None,
) -> dict:
    """List all monitored systems in Beszel.
    
    Args:
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        filter: PocketBase filter string (e.g., "name ~ 'server'" or "status = 'active'")
        sort: Sort order (e.g., "-created" for descending by created date)
    
    Returns:
        Dictionary containing paginated list of systems with their status and metadata
    """
    client = get_client()
    await ensure_authenticated(client)
    
    return await client.get_list(
        collection="systems",
        page=page,
        per_page=per_page,
        filter=filter,
        sort=sort,
    )


@mcp.tool()
async def list_containers(
    page: int = 1,
    per_page: int = 50,
    filter: Optional[str] = None,
    sort: Optional[str] = None,
) -> dict:
    """List all monitored containers in Beszel.
    
    Args:
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        filter: PocketBase filter string
        sort: Sort order
    
    Returns:
        Dictionary containing paginated list of containers running on monitored systems
    """
    client = get_client()
    await ensure_authenticated(client)
    
    return await client.get_list(
        collection="containers",
        page=page,
        per_page=per_page,
        filter=filter,
        sort=sort,
    )


@mcp.tool()
async def list_alerts(
    page: int = 1,
    per_page: int = 50,
    filter: Optional[str] = None,
    sort: Optional[str] = None,
) -> dict:
    """List all configured alerts in Beszel.
    
    Args:
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        filter: PocketBase filter string
        sort: Sort order
    
    Returns:
        Dictionary containing alert configurations including thresholds and notification settings
    """
    client = get_client()
    await ensure_authenticated(client)
    
    return await client.get_list(
        collection="alerts",
        page=page,
        per_page=per_page,
        filter=filter,
        sort=sort,
    )


@mcp.tool()
async def list_alert_history(
    page: int = 1,
    per_page: int = 50,
    filter: Optional[str] = None,
    sort: Optional[str] = None,
) -> dict:
    """List alert history in Beszel.
    
    Args:
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        filter: PocketBase filter string
        sort: Sort order (e.g., "-created" for most recent first)
    
    Returns:
        Dictionary containing historical records of triggered alerts
    """
    client = get_client()
    await ensure_authenticated(client)
    
    return await client.get_list(
        collection="alerts_history",
        page=page,
        per_page=per_page,
        filter=filter,
        sort=sort,
    )


@mcp.tool()
async def query_system_stats(
    system_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """Query statistics for a specific system.
    
    Args:
        system_id: The system ID to query statistics for
        start_time: Start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')
        end_time: End time in ISO 8601 format
        page: Page number (default: 1)
        per_page: Number of results per page (default: 100)
    
    Returns:
        Dictionary containing time-series data for CPU, memory, disk, and network usage
    """
    client = get_client()
    await ensure_authenticated(client)
    
    # Build filter for system and time range
    filters = [f"system = '{system_id}'"]
    
    time_filter = client.build_time_filter("created", start_time, end_time)
    if time_filter:
        filters.append(time_filter)
    
    return await client.query_stats(
        collection="system_stats",
        filter=" && ".join(filters),
        page=page,
        per_page=per_page,
        sort="-created",
    )


@mcp.tool()
async def query_container_stats(
    container_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """Query statistics for a specific container.
    
    Args:
        container_id: The container ID to query statistics for
        start_time: Start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')
        end_time: End time in ISO 8601 format
        page: Page number (default: 1)
        per_page: Number of results per page (default: 100)
    
    Returns:
        Dictionary containing time-series data for container CPU, memory, and network usage
    """
    client = get_client()
    await ensure_authenticated(client)
    
    # Build filter for container and time range
    filters = [f"container = '{container_id}'"]
    
    time_filter = client.build_time_filter("created", start_time, end_time)
    if time_filter:
        filters.append(time_filter)
    
    return await client.query_stats(
        collection="container_stats",
        filter=" && ".join(filters),
        page=page,
        per_page=per_page,
        sort="-created",
    )

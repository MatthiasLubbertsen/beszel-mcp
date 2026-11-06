"""Tests for the PocketBase client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from beszel_mcp.pocketbase_client import PocketBaseClient


@pytest.fixture
def client():
    """Create a test client."""
    return PocketBaseClient("http://localhost:8090", "test@example.com", "password123")


@pytest.mark.asyncio
async def test_authenticate(client):
    """Test authentication."""
    with patch.object(client.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "test-token-123"}
        mock_post.return_value = mock_response
        
        await client.authenticate()
        
        assert client.token == "test-token-123"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_get_list(client):
    """Test getting a list of records."""
    client.token = "test-token"
    
    with patch.object(client.client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "page": 1,
            "perPage": 50,
            "totalPages": 1,
            "totalItems": 2,
            "items": [
                {"id": "1", "name": "system1"},
                {"id": "2", "name": "system2"},
            ]
        }
        mock_get.return_value = mock_response
        
        result = await client.get_list("systems", page=1, per_page=50)
        
        assert result["totalItems"] == 2
        assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_build_time_filter(client):
    """Test building time filters."""
    # Test with both start and end time
    filter_str = client.build_time_filter(
        "created",
        "2024-01-01T00:00:00Z",
        "2024-12-31T23:59:59Z"
    )
    assert "created >= '2024-01-01T00:00:00Z'" in filter_str
    assert "created <= '2024-12-31T23:59:59Z'" in filter_str
    assert "&&" in filter_str
    
    # Test with only start time
    filter_str = client.build_time_filter(
        "created",
        "2024-01-01T00:00:00Z",
        None
    )
    assert filter_str == "created >= '2024-01-01T00:00:00Z'"
    
    # Test with only end time
    filter_str = client.build_time_filter(
        "created",
        None,
        "2024-12-31T23:59:59Z"
    )
    assert filter_str == "created <= '2024-12-31T23:59:59Z'"
    
    # Test with no time range
    filter_str = client.build_time_filter("created", None, None)
    assert filter_str == ""


@pytest.mark.asyncio
async def test_authenticate_superuser_collection():
    """Superuser login must hit the _superusers collection."""
    c = PocketBaseClient("http://localhost:8090", "a@b.c", "pw", superuser=True)
    with patch.object(c.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "t"}
        mock_post.return_value = mock_response
        await c.authenticate()
        assert "/api/collections/_superusers/auth-with-password" in mock_post.call_args.args[0]

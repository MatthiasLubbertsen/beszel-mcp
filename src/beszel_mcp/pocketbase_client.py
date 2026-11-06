"""PocketBase client for interacting with Beszel's backend."""

import httpx
from typing import Any, Optional
from datetime import datetime


class PocketBaseClient:
    """Client for interacting with PocketBase API."""

    def __init__(
        self,
        base_url: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        superuser: bool = False,
        token: Optional[str] = None,
    ):
        """Initialize the PocketBase client.
        
        Args:
            base_url: The base URL of the PocketBase instance
            email: Optional admin email for authentication
            password: Optional admin password for authentication
            superuser: Authenticate against the PocketBase ``_superusers``
                collection instead of ``users`` (needed for Beszel 0.21+
                superuser accounts)
            token: Optional pre-issued PocketBase auth token. When set, it is
                sent as-is and no login is performed.
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.superuser = superuser
        self.token: Optional[str] = token or None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> None:
        """Authenticate with PocketBase using admin credentials."""
        if not self.email or not self.password:
            return

        try:
            collection = "_superusers" if self.superuser else "users"
            response = await self.client.post(
                f"{self.base_url}/api/collections/{collection}/auth-with-password",
                json={
                    "identity": self.email,
                    "password": self.password,
                },
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("token")
        except Exception as e:
            raise Exception(f"Failed to authenticate with PocketBase: {e}")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_list(
        self,
        collection: str,
        page: int = 1,
        per_page: int = 50,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
        expand: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get a paginated list of records from a collection.
        
        Args:
            collection: The collection name
            page: Page number (default: 1)
            per_page: Number of records per page (default: 50)
            filter: PocketBase filter string
            sort: Sort order (e.g., "-created")
            expand: Fields to expand (e.g., "relField1,relField2")
            
        Returns:
            Dictionary containing paginated results
        """
        params = {
            "page": page,
            "perPage": per_page,
        }
        
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand

        try:
            response = await self.client.get(
                f"{self.base_url}/api/collections/{collection}/records",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get records from {collection}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to get records from {collection}: {e}")

    async def get_one(
        self,
        collection: str,
        record_id: str,
        expand: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get a single record by ID.
        
        Args:
            collection: The collection name
            record_id: The record ID
            expand: Fields to expand
            
        Returns:
            Dictionary containing the record
        """
        params = {}
        if expand:
            params["expand"] = expand

        try:
            response = await self.client.get(
                f"{self.base_url}/api/collections/{collection}/records/{record_id}",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get record {record_id} from {collection}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to get record {record_id} from {collection}: {e}")

    async def query_stats(
        self,
        collection: str,
        filter: str,
        page: int = 1,
        per_page: int = 100,
        sort: str = "-created",
    ) -> dict[str, Any]:
        """Query statistics records with filtering.
        
        Args:
            collection: The stats collection name (system_stats or container_stats)
            filter: PocketBase filter string
            page: Page number
            per_page: Number of records per page
            sort: Sort order
            
        Returns:
            Dictionary containing paginated statistics
        """
        return await self.get_list(
            collection=collection,
            page=page,
            per_page=per_page,
            filter=filter,
            sort=sort,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    def build_time_filter(
        self,
        field: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> str:
        """Build a time-based filter string.
        
        Args:
            field: The field name (e.g., "created")
            start_time: Start time in ISO 8601 format
            end_time: End time in ISO 8601 format
            
        Returns:
            PocketBase filter string
        """
        filters = []
        
        if start_time:
            filters.append(f"{field} >= '{start_time}'")
        if end_time:
            filters.append(f"{field} <= '{end_time}'")
            
        return " && ".join(filters) if filters else ""

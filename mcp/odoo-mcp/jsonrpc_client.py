"""Odoo JSON-RPC Client for connecting to Odoo Community Edition.

Odoo uses JSON-RPC 2.0 for external integrations.
This client handles authentication and model operations.
"""

import os
from typing import Any, Optional
import httpx


class OdooClient:
    """Async client for Odoo JSON-RPC API."""

    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """Initialize Odoo client.

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            db: Database name
            username: Odoo username
            password: Odoo password
        """
        self.url = url or os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = db or os.getenv("ODOO_DB", "odoo")
        self.username = username or os.getenv("ODOO_USERNAME", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD", "admin")
        self.uid: Optional[int] = None
        self._request_id = 0

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _call(
        self,
        service: str,
        method: str,
        args: list
    ) -> Any:
        """Make a JSON-RPC call to Odoo.

        Args:
            service: Odoo service (common, object, db)
            method: Method to call
            args: Method arguments

        Returns:
            Response result or raises exception
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args
            },
            "id": self._next_id()
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise Exception(f"HTTP error: {response.status_code}")

            data = response.json()

            if "error" in data:
                error = data["error"]
                message = error.get("data", {}).get("message", error.get("message", str(error)))
                raise Exception(f"Odoo error: {message}")

            return data.get("result")

    async def authenticate(self) -> int:
        """Authenticate with Odoo and get user ID.

        Returns:
            User ID if successful

        Raises:
            Exception if authentication fails
        """
        uid = await self._call(
            "common",
            "authenticate",
            [self.db, self.username, self.password, {}]
        )

        if not uid:
            raise Exception("Authentication failed: invalid credentials")

        self.uid = uid
        return uid

    async def version(self) -> dict:
        """Get Odoo server version info.

        Returns:
            Version information dictionary
        """
        return await self._call("common", "version", [])

    async def search(
        self,
        model: str,
        domain: list,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> list:
        """Search for records in a model.

        Args:
            model: Model name (e.g., 'res.partner', 'account.move')
            domain: Search domain (list of tuples)
            offset: Number of records to skip
            limit: Maximum records to return
            order: Sort order

        Returns:
            List of record IDs
        """
        if not self.uid:
            await self.authenticate()

        kwargs = {"offset": offset}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "search",
                [domain],
                kwargs
            ]
        )

    async def search_read(
        self,
        model: str,
        domain: list,
        fields: Optional[list] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> list:
        """Search and read records in one call.

        Args:
            model: Model name
            domain: Search domain
            fields: Fields to return (None for all)
            offset: Number of records to skip
            limit: Maximum records to return
            order: Sort order

        Returns:
            List of record dictionaries
        """
        if not self.uid:
            await self.authenticate()

        kwargs = {"offset": offset}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "search_read",
                [domain],
                kwargs
            ]
        )

    async def read(
        self,
        model: str,
        ids: list,
        fields: Optional[list] = None
    ) -> list:
        """Read specific records by ID.

        Args:
            model: Model name
            ids: List of record IDs
            fields: Fields to return (None for all)

        Returns:
            List of record dictionaries
        """
        if not self.uid:
            await self.authenticate()

        kwargs = {}
        if fields:
            kwargs["fields"] = fields

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "read",
                [ids],
                kwargs
            ]
        )

    async def create(self, model: str, values: dict) -> int:
        """Create a new record.

        Args:
            model: Model name
            values: Field values for the new record

        Returns:
            ID of created record
        """
        if not self.uid:
            await self.authenticate()

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "create",
                [values]
            ]
        )

    async def write(self, model: str, ids: list, values: dict) -> bool:
        """Update existing records.

        Args:
            model: Model name
            ids: List of record IDs to update
            values: Field values to update

        Returns:
            True if successful
        """
        if not self.uid:
            await self.authenticate()

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "write",
                [ids, values]
            ]
        )

    async def unlink(self, model: str, ids: list) -> bool:
        """Delete records.

        Args:
            model: Model name
            ids: List of record IDs to delete

        Returns:
            True if successful
        """
        if not self.uid:
            await self.authenticate()

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, "unlink",
                [ids]
            ]
        )

    async def call_method(
        self,
        model: str,
        method: str,
        args: list,
        kwargs: Optional[dict] = None
    ) -> Any:
        """Call a custom method on a model.

        Args:
            model: Model name
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method return value
        """
        if not self.uid:
            await self.authenticate()

        return await self._call(
            "object",
            "execute_kw",
            [
                self.db, self.uid, self.password,
                model, method,
                args,
                kwargs or {}
            ]
        )


# Singleton client instance
_client: Optional[OdooClient] = None


def get_client() -> OdooClient:
    """Get or create the Odoo client instance."""
    global _client
    if _client is None:
        _client = OdooClient()
    return _client

"""
Supabase client initialization and helpers.
"""

from supabase import create_client, Client
from app.config import get_settings
from app.utils import logger


_client: Client | None = None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            logger.warning("Supabase credentials not configured — database operations will fail")
            raise RuntimeError("Supabase URL and Key must be set in environment")
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized")
    return _client


async def insert_row(table: str, data: dict) -> dict:
    """Insert a row into a Supabase table and return the inserted data."""
    client = get_supabase()
    result = client.table(table).insert(data).execute()
    return result.data[0] if result.data else {}


async def update_row(table: str, match: dict, data: dict) -> dict:
    """Update rows matching the filter and return updated data."""
    client = get_supabase()
    query = client.table(table).update(data)
    for key, value in match.items():
        query = query.eq(key, value)
    result = query.execute()
    return result.data[0] if result.data else {}


async def get_rows(table: str, match: dict | None = None, limit: int = 100) -> list[dict]:
    """Fetch rows from a Supabase table with optional filtering."""
    client = get_supabase()
    query = client.table(table).select("*").limit(limit)
    if match:
        for key, value in match.items():
            query = query.eq(key, value)
    result = query.execute()
    return result.data or []


async def get_single_row(table: str, match: dict) -> dict | None:
    """Fetch a single row matching the filter."""
    rows = await get_rows(table, match, limit=1)
    return rows[0] if rows else None

"""
Shared httpx.AsyncClient singleton.

Initialized in app lifespan; avoids creating a new TCP connection per request.
"""
import logging

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


async def init_http_client() -> None:
    """Create the shared AsyncClient. Call once at startup."""
    global _client  # noqa: PLW0603
    _client = httpx.AsyncClient(timeout=10.0)
    logger.info("Shared httpx.AsyncClient initialized")


async def close_http_client() -> None:
    """Close the shared AsyncClient. Call once at shutdown."""
    global _client  # noqa: PLW0603
    if _client:
        await _client.aclose()
        _client = None
        logger.info("Shared httpx.AsyncClient closed")


def get_http_client() -> httpx.AsyncClient:
    """Return the shared AsyncClient instance."""
    if _client is None:
        raise RuntimeError("httpx.AsyncClient not initialized — call init_http_client() first")
    return _client

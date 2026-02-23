"""
Rate limiting configuration using slowapi.
Proxy-aware key extraction: CF-Connecting-IP > X-Forwarded-For > remote addr.
Authenticated users also get user_id-based keying.
"""
import ipaddress
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings

logger = logging.getLogger(__name__)


def _is_trusted_proxy(ip: str) -> bool:
    """Check if an IP is in the trusted proxies list."""
    if not settings.TRUSTED_PROXIES:
        # No trusted proxies configured — trust all forwarded headers
        # (Railway/Vercel proxy environments set X-Forwarded-For)
        return True
    try:
        addr = ipaddress.ip_address(ip)
        for proxy in settings.TRUSTED_PROXIES:
            if "/" in proxy:
                if addr in ipaddress.ip_network(proxy, strict=False):
                    return True
            elif str(addr) == proxy:
                return True
    except ValueError:
        pass
    return False


def get_rate_limit_key(request: Request) -> str:
    """Extract client identifier for rate limiting.

    Priority:
    1. CF-Connecting-IP (Cloudflare)
    2. X-Forwarded-For first IP (if proxy is trusted)
    3. Fallback to remote address
    """
    # 1. Cloudflare
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()

    # 2. X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        remote = get_remote_address(request) or ""
        if _is_trusted_proxy(remote):
            client_ip = xff.split(",")[0].strip()
            if client_ip:
                return client_ip

    # 3. Fallback
    return get_remote_address(request) or "unknown"


limiter = Limiter(key_func=get_rate_limit_key)

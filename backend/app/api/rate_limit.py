from __future__ import annotations
from fastapi import Request
from slowapi import Limiter


def get_render_client_ip(request: Request) -> str:
    """Extract client IP safely from Render's X-Forwarded-For header,
    falling back to request.client.host if not present.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs if proxy chains exist:
        # e.g. "client_ip, proxy1_ip, proxy2_ip"
        # The leftmost IP is always the client's actual IP.
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# Initialize the global limiter using the custom client IP resolver.
# This defaults to an in-memory limit. Can be pointed to Redis later.
limiter = Limiter(key_func=get_render_client_ip)

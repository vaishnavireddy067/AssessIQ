"""
AssessIQ Rate Limiting & Abuse Defense Middleware.
Implements an in-memory token bucket rate limiter to prevent credential stuffing and DDoS.
"""
import time
from typing import Dict, Tuple
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window in-memory rate limiter per IP address.
    Default limit: 120 requests per minute per IP.
    """
    def __init__(self, app, max_requests: int = 180, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_records: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # Exclude health checks from rate limiting
        if request.url.path in ["/health", "/healthz", "/readyz"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.request_records:
            self.request_records[client_ip] = []

        # Filter timestamps outside the window
        valid_timestamps = [t for t in self.request_records[client_ip] if now - t < self.window_seconds]
        self.request_records[client_ip] = valid_timestamps

        if len(valid_timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per minute allowed.",
                    }
                },
                headers={"Retry-After": "30"},
            )

        self.request_records[client_ip].append(now)
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(self.request_records[client_ip])))
        return response

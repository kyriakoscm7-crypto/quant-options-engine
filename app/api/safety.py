"""Small API boundary controls; production still needs host-level rate limits."""

import hmac
import time
from collections import deque

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 4 * 1024 * 1024


class RequestSafetyMiddleware:
    """Bound actual body bytes (including chunked requests) before JSON parsing.

    Never log request bodies. Avoid middleware-local shared visitor state.
    Proxy/server limits are still required for concurrency and slow clients.
    """

    def __init__(self, app, api_token: str = "", requests_per_minute: int = 120):
        if api_token and len(api_token) < 32:
            raise ValueError("QI_API_TOKEN must contain at least 32 characters")
        self.app = app
        self.api_token = api_token
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = [(key, value) for key, value in message.get("headers", [])
                           if key.lower() not in {b"cache-control", b"x-content-type-options",
                                                  b"referrer-policy"}]
                headers += [(b"cache-control", b"no-store"),
                            (b"x-content-type-options", b"nosniff"),
                            (b"referrer-policy", b"no-referrer")]
                message = {**message, "headers": headers}
            await send(message)

        # Streamlit sharing does not protect a separately hosted FastAPI service.
        # With a token configured, authenticate before reading or parsing bodies.
        # One bounded process-wide budget avoids IP spoofing and visitor maps.
        if self.api_token and not (scope["path"] == "/health" and scope["method"] == "GET"):
            credentials = [value for key, value in scope.get("headers", [])
                           if key.lower() == b"authorization"]
            expected = ("Bearer " + self.api_token).encode()
            if len(credentials) != 1 or not hmac.compare_digest(credentials[0], expected):
                response = JSONResponse(status_code=401, content={"detail": "Authentication required."},
                                        headers={"WWW-Authenticate": "Bearer"})
                return await response(scope, receive, private_send)
            now = time.monotonic()
            while self.request_times and now - self.request_times[0] >= 60:
                self.request_times.popleft()
            if len(self.request_times) >= self.requests_per_minute:
                response = JSONResponse(status_code=429, content={"detail": "Calculation request budget exceeded."},
                                        headers={"Retry-After": "60"})
                return await response(scope, receive, private_send)
            self.request_times.append(now)

        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > MAX_REQUEST_BYTES:
                response = JSONResponse(status_code=413, content={
                    "detail": "Request exceeds the 4 MiB limit."
                })
                return await response(scope, receive, private_send)
            chunks.append(body)
            if not message.get("more_body", False):
                break

        body = b"".join(chunks)
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, bounded_receive, private_send)

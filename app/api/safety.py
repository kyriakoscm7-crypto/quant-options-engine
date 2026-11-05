"""Small API boundary controls; production still needs host-level rate limits."""

import asyncio
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

    def __init__(
        self,
        app,
        api_token: str = "",
        requests_per_minute: int = 120,
        mode: str = "development",
    ):
        if mode not in {"production", "development"}:
            raise ValueError("QI_API_MODE must be production or development")
        if mode == "production" and not api_token:
            raise ValueError(
                "Production requires QI_API_TOKEN; local development must be explicit"
            )
        self.mode = mode
        if api_token and len(api_token) < 32:
            raise ValueError("QI_API_TOKEN must contain at least 32 characters")
        self.app = app
        self.api_token = api_token
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()
        self.active_requests = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if self.mode == "development" and scope.get("client", ("",))[0] not in {
            "127.0.0.1",
            "::1",
            "testclient",
        }:
            return await JSONResponse(
                status_code=403, content={"detail": "Development API is loopback only."}
            )(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower()
                    not in {
                        b"cache-control",
                        b"x-content-type-options",
                        b"referrer-policy",
                    }
                ]
                headers += [
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                message = {**message, "headers": headers}
            await send(message)

        # Streamlit sharing does not protect a separately hosted FastAPI service.
        # With a token configured, authenticate before reading or parsing bodies.
        # One bounded process-wide budget avoids IP spoofing and visitor maps.
        if self.api_token and not (
            scope["path"] == "/health" and scope["method"] == "GET"
        ):
            credentials = [
                value
                for key, value in scope.get("headers", [])
                if key.lower() == b"authorization"
            ]
            expected = ("Bearer " + self.api_token).encode()
            if len(credentials) != 1 or not hmac.compare_digest(
                credentials[0], expected
            ):
                response = JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
                return await response(scope, receive, private_send)
        if scope["path"] != "/health":
            now = time.monotonic()
            while self.request_times and now - self.request_times[0] >= 60:
                self.request_times.popleft()
            if len(self.request_times) >= self.requests_per_minute:
                return await JSONResponse(
                    status_code=429,
                    content={"detail": "Calculation request budget exceeded."},
                    headers={"Retry-After": "60"},
                )(scope, receive, private_send)
            self.request_times.append(now)
        if self.active_requests >= 8:
            return await JSONResponse(status_code=503, content={"detail": "API busy."})(
                scope, receive, private_send
            )
        self.active_requests += 1
        try:
            await self.handle(scope, receive, private_send)
        finally:
            self.active_requests -= 1

    async def handle(self, scope, receive, private_send):

        deadline = time.monotonic() + 15
        chunks = []
        size = 0
        while True:
            try:
                message = await asyncio.wait_for(
                    receive(), timeout=max(0.001, deadline - time.monotonic())
                )
            except TimeoutError:
                return await JSONResponse(
                    status_code=408, content={"detail": "Request body timed out."}
                )(scope, receive, private_send)
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > MAX_REQUEST_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request exceeds the 4 MiB limit."},
                )
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

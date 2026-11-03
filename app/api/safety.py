"""Small API boundary controls; production still needs host-level rate limits."""

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 4 * 1024 * 1024


class RequestSafetyMiddleware:
    """Bound actual body bytes (including chunked requests) before JSON parsing.

    Never log request bodies. Avoid middleware-local shared visitor state.
    Proxy/server limits are still required for concurrency and slow clients.
    """

    def __init__(self, app):
        self.app = app

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

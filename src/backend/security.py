"""HTTP hardening: a request body size limit and security headers on every response.

Both are plain ASGI middleware, so they also cover the static frontend, not just the API.
"""

import json


# Contact form messages are at most a few KB (see schemas.ContactRequest); anything far bigger
# is rejected before it is read into memory.
MAX_BODY_BYTES = 64 * 1024

# The site loads only its own scripts, styles, images and translations. No inline scripts or
# styles, nothing from third parties: new external resources need an entry here.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self'",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

SECURITY_HEADERS = {
    "content-security-policy": CONTENT_SECURITY_POLICY,
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "cross-origin-opener-policy": "same-origin",
    "cross-origin-resource-policy": "same-origin",
}

# The interactive API docs (development only) load Swagger UI from a CDN with inline scripts.
CSP_EXEMPT_PATHS = ("/api/docs",)


class BodySizeLimitMiddleware:
    """Answers 413 for request bodies over `max_bytes`, without reading more than that.

    Checks Content-Length up front. The body itself is read here (at most `max_bytes`, so memory
    stays bounded) before the app sees it; that also covers chunked requests without a
    Content-Length, and the 413 doesn't depend on how the app reads bodies.
    """

    def __init__(self, app, max_bytes=MAX_BODY_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = dict(scope["headers"]).get(b"content-length")
        if content_length is not None:
            try:
                too_large = int(content_length) > self.max_bytes
            except ValueError:
                too_large = True
            if too_large:
                await _reject(send)
                return

        buffered = []
        received = 0
        while True:
            message = await receive()
            buffered.append(message)
            if message["type"] != "http.request":
                break  # client disconnected; let the app see that
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                await _reject(send)
                return
            if not message.get("more_body", False):
                break

        async def replay_receive():
            # First the body read above, then whatever comes next (e.g. a disconnect).
            if buffered:
                return buffered.pop(0)
            return await receive()

        await self.app(scope, replay_receive, send)


async def _reject(send):
    body = json.dumps({"detail": "request_too_large"}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})


class SecurityHeadersMiddleware:
    """Adds SECURITY_HEADERS to every HTTP response (unless the response already sets one)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        exempt_csp = scope["path"].startswith(CSP_EXEMPT_PATHS)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name == "content-security-policy" and exempt_csp:
                        continue
                    if name.encode() not in present:
                        headers.append((name.encode(), value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)

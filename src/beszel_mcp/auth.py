"""Bearer-token auth for the HTTP transport."""

import hmac
import json

OPEN_PATHS = {"/health"}


class BearerAuthMiddleware:
    """Pure-ASGI middleware requiring ``Authorization: Bearer <token>``.

    ``/health`` stays open so orchestrators can probe it.
    """

    def __init__(self, app, token: str):
        self.app = app
        self.token = token.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in OPEN_PATHS:
            await self.app(scope, receive, send)
            return

        header = dict(scope["headers"]).get(b"authorization", b"")
        scheme, _, supplied = header.partition(b" ")
        if scheme.lower() == b"bearer" and hmac.compare_digest(supplied.strip(), self.token):
            await self.app(scope, receive, send)
            return

        body = json.dumps({"error": "unauthorized"}).encode()
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"www-authenticate", b"Bearer"),
            ],
        })
        await send({"type": "http.response.body", "body": body})

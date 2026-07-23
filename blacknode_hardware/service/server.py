"""Small standard-library JSON-RPC HTTP server for local device testing."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .runtime import HardwareRuntime


class HardwareRequestHandler(BaseHTTPRequestHandler):
    runtime: HardwareRuntime
    auth_token: str | None = None

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send(
        self,
        status: int,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        if self.auth_token is None:
            return True
        from ..auth import authorization_matches

        return authorization_matches(self.headers.get("Authorization"), self.auth_token)

    def _require_authorization(self) -> bool:
        if self._authorized():
            return True
        self._send(
            401,
            {"ok": False, "error": "authentication required"},
            {"WWW-Authenticate": "Bearer"},
        )
        return False

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(
                200,
                {
                    "ok": True,
                    "service": "blacknode-hardware",
                    "auth_required": self.auth_token is not None,
                },
            )
            return
        if not self._require_authorization():
            return
        if self.path == "/status":
            self._send(200, self.runtime.status())
        elif self.path == "/capabilities":
            self._send(200, self.runtime.capabilities())
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/rpc":
            self._send(404, {"ok": False, "error": "not found"})
            return
        if not self._require_authorization():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            result = self.runtime.call(str(request.get("method", "")), request.get("params") or {})
            self._send(200, {"jsonrpc": "2.0", "id": request.get("id"), "result": result})
        except Exception as exc:
            self._send(200, {"jsonrpc": "2.0", "id": None, "error": {"message": str(exc)}})


def create_server(
    runtime: HardwareRuntime,
    host: str = "127.0.0.1",
    port: int = 8765,
    auth_token: str | None = None,
) -> ThreadingHTTPServer:
    handler = type(
        "BoundHardwareRequestHandler",
        (HardwareRequestHandler,),
        {"runtime": runtime, "auth_token": auth_token},
    )
    return ThreadingHTTPServer((host, port), handler)


def serve(
    runtime: HardwareRuntime,
    host: str = "127.0.0.1",
    port: int = 8765,
    auth_token: str | None = None,
) -> None:
    server = create_server(runtime, host, port, auth_token=auth_token)
    print(f"blacknode-hardware listening on http://{host}:{port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        runtime.close()

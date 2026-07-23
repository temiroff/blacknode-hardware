"""Small standard-library JSON-RPC HTTP server for local device testing."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .runtime import HardwareRuntime


class HardwareRequestHandler(BaseHTTPRequestHandler):
    runtime: HardwareRuntime

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"ok": True, "service": "blacknode-hardware"})
        elif self.path == "/status":
            self._send(200, self.runtime.status())
        elif self.path == "/capabilities":
            self._send(200, self.runtime.capabilities())
        else:
            self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/rpc":
            self._send(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            result = self.runtime.call(str(request.get("method", "")), request.get("params") or {})
            self._send(200, {"jsonrpc": "2.0", "id": request.get("id"), "result": result})
        except Exception as exc:
            self._send(200, {"jsonrpc": "2.0", "id": None, "error": {"message": str(exc)}})


def create_server(runtime: HardwareRuntime, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    handler = type("BoundHardwareRequestHandler", (HardwareRequestHandler,), {"runtime": runtime})
    return ThreadingHTTPServer((host, port), handler)


def serve(runtime: HardwareRuntime, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = create_server(runtime, host, port)
    print(f"blacknode-hardware listening on http://{host}:{port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        runtime.close()

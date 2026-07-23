"""Hardware service runtime with honest disconnected-device status."""

from __future__ import annotations

from typing import Any


class HardwareRuntime:
    def __init__(self, provider: Any | None = None, device_id: str = "device") -> None:
        self.provider = provider
        self.device_id = device_id

    def status(self) -> dict[str, Any]:
        if self.provider is None:
            return {
                "device_id": self.device_id,
                "connected": False,
                "armed": False,
                "capabilities": [],
                "error": "no hardware adapter configured",
            }
        state = self.provider.state()
        return state.as_dict() if hasattr(state, "as_dict") else dict(state)

    def capabilities(self) -> dict[str, Any]:
        status = self.status()
        return {
            "device_id": status.get("device_id", self.device_id),
            "connected": bool(status.get("connected", False)),
            "capabilities": list(status.get("capabilities", [])),
        }

    def stop(self) -> dict[str, Any]:
        if self.provider is None:
            return {"ok": False, "error": "no hardware adapter configured"}
        self.provider.stop()
        if hasattr(self.provider, "disarm"):
            self.provider.disarm()
        return {"ok": True, "status": self.status()}

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        del params
        if method == "get_status":
            return self.status()
        if method == "get_capabilities":
            return self.capabilities()
        if method == "stop":
            result = self.stop()
            if not result["ok"]:
                raise RuntimeError(result["error"])
            return result
        raise ValueError(f"unknown method: {method}")

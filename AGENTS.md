# blacknode-hardware Agent Instructions

This package owns generic hardware contracts, device state, safety boundaries,
and replaceable hardware adapters for Blacknode.

Keep workflows dependent on stable capabilities such as `mobile_base`,
`camera`, `range_sensor`, `battery`, and `servo_bus`. Put transport details,
device paths, register maps, SDK imports, and platform-specific code behind
adapters.

Safety requirements:

- Devices start disarmed.
- Motion commands require explicit authorization.
- Commands must expire when their freshness deadline passes.
- Stop must be idempotent and safe to call repeatedly.
- Every physical provider needs a hardware-free mock or replay provider.
- Optional hardware dependencies must not break package discovery.

Verification:

```powershell
python -m pytest tests
```

Physical hardware paths are not considered verified by unit tests.

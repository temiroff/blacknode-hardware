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
- Do not add mock, fake, simulated, or hardcoded hardware providers.
- Hardware-free tests may validate contracts and configuration but must not
  pretend that a physical device responded.
- Never write pairing tokens to service logs or place them in process
  arguments, tracked files, URLs, or deployment artifacts.
- Deployment and motion endpoints require authenticated transport and must
  never be enabled in unauthenticated mode.
- Optional hardware dependencies must not break package discovery.

Verification:

```powershell
python -m pytest tests
```

Physical hardware paths are not considered verified by unit tests.

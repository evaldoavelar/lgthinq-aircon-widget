"""ThinQ SDK adapter; upstream exceptions never cross this boundary."""

import asyncio
from copy import deepcopy
from typing import Protocol


class BackendError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class Client(Protocol):
    async def discover(self) -> list[dict]: ...
    async def profile(self, device_id: str) -> dict: ...
    async def status(self, device_id: str) -> dict: ...
    async def control(self, device_id: str, payload: dict) -> None: ...


class SDKClient:
    def __init__(self, api, *, allow_control=False, timeout=15, interval=1):
        self.api, self.allow_control = api, allow_control
        self.timeout, self.interval = timeout, interval
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def _call(self, method, *args):
        async with self._lock:
            loop = asyncio.get_running_loop()
            await asyncio.sleep(max(0, self.interval - (loop.time() - self._last)))
            self._last = loop.time()
            try:
                return await asyncio.wait_for(method(*args), self.timeout)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                code = str(getattr(exc, "code", ""))
                if code in {"1103", "1218", "1302"} or getattr(exc, "status", None) == 401:
                    category = "auth_required"
                elif code in {"1307", "1310"}:
                    category = "region_unsupported"
                elif code in {"1205", "1213", "1224"}:
                    category = "device_absent"
                elif code in {"1219", "1220", "1221", "2101", "2201", "2202"}:
                    category = "unsupported"
                elif code == "1222":
                    category = "device_offline"
                elif code == "1306":
                    category = "rate_limited"
                else:
                    category = (
                        "network_error"
                        if (
                            isinstance(exc, (OSError, TimeoutError))
                            or type(exc).__module__.startswith("aiohttp.client_exceptions")
                        )
                        else "operational_error"
                    )
                raise BackendError(category) from None

    async def discover(self):
        result = await self._call(self.api.async_get_device_list)
        if not isinstance(result, list):
            raise BackendError("invalid_response")
        return result

    async def profile(self, device_id):
        result = await self._call(self.api.async_get_device_profile, device_id)
        if not isinstance(result, dict):
            raise BackendError("invalid_response")
        return result

    async def status(self, device_id):
        result = await self._call(self.api.async_get_device_status, device_id)
        if not isinstance(result, dict):
            raise BackendError("invalid_response")
        return result

    async def control(self, device_id, payload):
        if not self.allow_control:
            raise BackendError("real_control_not_authorized")
        await self._call(self.api.async_post_device_control, device_id, payload)


SIM_PROFILE = {
    "property": {
        "operation": {
            "airConOperationMode": {
                "mode": ["r", "w"],
                "type": "enum",
                "value": {"w": ["POWER_ON", "POWER_OFF"]},
            }
        },
        "temperatureInUnits": [
            {
                "unit": "C",
                "targetTemperature": {
                    "mode": ["r", "w"],
                    "type": "range",
                    "value": {"w": {"min": 18, "max": 30, "step": 1}},
                },
            }
        ],
    }
}


# Synthetic display fixture: never used as a fallback for an actual LG profile.
SIM_PROFILE["property"].update(
    {
        "airConJobMode": {
            "currentJobMode": {
                "mode": ["r", "w"],
                "type": "enum",
                "value": {"w": ["COOL", "AUTO", "AIR_DRY", "FAN"]},
            }
        },
        "airFlow": {
            "windStrength": {
                "mode": ["r", "w"],
                "type": "enum",
                "value": {"w": ["LOW", "MID", "HIGH", "AUTO"]},
            }
        },
        "powerSave": {
            "powerSaveEnabled": {"mode": ["r", "w"], "type": "enum", "value": {"w": [False, True]}}
        },
        "windDirection": {
            "rotateUpDown": {"mode": ["r", "w"], "type": "enum", "value": {"w": [False, True]}}
        },
        "sleepTimer": {
            "relativeStopTimer": {"mode": ["r"], "type": "enum", "value": {"r": ["UNSET"]}}
        },
    }
)
SIM_PROFILE["property"]["temperatureInUnits"][0]["currentTemperature"] = {
    "mode": ["r"],
    "type": "range",
    "value": {"r": {"min": 0, "max": 50}},
}


class SimulationClient:
    def __init__(self):
        self.state = {
            "operation": {"airConOperationMode": "POWER_OFF"},
            "airConJobMode": {"currentJobMode": "COOL"},
            "airFlow": {"windStrength": "AUTO"},
            "powerSave": {"powerSaveEnabled": False},
            "windDirection": {"rotateUpDown": True},
            "sleepTimer": {"relativeStopTimer": "UNSET"},
            "temperatureInUnits": [
                {"unit": "C", "targetTemperature": 24, "currentTemperature": 26}
            ],
        }

    async def discover(self):
        return [
            {"deviceId": "synthetic-ac", "deviceInfo": {"deviceType": "DEVICE_AIR_CONDITIONER"}}
        ]

    async def profile(self, device_id):
        return deepcopy(SIM_PROFILE)

    async def status(self, device_id):
        return deepcopy(self.state)

    async def control(self, device_id, payload):
        for resource, changes in deepcopy(payload).items():
            if resource in {"temperatureInUnits", "twoSetTemperatureInUnits"}:
                # Control uses an object; state/profile use arrays grouped by unit.
                for change in [changes] if isinstance(changes, dict) else changes:
                    existing = next(
                        (
                            item
                            for item in self.state[resource]
                            if item.get("unit") == change.get("unit")
                        ),
                        None,
                    )
                    if existing is not None:
                        existing.update(change)
                    else:
                        self.state[resource].append(change)
            elif isinstance(changes, dict):
                self.state.setdefault(resource, {}).update(changes)
            else:
                self.state[resource] = changes

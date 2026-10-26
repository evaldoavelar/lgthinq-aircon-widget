"""Async orchestration, confirmed state and bounded reconnect polling."""

import asyncio
import time

from .client import BackendError, Client
from .credentials import CredentialError
from .models import Snapshot, capabilities


class Engine:
    def __init__(
        self,
        client: Client,
        device_id: str,
        *,
        simulated=False,
        device_index=None,
        allow_control=False,
    ):
        self.client, self.device_id = client, device_id
        self.snapshot = Snapshot(simulated=simulated)
        self._lock = asyncio.Lock()
        self.device_index = device_index
        self.allow_control = allow_control
        self._profile = None

    async def _refresh(self):
        if self.device_id is None:
            devices = await self.client.discover()
            if self.device_index is None or not 0 <= self.device_index < len(devices):
                raise BackendError("device_absent")
            self.device_id = devices[self.device_index].get("deviceId")
            if not self.device_id:
                raise BackendError("invalid_response")
        if self._profile is None:
            self._profile = await self.client.profile(self.device_id)
        state = await self.client.status(self.device_id)
        self.snapshot.capabilities = capabilities(self._profile)
        if not (self.snapshot.simulated or self.allow_control):
            # Permission is an explicit operator choice, separate from LG support.
            for capability in self.snapshot.capabilities.values():
                capability.writable = False
        self.snapshot.state = state
        self.snapshot.updated_at = time.time()
        self.snapshot.error = None
        self.snapshot.connection = "connected"

    def _failure(self, exc):
        self.snapshot.error = (
            exc.code
            if isinstance(exc, BackendError)
            else "credential_required"
            if isinstance(exc, CredentialError)
            else "dependency_missing"
            if isinstance(exc, ImportError)
            else "operational_error"
        )
        self.snapshot.connection = (
            "auth_required"
            if self.snapshot.error in {"auth_required", "credential_required"}
            else "error"
        )

    async def refresh(self):
        async with self._lock:
            self.snapshot.connection = "connecting"
            try:
                await self._refresh()
            except asyncio.CancelledError:
                self.snapshot.connection = "disconnected"
                raise
            except Exception as exc:
                self._failure(exc)
        return self.snapshot

    async def command(self, key, value):
        async with self._lock:
            cap = self.snapshot.capabilities.get(key)
            if cap is None:
                raise ValueError("Unknown capability")
            cap.validate(value)
            payload = {cap.path[-1]: value}
            for part in reversed(cap.path[:-1]):
                payload = {
                    part: (
                        {**payload, "unit": cap.unit}
                        if part in {"temperature", "temperatureInUnits", "twoSetTemperatureInUnits"}
                        and cap.unit
                        else payload
                    )
                }
            self.snapshot.connection = "command_pending"
            try:
                await self.client.control(self.device_id, payload)
                # Never publish intended value as confirmation.
                await self._refresh()
            except asyncio.CancelledError:
                self.snapshot.connection = "disconnected"
                raise
            except Exception as exc:
                self._failure(exc)
        return self.snapshot

    async def monitor(self, stop: asyncio.Event, interval=15):
        delay = interval
        try:
            while not stop.is_set():
                await self.refresh()
                # Auth failures wait for explicit reconfiguration/restart.
                if self.snapshot.connection == "auth_required":
                    await stop.wait()
                    break
                delay = interval if self.snapshot.connection == "connected" else min(delay * 2, 900)
                try:
                    await asyncio.wait_for(stop.wait(), timeout=delay)
                except TimeoutError:
                    pass
        finally:
            self.snapshot.connection = "disconnected"

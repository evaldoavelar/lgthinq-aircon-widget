"""Local setup and connection lifecycle, independent of the desktop transport."""

import asyncio
from uuid import uuid4

from .client import BackendError
from .config import configure, load, validate
from .credentials import CredentialError, Vault
from .engine import Engine
from .live import LiveClient
from .models import Snapshot


class LocalController:
    def __init__(
        self, path, *, client_factory=LiveClient, vault_factory=Vault, control_disabled=False
    ):
        self.path = path
        self.client_factory = client_factory
        self.vault_factory = vault_factory
        self.control_disabled = control_disabled
        self.config = load(path) if path.exists() else validate({"client_id": str(uuid4())})
        self._apply_control_policy()
        self.engine = None
        self.client = self  # The D-Bus lifecycle calls client.close().
        self.snapshot = Snapshot(connection="disconnected", error="setup_required")
        self.devices = []
        self.setup_error = None
        self.setup_busy = False
        self._lock = asyncio.Lock()

    def settings(self):
        # No credential read, secret, or raw LG response belongs in this object.
        return {
            "country": self.config["country"],
            "device_id": self.config["device_id"],
            "allow_control": self.config["allow_control"],
            "remote": bool(self.config["endpoint"]),
            "devices": self.devices,
            "busy": self.setup_busy,
            "error": self.setup_error,
        }

    @property
    def snapshot(self):
        snapshot = self.engine.snapshot if self.engine else self._snapshot
        if self.control_disabled:
            for capability in snapshot.capabilities.values():
                capability.writable = False
        return snapshot

    def _apply_control_policy(self):
        if self.control_disabled:
            self.config["allow_control"] = False

    @snapshot.setter
    def snapshot(self, value):
        self._snapshot = value

    def _client(self):
        return self.client_factory(
            account=self.config["account"],
            country=self.config["country"],
            client_id=self.config["client_id"],
            allow_control=self.config["allow_control"],
        )

    async def _close_engine(self):
        if self.engine:
            await self.engine.client.close()
        self.engine = None
        self.snapshot = Snapshot(connection="disconnected", error="setup_required")

    async def _discover(self):
        client = self._client()
        try:
            raw = await client.discover()
        finally:
            await client.close()
        self.devices = []
        for device in raw:
            info = device.get("deviceInfo", {})
            if info.get("deviceType") != "DEVICE_AIR_CONDITIONER":
                continue
            identifier = device.get("deviceId")
            if isinstance(identifier, str) and identifier:
                alias = info.get("alias") or info.get("deviceName")
                self.devices.append(
                    {
                        "id": identifier,
                        "label": str(alias)[:160]
                        if alias
                        else f"Ar-condicionado {len(self.devices) + 1}",
                    }
                )
        # Legacy indices refer to the complete discovery list, not the filtered list.
        selected = self.config["device_id"]
        index = self.config["device_index"]
        if not selected and index is not None:
            if index < len(raw):
                candidate = raw[index].get("deviceId")
                if any(d["id"] == candidate for d in self.devices):
                    selected = candidate
            if not selected:
                self.setup_error = "selection_required"
                return
        if not selected and len(self.devices) == 1:
            selected = self.devices[0]["id"]
        if selected and any(d["id"] == selected for d in self.devices):
            self.config = configure(
                self.path, {"device_id": selected, "device_index": None}, clear_none=True
            )
            self._apply_control_policy()
        elif selected:
            self.setup_error = "device_absent"
        else:
            self.setup_error = "selection_required" if self.devices else "no_devices"

    def _failure(self, exc):
        self.setup_error = (
            exc.code
            if isinstance(exc, BackendError)
            else "credential_required"
            if isinstance(exc, CredentialError)
            else "invalid_settings"
            if isinstance(exc, ValueError)
            else "dependency_missing"
            if isinstance(exc, ImportError)
            else "operational_error"
        )
        # Keep the last confirmed state, but publish the failure even with an
        # existing engine: assigning _snapshot alone is hidden by the getter.
        self.snapshot.connection = (
            "auth_required"
            if self.setup_error in {"auth_required", "credential_required"}
            else "error"
        )
        self.snapshot.error = self.setup_error

    async def configure(self, values, token):
        async with self._lock:
            self.setup_busy = True
            self.setup_error = None
            try:
                if not isinstance(values, dict) or set(values) - {
                    "country",
                    "device_id",
                    "allow_control",
                    "convert_to_local",
                }:
                    raise ValueError("Invalid settings")
                if self.config["endpoint"] and values.get("convert_to_local") is not True:
                    raise ValueError("Explicit local conversion required")
                if not isinstance(token, str) or len(token) > 16384:
                    raise ValueError("Invalid credential")
                changes = {k: v for k, v in values.items() if k != "convert_to_local"}
                if changes.get("device_id") is not None:
                    changes["device_index"] = None
                if self.config["endpoint"]:
                    changes["endpoint"] = None
                new_country = changes.get("country", self.config["country"])
                if not isinstance(new_country, str):
                    raise ValueError("Invalid country")
                if new_country.upper() != self.config["country"]:
                    changes.update(device_id=None, device_index=None)
                    self.devices = []
                proposed = validate({**self.config, **changes})
                if proposed["device_id"] != self.config["device_id"] and proposed["device_id"]:
                    if not any(d["id"] == proposed["device_id"] for d in self.devices):
                        raise ValueError("Discover before selecting a device")
                # Vault operations can involve a graphical unlock prompt; never block GLib/QML.
                if token:
                    await asyncio.to_thread(
                        lambda: self.vault_factory().store(proposed["account"], token)
                    )
                self.config = configure(
                    self.path, {"client_id": self.config["client_id"], **changes}, clear_none=True
                )
                self._apply_control_policy()
                await self._close_engine()
                await self._discover()
                await self._after_discovery()
            except Exception as exc:
                self._failure(exc)
            finally:
                token = None
                self.setup_busy = False

    async def discover(self):
        async with self._lock:
            self.setup_busy = True
            self.setup_error = None
            try:
                if self.config["endpoint"]:
                    raise ValueError("Explicit local conversion required")
                await self._discover()
                await self._close_engine()
                await self._after_discovery()
            except Exception as exc:
                self._failure(exc)
            finally:
                self.setup_busy = False

    async def _after_discovery(self):
        if self.setup_error == "device_absent":
            self.snapshot = Snapshot(connection="error", error="device_absent")
        else:
            await self._refresh()

    async def _refresh(self, *, explicit=False):
        if self.config["endpoint"]:
            # Existing remote configuration is read-only to the local setup UI.
            if self.engine is None:
                from .remote import RemoteEngine

                self.engine = RemoteEngine(
                    self.config["endpoint"],
                    lambda: self.vault_factory(service="lgthinq-homelab-api").read("default"),
                )
            if explicit:
                await self.engine.request_refresh()
            else:
                await self.engine.refresh()
            self.snapshot = self.engine.snapshot
            return
        if not self.config["device_id"]:
            if self.config["device_index"] is not None:
                await self._discover()
            if not self.config["device_id"]:
                self.snapshot = Snapshot(connection="disconnected", error="setup_required")
                return
        if self.engine is None:
            self.engine = Engine(
                self._client(),
                self.config["device_id"],
                allow_control=self.config["allow_control"],
            )
        await self.engine.refresh()
        self.snapshot = self.engine.snapshot
        if self.config["device_id"]:
            self.setup_error = self.snapshot.error

    async def refresh(self):
        return await self._read(explicit=False)

    async def request_refresh(self):
        return await self._read(explicit=True)

    async def _read(self, *, explicit):
        async with self._lock:
            try:
                await self._refresh(explicit=explicit)
            except Exception as exc:
                self._failure(exc)
        return self.snapshot

    async def command(self, key, value):
        async with self._lock:
            if self.control_disabled:
                raise ValueError("Real control disabled for this service session")
            if self.engine is None:
                raise ValueError("Setup required")
            await self.engine.command(key, value)
            self.snapshot = self.engine.snapshot
        return self.snapshot

    async def close(self):
        if self.engine:
            close = getattr(self.engine, "close", None) or self.engine.client.close
            await close()
            self.engine = None

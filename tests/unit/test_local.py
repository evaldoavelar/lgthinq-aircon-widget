"""Integrated local setup with synthetic devices and an in-memory credential vault."""

import json
import tempfile
import unittest
from pathlib import Path

from lgthinq_daemon.client import BackendError, SimulationClient
from lgthinq_daemon.config import configure, load
from lgthinq_daemon.credentials import CredentialError
from lgthinq_daemon.local import LocalController


class LocalTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.json"
        self.secret = None
        self.fail_vault = False
        self.failure = None
        self.devices = [
            {
                "deviceId": "synthetic-ac",
                "deviceInfo": {"deviceType": "DEVICE_AIR_CONDITIONER", "alias": "Sala"},
            }
        ]
        self.calls = []
        owner = self

        class Vault:
            def store(self, account, token):
                if owner.fail_vault:
                    raise CredentialError("synthetic locked vault")
                owner.secret = token

        class Client(SimulationClient):
            def __init__(self, **kwargs):
                super().__init__()
                owner.calls.append(kwargs)

            async def discover(self):
                if owner.failure:
                    raise BackendError(owner.failure)
                return owner.devices

            async def close(self):
                pass

        self.local = LocalController(self.path, client_factory=Client, vault_factory=Vault)

    async def test_first_setup_and_secret_never_in_public_state(self):
        await self.local.refresh()
        self.assertEqual(self.local.snapshot.error, "setup_required")
        self.assertFalse(self.path.exists())
        await self.local.configure({"country": "br", "allow_control": False}, "synthetic-secret")
        self.assertEqual(self.secret, "synthetic-secret")
        self.assertEqual(self.local.snapshot.connection, "connected")
        self.assertEqual(load(self.path)["device_id"], "synthetic-ac")
        self.assertNotIn("synthetic-secret", self.path.read_text())
        self.assertNotIn("synthetic-secret", json.dumps(self.local.settings()))
        self.assertNotIn("synthetic-secret", json.dumps(self.local.snapshot.to_dict()))
        self.assertFalse(any(c.writable for c in self.local.snapshot.capabilities.values()))
        await self.local.configure({"allow_control": True}, "")
        self.assertEqual(self.secret, "synthetic-secret")
        await self.local.command("temperatureInUnits.targetTemperature.C", 25)
        self.assertEqual(
            self.local.snapshot.state["temperatureInUnits"][0]["targetTemperature"], 25
        )
        await self.local.close()

    async def test_multiple_devices_require_selection_and_keep_stable_id(self):
        self.devices.append(
            {"deviceId": "second", "deviceInfo": {"deviceType": "DEVICE_AIR_CONDITIONER"}}
        )
        await self.local.configure({"country": "BR"}, "synthetic")
        self.assertEqual(self.local.setup_error, "selection_required")
        self.assertIsNone(load(self.path)["device_id"])
        await self.local.configure({"device_id": "second"}, "")
        self.devices.reverse()
        await self.local.discover()
        self.assertEqual(load(self.path)["device_id"], "second")
        self.devices = []
        await self.local.discover()
        self.assertEqual(self.local.snapshot.error, "device_absent")
        self.assertEqual(load(self.path)["device_id"], "second")
        await self.local.close()

    async def test_empty_auth_locked_and_invalid_are_sanitized(self):
        self.fail_vault = True
        await self.local.configure({}, "synthetic")
        self.assertEqual(self.local.setup_error, "credential_required")
        self.assertFalse(self.path.exists())
        self.fail_vault = False
        self.failure = "auth_required"
        await self.local.configure({}, "synthetic")
        self.assertEqual(self.local.snapshot.connection, "auth_required")
        self.failure = None
        self.devices = []
        await self.local.configure({}, "replacement")
        self.assertEqual(self.local.setup_error, "no_devices")
        for values in [
            {"country": None},
            {"country": "invalid"},
            {"pat": "forbidden"},
            {"device_id": "unseen"},
        ]:
            await self.local.configure(values, "")
            self.assertEqual(self.local.setup_error, "invalid_settings")
        await self.local.close()

    async def test_country_and_pat_changes_recreate_client_preserve_uuid(self):
        await self.local.configure({}, "first")
        uuid = load(self.path)["client_id"]
        previous = self.local.engine
        await self.local.configure({"country": "US"}, "second")
        self.assertIsNot(previous, self.local.engine)
        self.assertEqual(self.calls[-1]["country"], "US")
        self.assertEqual(load(self.path)["client_id"], uuid)
        await self.local.close()

    async def test_legacy_index_migrates_only_after_valid_discovery(self):
        configure(self.path, {"device_index": 0})
        self.local.config = load(self.path)
        self.failure = "network_error"
        await self.local.refresh()
        self.assertIsNone(load(self.path)["device_id"])
        self.failure = None
        await self.local.refresh()
        self.assertEqual(load(self.path)["device_id"], "synthetic-ac")
        self.assertIsNone(load(self.path)["device_index"])
        await self.local.close()

    async def test_remote_requires_explicit_conversion(self):
        configure(self.path, {"endpoint": "https://synthetic.example", "device_index": 0})
        self.local.config = load(self.path)
        await self.local.configure({}, "synthetic")
        self.assertEqual(self.local.setup_error, "invalid_settings")
        self.assertEqual(load(self.path)["endpoint"], "https://synthetic.example")
        await self.local.configure({"convert_to_local": True}, "synthetic")
        self.assertIsNone(load(self.path)["endpoint"])
        self.assertEqual(self.local.snapshot.connection, "connected")
        await self.local.close()

    async def test_discovery_failure_updates_existing_engine_and_recovers(self):
        await self.local.configure({}, "synthetic")
        confirmed = self.local.snapshot.state.copy()
        for failure, connection in [("network_error", "error"), ("auth_required", "auth_required")]:
            with self.subTest(failure=failure):
                self.failure = failure
                await self.local.discover()
                self.assertEqual(self.local.snapshot.connection, connection)
                self.assertEqual(self.local.snapshot.error, failure)
                self.assertEqual(self.local.snapshot.state, confirmed)
                self.failure = None
                await self.local.discover()
                self.assertEqual(self.local.snapshot.connection, "connected")
                self.assertIsNone(self.local.snapshot.error)
        await self.local.close()


class VaultSelectionTests(unittest.TestCase):
    def test_safe_automatic_selection_and_kwallet6_without_reading_secrets(self):
        import os
        from types import SimpleNamespace
        from unittest.mock import patch

        try:
            import dbus
            from keyring.backends import SecretService, kwallet
        except ImportError:
            self.skipTest("keyring/dbus unavailable")
        from lgthinq_daemon.credentials import Vault

        class Secret:
            __module__ = "keyring.backends.SecretService"
            priority = 5

        class Wallet:
            __module__ = "keyring.backends.kwallet"
            priority = 0

        with (
            patch.dict(os.environ, {"PYTHON_KEYRING_BACKEND": ""}),
            patch.object(SecretService, "Keyring", Secret),
            patch.object(kwallet, "DBusKeyring", Wallet),
        ):
            self.assertIsInstance(Vault().backend, Secret)
            Secret.priority = 0
            bus = SimpleNamespace(
                list_names=lambda: [], list_activatable_names=lambda: ["org.kde.kwalletd6"]
            )
            with patch.object(dbus, "SessionBus", return_value=bus):
                backend = Vault().backend
                self.assertEqual(backend.bus_name, "org.kde.kwalletd6")
                self.assertEqual(backend.object_path, "/modules/kwalletd6")
            bus.list_activatable_names = lambda: []
            with patch.object(dbus, "SessionBus", return_value=bus):
                with self.assertRaises(CredentialError):
                    Vault()

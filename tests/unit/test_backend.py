"""Offline regression tests; no credential, bus, network or appliance required."""

import asyncio
import unittest
from types import SimpleNamespace

from lgthinq_daemon.cli import parser, run
from lgthinq_daemon.client import BackendError, SDKClient, SimulationClient
from lgthinq_daemon.credentials import CredentialError, Vault
from lgthinq_daemon.engine import Engine
from lgthinq_daemon.models import Capability, capabilities


class BackendTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmed_roundtrip(self):
        e = Engine(SimulationClient(), "synthetic-ac", simulated=True)
        await e.refresh()
        await e.command("temperatureInUnits.targetTemperature.C", 25)
        self.assertEqual(e.snapshot.state["temperatureInUnits"][0]["targetTemperature"], 25)
        self.assertEqual(e.snapshot.connection, "connected")

    async def test_reject_unsupported_and_invalid(self):
        e = Engine(SimulationClient(), "synthetic-ac", simulated=True)
        await e.refresh()
        for key, value in [
            ("eco", True),
            ("temperatureInUnits.targetTemperature.C", 90),
            ("temperatureInUnits.targetTemperature.C", 24.5),
        ]:
            with self.assertRaises(ValueError):
                await e.command(key, value)

    async def test_auth_sanitized(self):
        class SensitiveError(Exception):
            code = "1103"

        async def fail(*args):
            raise SensitiveError("PAT SECRET")

        sdk = SDKClient(SimpleNamespace(async_get_device_list=fail), interval=0)
        with self.assertRaises(BackendError) as ctx:
            await sdk.discover()
        self.assertEqual(str(ctx.exception), "auth_required")

    async def test_real_control_denied(self):
        sdk = SDKClient(None)
        with self.assertRaisesRegex(BackendError, "not_authorized"):
            await sdk.control("device", {})
        args = parser().parse_args(["command", "key", "true"])
        with self.assertRaisesRegex(ValueError, "Real control disabled"):
            await run(args)

    async def test_error_categories(self):
        for code, category in [
            ("1307", "region_unsupported"),
            ("1205", "device_absent"),
            ("1219", "unsupported"),
            ("1306", "rate_limited"),
        ]:

            async def fail(code=code):
                exc = RuntimeError("private SDK message")
                exc.code = code
                raise exc

            sdk = SDKClient(SimpleNamespace(async_get_device_list=fail), interval=0)
            with self.assertRaisesRegex(BackendError, category):
                await sdk.discover()

    async def test_sdk_signatures_and_malformed_response(self):
        calls = []

        async def read(device):
            calls.append(device)
            return {}

        sdk = SDKClient(
            SimpleNamespace(async_get_device_profile=read, async_get_device_status=read), interval=0
        )
        self.assertEqual(await sdk.profile("synthetic"), {})
        self.assertEqual(await sdk.status("synthetic"), {})
        self.assertEqual(calls, ["synthetic", "synthetic"])

        async def invalid():
            return None

        sdk.api = SimpleNamespace(async_get_device_list=invalid)
        with self.assertRaisesRegex(BackendError, "invalid_response"):
            await sdk.discover()

    async def test_no_device(self):
        class Empty(SimulationClient):
            async def discover(self):
                return []

        from lgthinq_daemon.cli import operate

        args = parser().parse_args(["--simulate", "status"])
        with self.assertRaisesRegex(ValueError, "Device absent"):
            await operate(Empty(), args)

    async def test_timeout(self):
        async def slow():
            await asyncio.sleep(10)

        sdk = SDKClient(SimpleNamespace(async_get_device_list=slow), timeout=0.001, interval=0)
        with self.assertRaisesRegex(BackendError, "network_error"):
            await sdk.discover()

    async def test_reconnect_and_auth_stop(self):
        class Flaky(SimulationClient):
            failures = 1

            async def status(self, device):
                if self.failures:
                    self.failures -= 1
                    raise BackendError("network_error")
                return await super().status(device)

        e = Engine(Flaky(), "synthetic-ac")
        await e.refresh()
        self.assertEqual(e.snapshot.connection, "error")
        await e.refresh()
        self.assertEqual(e.snapshot.connection, "connected")

    async def test_failed_command_preserves_confirmed_state(self):
        class Broken(SimulationClient):
            async def control(self, device, payload):
                raise BackendError("network_error")

        e = Engine(Broken(), "synthetic-ac", simulated=True)
        await e.refresh()
        await e.command("temperatureInUnits.targetTemperature.C", 25)
        self.assertEqual(e.snapshot.state["temperatureInUnits"][0]["targetTemperature"], 24)
        self.assertEqual(e.snapshot.error, "network_error")

    async def test_cancellation(self):
        async def slow():
            await asyncio.sleep(20)

        sdk = SDKClient(SimpleNamespace(async_get_device_list=slow), interval=0)
        task = asyncio.create_task(sdk.discover())
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_discovery_no_device_diagnostic(self):
        args = parser().parse_args(["--simulate", "discover"])
        result = await run(args)
        self.assertEqual(result["count"], 1)
        self.assertNotIn("synthetic-ac", str(result))

    async def test_live_engine_is_read_only(self):
        e = Engine(SimulationClient(), "synthetic-ac")
        await e.refresh()
        self.assertTrue(e.snapshot.capabilities)
        self.assertTrue(all(not cap.writable for cap in e.snapshot.capabilities.values()))
        self.assertTrue(e.snapshot.capabilities["operation.airConOperationMode"].supported_writable)
        self.assertFalse(
            e.snapshot.capabilities["temperatureInUnits.currentTemperature.C"].supported_writable
        )
        with self.assertRaises(ValueError):
            await e.command("operation.airConOperationMode", "POWER_ON")

    async def test_device_index_selected_without_publishing_id(self):
        e = Engine(SimulationClient(), None, device_index=0)
        await e.refresh()
        self.assertEqual(e.snapshot.connection, "connected")
        self.assertNotIn("synthetic-ac", str(e.snapshot.to_dict()))

    async def test_http_auth_code(self):
        async def fail():
            error = RuntimeError("sensitive")
            error.status = 401
            raise error

        with self.assertRaisesRegex(BackendError, "auth_required"):
            await SDKClient(SimpleNamespace(async_get_device_list=fail), interval=0).discover()

    async def test_vault_failure_requires_intervention(self):
        class Locked(SimulationClient):
            async def profile(self, device):
                raise CredentialError("Locked")

        e = Engine(Locked(), "synthetic-ac")
        await e.refresh()
        self.assertEqual(e.snapshot.connection, "auth_required")
        self.assertEqual(e.snapshot.error, "credential_required")


class ModelTests(unittest.TestCase):
    def test_absent_capabilities_never_invented(self):
        self.assertEqual(capabilities({}), {})
        with self.assertRaises(ValueError):
            Capability(("missing",), writable=True).validate(24)

    def test_unit_enum_becomes_string_in_keys_and_capability(self):
        profile = {
            "property": {
                "temperature": {
                    "unit": {"type": "enum", "mode": ["r"], "value": {"r": ["C"]}},
                    "targetTemperature": {
                        "type": "range",
                        "mode": ["r", "w"],
                        "value": {"w": {"min": 18, "max": 30, "step": 0.5}},
                    },
                }
            }
        }
        caps = capabilities(profile)
        self.assertEqual(list(caps), ["temperature.targetTemperature.C"])
        cap = caps["temperature.targetTemperature.C"]
        self.assertEqual(cap.unit, "C")
        self.assertEqual((cap.minimum, cap.maximum, cap.step), (18, 30, 0.5))
        cap.validate(24.5)
        with self.assertRaises(ValueError):
            cap.validate(24.25)

    def test_unknown_or_ambiguous_unit_never_stringifies_metadata(self):
        for raw in (
            {"type": "enum", "mode": ["r"], "value": {"r": ["C", "F"]}},
            {"type": "enum", "mode": ["r"], "value": None},
            3,
            None,
        ):
            caps = capabilities(
                {
                    "property": {
                        "temperature": {
                            "unit": raw,
                            "currentTemperature": {"mode": ["r"], "type": "range"},
                        }
                    }
                }
            )
            self.assertEqual(list(caps), ["temperature.currentTemperature"])
            self.assertIsNone(caps["temperature.currentTemperature"].unit)

    def test_temperature_units_keep_separate_domains(self):
        caps = capabilities(
            {
                "property": {
                    "temperatureInUnits": [
                        {
                            "unit": unit,
                            "targetTemperature": {
                                "mode": ["r", "w"],
                                "type": "range",
                                "value": {"w": {"min": minimum, "max": maximum, "step": step}},
                            },
                        }
                        for unit, minimum, maximum, step in [("C", 18, 30, 0.5), ("F", 64, 86, 1)]
                    ]
                }
            }
        )
        self.assertEqual(caps["temperatureInUnits.targetTemperature.C"].unit, "C")
        self.assertEqual(caps["temperatureInUnits.targetTemperature.F"].step, 1)

    def test_nonfinite_and_boolean_rejected(self):
        c = Capability(("x",), True, minimum=18, maximum=30, step=1)
        for v in [float("nan"), float("inf"), True, "24"]:
            with self.assertRaises(ValueError):
                c.validate(v)

    def test_profile_excluded_values(self):
        cap = Capability(("x",), True, minimum=18, maximum=30, step=1, excluded=[25])
        with self.assertRaises(ValueError):
            cap.validate(25)
        cap.validate(24)

    def test_credential_entry_requires_terminal(self):
        from unittest.mock import patch

        vault = Vault.__new__(Vault)
        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(CredentialError, "private interactive terminal"):
                vault.store_interactive("default")

    def test_homelab_credential_uses_separate_namespace(self):
        from unittest.mock import patch

        calls = []

        class Backend:
            __module__ = "keyring.backends.SecretService"

            def set_password(self, *args):
                calls.append(args)

        vault = Vault(Backend(), service="lgthinq-homelab-api")
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("getpass.getpass", return_value="synthetic-homelab-key-00000000000001") as prompt,
        ):
            vault.store_interactive("desktop")
        self.assertIn("Homelab API key", prompt.call_args.args[0])
        self.assertEqual(calls[0][:2], ("lgthinq-homelab-api", "desktop"))

    def test_plaintext_keyring_rejected(self):
        with self.assertRaises(CredentialError):
            Vault(SimpleNamespace())


if __name__ == "__main__":
    unittest.main()

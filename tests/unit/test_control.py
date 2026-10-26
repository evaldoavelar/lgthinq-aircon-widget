"""Control opt-in and actual SDK boundary; all devices and responses synthetic."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from lgthinq_daemon.cli import operate, parser
from lgthinq_daemon.client import SDKClient, SimulationClient
from lgthinq_daemon.config import configure, resolve, validate
from lgthinq_daemon.container_server import ContainerClient
from lgthinq_daemon.engine import Engine
from lgthinq_daemon.live import LiveClient


class ControlTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_control_reaches_sdk_and_confirms_readback(self):
        simulation = SimulationClient()
        calls = []

        async def post(device, payload):
            calls.append((device, payload))
            await simulation.control(device, payload)
            return {}

        sdk = SDKClient(
            SimpleNamespace(
                async_get_device_profile=simulation.profile,
                async_get_device_status=simulation.status,
                async_post_device_control=post,
            ),
            allow_control=True,
            interval=0,
        )
        engine = Engine(sdk, "synthetic-ac", allow_control=True)
        await engine.refresh()
        for key, value, payload in [
            (
                "operation.airConOperationMode",
                "POWER_ON",
                {"operation": {"airConOperationMode": "POWER_ON"}},
            ),
            (
                "temperatureInUnits.targetTemperature.C",
                25,
                {"temperatureInUnits": {"targetTemperature": 25, "unit": "C"}},
            ),
            ("airConJobMode.currentJobMode", "FAN", {"airConJobMode": {"currentJobMode": "FAN"}}),
            ("airFlow.windStrength", "HIGH", {"airFlow": {"windStrength": "HIGH"}}),
            ("powerSave.powerSaveEnabled", True, {"powerSave": {"powerSaveEnabled": True}}),
            ("windDirection.rotateUpDown", False, {"windDirection": {"rotateUpDown": False}}),
        ]:
            await engine.command(key, value)
            self.assertEqual(calls[-1], ("synthetic-ac", payload))
            self.assertEqual(engine.snapshot.connection, "connected")
            self.assertIsNone(engine.snapshot.error)
        self.assertFalse(engine.snapshot.simulated)
        self.assertEqual(engine.snapshot.state["operation"]["airConOperationMode"], "POWER_ON")
        self.assertEqual(engine.snapshot.state["temperatureInUnits"][0]["targetTemperature"], 25)
        self.assertFalse(
            engine.snapshot.capabilities["temperatureInUnits.currentTemperature.C"].writable
        )
        with self.assertRaises(ValueError):
            await engine.command("temperatureInUnits.targetTemperature.C", 31)
        self.assertEqual(len(calls), 6)

    async def test_legacy_temperature_unit_payload(self):
        class Legacy(SimulationClient):
            async def profile(self, device):
                return {
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

        client = Legacy()
        client.control = AsyncMock()
        engine = Engine(client, "synthetic", allow_control=True)
        await engine.refresh()
        await engine.command("temperature.targetTemperature.C", 24.5)
        client.control.assert_awaited_once_with(
            "synthetic", {"temperature": {"targetTemperature": 24.5, "unit": "C"}}
        )

    async def test_live_and_container_opt_in_dispatch_without_secrets(self):
        adapter = SimpleNamespace(control=AsyncMock())
        live = LiveClient(
            account="synthetic", country="BR", client_id="synthetic", allow_control=True
        )
        live.adapter = adapter
        container = ContainerClient({"allow_control": True})
        container._sdk = adapter
        for client in (live, container):
            await client.control("synthetic", {"operation": {"airConOperationMode": "POWER_ON"}})
        self.assertEqual(adapter.control.await_count, 2)
        self.assertIsNone(live.session)
        self.assertIsNone(container._session)

    async def test_cli_opt_in_propagates_to_engine(self):
        args = parser().parse_args(
            [
                "--allow-control",
                "--device-index",
                "0",
                "command",
                "operation.airConOperationMode",
                '"POWER_ON"',
            ]
        )
        result = await operate(SimulationClient(), args)
        self.assertFalse(result["simulated"])
        self.assertEqual(result["state"]["operation"]["airConOperationMode"], "POWER_ON")

    async def test_opt_in_survives_polling_and_failed_write(self):
        client = SimulationClient()
        engine = Engine(client, "synthetic", allow_control=True)
        await engine.refresh()
        client.control = AsyncMock(side_effect=OSError())
        await engine.command("operation.airConOperationMode", "POWER_ON")
        self.assertEqual(engine.snapshot.state["operation"]["airConOperationMode"], "POWER_OFF")
        self.assertEqual(engine.snapshot.connection, "error")
        await engine.refresh()
        self.assertTrue(engine.snapshot.capabilities["operation.airConOperationMode"].writable)


class ControlConfigTests(unittest.TestCase):
    def test_default_explicit_enable_and_cli_disable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            self.assertFalse(configure(path, {})["allow_control"])
            enabled = configure(path, {"allow_control": True})
            args, _ = resolve(parser().parse_args(["--config", str(path), "serve"]))
            self.assertTrue(args.allow_control)
            args, _ = resolve(
                parser().parse_args(["--config", str(path), "--no-allow-control", "serve"])
            )
            self.assertFalse(args.allow_control)
            for invalid in (1, "true", None):
                with self.assertRaisesRegex(ValueError, "boolean"):
                    validate({**enabled, "allow_control": invalid})

    def test_service_creation_propagates_opt_in(self):
        from lgthinq_daemon.cli import main

        with (
            TemporaryDirectory() as directory,
            patch("lgthinq_daemon.dbus_service.serve") as serve,
            patch(
                "sys.argv",
                [
                    "lgthinq",
                    "--config",
                    str(Path(directory) / "settings.json"),
                    "--allow-control",
                    "serve",
                ],
            ),
        ):
            configure(Path(directory) / "settings.json", {"device_index": 0})
            self.assertEqual(main(), 0)
            engine = serve.call_args.args[0]
            self.assertTrue(engine.allow_control)
            self.assertTrue(engine.client.allow_control)
            self.assertIsNone(engine.client.session)


class AutomaticRefreshTests(unittest.IsolatedAsyncioTestCase):
    async def test_monitor_updates_external_changes_without_manual_refresh(self):
        import asyncio

        client = SimulationClient()
        client.profile = AsyncMock(wraps=client.profile)
        client.status = AsyncMock(wraps=client.status)
        engine = Engine(client, "synthetic", simulated=True)
        stop = asyncio.Event()
        task = asyncio.create_task(engine.monitor(stop, interval=0.01))
        try:

            async def wait_for_temperature(expected):
                while (
                    engine.snapshot.state.get("temperatureInUnits", [{}])[0].get(
                        "targetTemperature"
                    )
                    != expected
                ):
                    await asyncio.sleep(0.001)

            await asyncio.wait_for(wait_for_temperature(24), timeout=1)
            client.state["temperatureInUnits"][0]["targetTemperature"] = 27
            await asyncio.wait_for(wait_for_temperature(27), timeout=1)
            self.assertGreaterEqual(client.status.await_count, 2)
            client.profile.assert_awaited_once()
        finally:
            stop.set()
            await task

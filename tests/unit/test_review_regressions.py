"""R03/R04/R07 regressions: synthetic config, clients, vault and D-Bus adapter."""

import asyncio
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lgthinq_daemon import cli, dbus_service
from lgthinq_daemon.client import SimulationClient
from lgthinq_daemon.config import configure, load, resolve
from lgthinq_daemon.local import LocalController
from lgthinq_daemon.models import Capability, Snapshot


class Client(SimulationClient):
    calls = []

    def __init__(self, **kwargs):
        super().__init__()
        self.calls.append(kwargs)

    async def discover(self):
        return [
            {"deviceId": name, "deviceInfo": {"deviceType": "DEVICE_AIR_CONDITIONER"}}
            for name in ("synthetic-A", "synthetic-B")
        ]

    async def close(self):
        pass


class ReviewCLI(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "config.json"
        configure(self.path, {"device_id": "synthetic-A", "allow_control": True})
        Client.calls = []

    def invoke(self, options, action):
        self.captured = []
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["lgthinq", "--config", str(self.path), *options, action]),
            patch.object(dbus_service, "serve", side_effect=self.captured.append),
            contextlib.redirect_stdout(output),
        ):
            result = cli.main()
        return result, output.getvalue()

    def test_r03_explicit_denial_reaches_client_engine_and_survives_ui(self):
        before = self.path.read_bytes()
        self.assertEqual(self.invoke(["--no-allow-control"], "serve-local")[0], 0)
        local = self.captured[0]
        self.assertFalse(local.config["allow_control"], "R03: explicit denial lost at controller")
        self.assertEqual(self.path.read_bytes(), before)
        local.client_factory = Client

        async def exercise():
            await local.refresh()
            self.assertFalse(Client.calls[-1]["allow_control"])
            self.assertFalse(local.engine.allow_control)
            await local.configure({"allow_control": True}, "")
            self.assertFalse(local.config["allow_control"])
            self.assertFalse(local.engine.allow_control)
            await local.discover()
            self.assertFalse(local.config["allow_control"])
            self.assertFalse(any(c.writable for c in local.snapshot.capabilities.values()))
            self.assertTrue(load(self.path)["allow_control"])
            with self.assertRaisesRegex(ValueError, "disabled"):
                await local.command("operation.airConOperationMode", "POWER_ON")
            await local.close()

        asyncio.run(exercise())

    def test_r03_connection_overrides_are_explicitly_rejected(self):
        for options in (
            ["--device", "synthetic-B"],
            ["--device-index", "1"],
            ["--country", "US"],
            ["--account", "synthetic"],
            ["--client-id", "00000000-0000-0000-0000-000000000001"],
            ["--endpoint", "https://synthetic.example"],
            ["--api-token-account", "default"],
            ["--host", "127.0.0.1"],
            ["--port", "8765"],
            ["--allow-control"],
            ["--tls-cert", "synthetic.pem"],
            ["--tls-key", "synthetic.key"],
        ):
            with self.subTest(options=options):
                code, output = self.invoke(options, "serve-local")
                self.assertEqual(code, 2, "R03: unsupported serve-local option silently accepted")
                self.assertIn("serve-local", json.loads(output)["error"])
                self.assertFalse(self.captured)

    def test_r03_default_preserves_saved_settings_and_fresh_defaults(self):
        configure(self.path, {"country": "US", "account": "synthetic"})
        before = self.path.read_bytes()
        self.assertEqual(self.invoke([], "serve-local")[0], 0)
        local = self.captured[0]
        self.assertEqual(local.config, load(self.path))
        local.client_factory = Client
        asyncio.run(local.refresh())
        self.assertEqual(Client.calls[-1]["account"], "synthetic")
        self.assertEqual(Client.calls[-1]["country"], "US")
        self.assertTrue(local.engine.allow_control)
        self.assertEqual(self.path.read_bytes(), before)
        fresh = LocalController(self.path.parent / "absent.json")
        self.assertFalse(fresh.config["allow_control"])
        self.assertEqual(fresh.config["country"], "BR")
        self.assertEqual(fresh.config["account"], "default")

    def assert_next_selection(self, expected_id, expected_index, selected):
        saved = load(self.path)
        self.assertEqual((saved["device_id"], saved["device_index"]), (expected_id, expected_index))
        args, _ = resolve(cli.parser().parse_args(["--config", str(self.path), "status"]))
        self.assertEqual((args.device, args.device_index), (expected_id, expected_index))
        args.simulate = False
        client = Client()
        original_status = client.status
        observed = []

        async def status(identifier):
            observed.append(identifier)
            return await original_status(identifier)

        client.status = status
        result = asyncio.run(cli.operate(client, args))
        self.assertEqual(result["connection"], "connected")
        self.assertEqual(observed, [selected], "R04: next call selected a stale appliance")

    def test_r04_ui_id_then_cli_index_then_next_call(self):
        local = LocalController(self.path, client_factory=Client)
        local.devices = [{"id": "synthetic-A"}, {"id": "synthetic-B"}]
        asyncio.run(local.configure({"device_id": "synthetic-A"}, ""))
        self.assertEqual(load(self.path)["device_id"], "synthetic-A")
        self.assertEqual(self.invoke(["--device-index", "1"], "configure")[0], 0)
        self.assert_next_selection(None, 1, "synthetic-B")

    def test_r04_ui_id_reconciles_saved_index(self):
        configure(self.path, {"device_index": 0})
        local = LocalController(self.path, client_factory=Client)
        local.devices = [{"id": "synthetic-A"}, {"id": "synthetic-B"}]
        asyncio.run(local.configure({"device_id": "synthetic-B"}, ""))
        self.assertIsNone(local.setup_error)
        self.assert_next_selection("synthetic-B", None, "synthetic-B")

    def test_r04_cli_id_replaces_legacy_index_then_next_call(self):
        configure(self.path, {"device_index": 0})
        self.assertEqual(self.invoke(["--device", "synthetic-B"], "configure")[0], 0)
        self.assert_next_selection("synthetic-B", None, "synthetic-B")

    def test_r04_no_explicit_selection_preserves_configuration(self):
        before = load(self.path)
        self.assertEqual(self.invoke([], "configure")[0], 0)
        self.assertEqual(load(self.path), before)
        self.assert_next_selection("synthetic-A", None, "synthetic-A")

    def test_r04_conflicts_rejected_without_write(self):
        before = self.path.read_bytes()
        for action in ("configure", "status"):
            code, output = self.invoke(["--device", "synthetic-B", "--device-index", "1"], action)
            self.assertEqual(code, 2)
            self.assertIn("either", json.loads(output)["error"])
            self.assertEqual(self.path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "either"):
            configure(self.path, {"device_id": "synthetic-B", "device_index": 1})
        self.assertEqual(self.path.read_bytes(), before)

    def test_r04_legacy_dual_selection_still_prefers_stable_id(self):
        data = load(self.path)
        data["device_index"] = 1
        self.path.write_text(json.dumps(data))
        args, _ = resolve(cli.parser().parse_args(["--config", str(self.path), "status"]))
        self.assertEqual((args.device, args.device_index), ("synthetic-A", None))

    def test_r03_saved_remote_default_and_explicit_denial_use_remote_controller(self):
        configure(self.path, {"endpoint": "https://synthetic.example"})
        for options in ([], ["--no-allow-control"]):
            with self.subTest(options=options):
                self.assertEqual(self.invoke(options, "serve-local")[0], 0)
                local = self.captured[0]
                self.assertEqual(local.config["endpoint"], "https://synthetic.example")
                with patch("lgthinq_daemon.remote.RemoteEngine", Remote):
                    asyncio.run(local.refresh())
                self.assertEqual(local.engine.reads, 1)
                self.assertEqual(local.config["allow_control"], not bool(options))


class Remote:
    def __init__(self, *args, **kwargs):
        self.snapshot = Snapshot(connection="connected")
        self.client = self
        self.reads = self.requests = self.commands = 0

    async def refresh(self):
        self.reads += 1

    async def request_refresh(self):
        self.requests += 1
        await asyncio.sleep(0)
        self.snapshot.connection = "connected"
        self.snapshot.error = None

    async def command(self, *args):
        self.commands += 1

    async def close(self):
        pass


class ReviewRemote(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "config.json"
        configure(self.path, {"endpoint": "https://synthetic.example"})
        self.patch = patch("lgthinq_daemon.remote.RemoteEngine", Remote)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    async def test_r07_integrated_adapter_refresh_and_cached_poll(self):
        import dbus.service
        from gi.repository import GLib

        local = LocalController(self.path)
        # Export-free instance of the real adapter; submit is the async boundary.
        with (
            patch.object(dbus.service.Object, "__init__"),
            patch.object(dbus, "SessionBus"),
            patch.object(dbus.service, "BusName"),
        ):
            adapter = dbus_service.make_adapter(local, None, GLib)
        pending = []
        adapter.submit = lambda coroutine: (pending.append(coroutine), True)[1]
        self.assertTrue(adapter.Refresh())
        await pending.pop()
        self.assertEqual(local.engine.requests, 1, "R07: explicit Refresh only read remote cache")
        self.assertEqual(local.engine.reads, 0, "R07: duplicated remote operation")
        # The poll callback submits engine.refresh, while GetSnapshot is local cache.
        await local.refresh()
        adapter.GetSnapshot()
        self.assertEqual((local.engine.requests, local.engine.reads), (1, 1))
        self.assertTrue(adapter.Refresh())
        await pending.pop()
        self.assertEqual((local.engine.requests, local.engine.reads), (2, 1))
        await local.close()

    async def test_r07_remote_error_snapshot_and_recovery(self):
        local = LocalController(self.path)
        await local.refresh()

        async def unavailable():
            local.engine.snapshot.connection = "error"
            local.engine.snapshot.error = "remote_timeout"

        local.engine.request_refresh = unavailable
        snapshot = await local.request_refresh()
        self.assertEqual(snapshot.error, "remote_timeout")
        self.assertEqual(snapshot.connection, "error")
        local.engine.request_refresh = Remote.request_refresh.__get__(local.engine)
        await local.request_refresh()
        self.assertEqual(local.engine.requests, 1)
        self.assertEqual(local.snapshot.connection, "connected")
        self.assertIsNone(local.snapshot.error)
        with patch.object(
            local.engine, "request_refresh", side_effect=OSError("synthetic failure")
        ):
            snapshot = await local.request_refresh()
        self.assertEqual(snapshot.error, "operational_error")
        await local.request_refresh()
        self.assertIsNone(local.snapshot.error)
        await local.close()

    async def test_r03_remote_denial_blocks_commands_and_writable_capabilities(self):
        local = LocalController(self.path, control_disabled=True)
        await local.refresh()
        local.engine.snapshot.capabilities["synthetic"] = Capability(("synthetic",), writable=True)
        self.assertFalse(local.snapshot.capabilities["synthetic"].writable)
        with self.assertRaisesRegex(ValueError, "disabled"):
            await local.command("synthetic", True)
        self.assertEqual(local.engine.commands, 0)
        await local.close()

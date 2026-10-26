"""Real loopback HTTP with synthetic credentials and appliance only."""

import asyncio
import unittest

from aiohttp.test_utils import TestClient, TestServer

from lgthinq_daemon.client import SimulationClient
from lgthinq_daemon.engine import Engine
from lgthinq_daemon.http_api import create_app, run_server
from lgthinq_daemon.remote import RemoteEngine, validate_url

TOKEN = "synthetic-api-secret-never-used-outside-tests"


class HTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
        await self.engine.refresh()
        self.client = TestClient(
            TestServer(
                create_app(self.engine, TOKEN, min_interval=0, poll_interval=None), host="127.0.0.1"
            )
        )
        await self.client.start_server()
        self.headers = {"Authorization": f"Bearer {TOKEN}"}

    async def asyncTearDown(self):
        await self.client.close()

    async def test_auth_and_no_secret_response(self):
        response = await self.client.get("/healthz")
        self.assertEqual(response.status, 200)
        response = await self.client.get("/v1/snapshot")
        self.assertEqual(response.status, 401)
        self.assertNotIn(TOKEN, await response.text())
        response = await self.client.get("/v1/snapshot", headers=self.headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertTrue((await response.json())["simulated"])

    async def test_remote_roundtrip_and_close(self):
        remote = RemoteEngine(str(self.client.make_url("/")), lambda: TOKEN)
        try:
            await remote.refresh()
            self.assertEqual(remote.snapshot.connection, "connected")
            await remote.command("temperatureInUnits.targetTemperature.C", 25)
            self.assertEqual(
                remote.snapshot.state["temperatureInUnits"][0]["targetTemperature"], 25
            )
            self.assertEqual(remote.snapshot.to_dict(), self.engine.snapshot.to_dict())
        finally:
            await remote.close()
        self.assertIsNone(remote._session)

    async def test_wrong_remote_token(self):
        remote = RemoteEngine(str(self.client.make_url("/")), TOKEN + "wrong")
        try:
            await remote.refresh()
            self.assertEqual(remote.snapshot.error, "remote_auth_required")
        finally:
            await remote.close()

    async def test_invalid_and_readonly_command(self):
        for body in [
            {"key": "missing", "value": 0},
            {"token": "not-accepted"},
            {"key": "temperatureInUnits.targetTemperature.C", "value": 90},
        ]:
            response = await self.client.post("/v1/commands", json=body, headers=self.headers)
            self.assertEqual(response.status, 400)
        cap = self.engine.snapshot.capabilities["temperatureInUnits.targetTemperature.C"]
        cap.writable = False
        response = await self.client.post(
            "/v1/commands",
            json={"key": "temperatureInUnits.targetTemperature.C", "value": 25},
            headers=self.headers,
        )
        self.assertEqual(response.status, 400)

    async def test_busy(self):
        event = asyncio.Event()
        original = self.engine.refresh

        async def slow():
            await event.wait()
            return await original()

        self.engine.refresh = slow
        first = asyncio.create_task(self.client.post("/v1/refresh", headers=self.headers))
        await asyncio.sleep(0.03)
        second = await self.client.post("/v1/refresh", headers=self.headers)
        self.assertEqual(second.status, 409)
        event.set()
        self.assertEqual((await first).status, 200)

    async def test_timeout_and_recovery(self):
        async def slow():
            await asyncio.sleep(20)

        engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
        engine.refresh = slow
        client = TestClient(
            TestServer(
                create_app(engine, TOKEN, timeout=0.01, min_interval=0, poll_interval=None),
                host="127.0.0.1",
            )
        )
        await client.start_server()
        try:
            for _ in range(2):
                response = await client.post("/v1/refresh", headers=self.headers)
                self.assertEqual(response.status, 504)
        finally:
            await client.close()

    async def test_polling_cleanup_and_cached_reads(self):
        class Closing(SimulationClient):
            closed = False
            calls = 0

            async def status(self, device):
                self.calls += 1
                return await super().status(device)

            async def close(self):
                self.closed = True

        source = Closing()
        engine = Engine(source, "synthetic-ac", simulated=True)
        client = TestClient(
            TestServer(create_app(engine, TOKEN, poll_interval=0.02), host="127.0.0.1")
        )
        await client.start_server()
        await asyncio.sleep(0.05)
        for _ in range(3):
            self.assertEqual((await client.get("/v1/snapshot", headers=self.headers)).status, 200)
        self.assertGreater(source.calls, 0)
        await client.close()
        self.assertTrue(source.closed)
        calls = source.calls
        await asyncio.sleep(0.03)
        self.assertEqual(source.calls, calls)

    async def test_rate_limit(self):
        client = TestClient(
            TestServer(
                create_app(self.engine, TOKEN, min_interval=60, poll_interval=None),
                host="127.0.0.1",
            )
        )
        await client.start_server()
        try:
            self.assertEqual((await client.post("/v1/refresh", headers=self.headers)).status, 200)
            self.assertEqual((await client.post("/v1/refresh", headers=self.headers)).status, 429)
        finally:
            await client.close()


class URLTests(unittest.TestCase):
    def test_https_policy(self):
        for url in [
            "http://192.168.1.10:8765",
            "https://user:pass@example.com",
            "https://example.com/?token=x",
            "https://example.com/#x",
            "https://example.com/path",
        ]:
            with self.assertRaises(ValueError):
                validate_url(url)
        self.assertEqual(validate_url("https://192.168.1.10:8765/"), "https://192.168.1.10:8765")
        self.assertEqual(validate_url("http://127.0.0.1:8765"), "http://127.0.0.1:8765")
        with self.assertRaises(ValueError):
            run_server(None, TOKEN, host="0.0.0.0")

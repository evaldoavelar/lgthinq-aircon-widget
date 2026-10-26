"""Run via docker stdin with --network none; synthetic values only."""

import asyncio
import os
import ssl
from unittest.mock import patch

from aiohttp import ClientConnectorCertificateError, ClientSession
from aiohttp.test_utils import TestClient, TestServer

from lgthinq_daemon.client import SimulationClient
from lgthinq_daemon.engine import Engine
from lgthinq_daemon.http_api import create_app


async def main():
    engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
    await engine.refresh()
    token = "synthetic-container-smoke-key-000000000001"
    app = create_app(engine, token, min_interval=0, poll_interval=None)
    async with TestClient(TestServer(app)) as client:
        assert (await client.get("/v1/snapshot")).status == 401
        headers = {"Authorization": "Bearer " + token}
        response = await client.get("/v1/snapshot", headers=headers)
        assert response.status == 200 and (await response.json())["simulated"]
        response = await client.post(
            "/v1/commands",
            headers=headers,
            json={"key": "operation.airConOperationMode", "value": "POWER_ON"},
        )
        assert response.status == 200
        assert (await response.json())["state"]["operation"]["airConOperationMode"] == "POWER_ON"
    print("PASS Docker: unprivileged/read-only, network none, HTTP auth and simulated control")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("/smoke-tls/server.crt", "/smoke-tls/server.key")
    engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
    app = create_app(engine, token, min_interval=0, poll_interval=None)
    server = TestServer(app)
    await server.start_server(ssl=context)
    async with server:
        async with ClientSession() as session:
            url = str(server.make_url("/v1/snapshot"))
            try:
                await session.get(url)
            except ClientConnectorCertificateError:
                pass
            else:
                raise AssertionError("Untrusted TLS certificate was accepted")
            # SSL_CERT_FILE is how the KDE bridge uses the installation-local CA.
            with patch.dict(os.environ, SSL_CERT_FILE="/smoke-tls/server.crt"):
                trusted = ssl.create_default_context()
            async with session.get(url, ssl=trusted) as response:
                assert response.status == 401
            async with session.get(url, ssl=trusted, headers=headers) as response:
                assert response.status == 200 and (await response.json())["simulated"]
    print("PASS Docker TLS: untrusted rejected, trusted authenticated snapshot accepted")


if __name__ == "__main__":
    asyncio.run(main())

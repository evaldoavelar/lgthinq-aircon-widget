"""Process fixture: simulated homelab HTTP server -> real local D-Bus adapter."""

import asyncio
import signal
import threading

from aiohttp import web

from lgthinq_daemon.client import SimulationClient
from lgthinq_daemon.dbus_service import serve
from lgthinq_daemon.engine import Engine
from lgthinq_daemon.http_api import create_app
from lgthinq_daemon.remote import RemoteEngine

TOKEN = "synthetic-integration-key-not-a-real-secret-0001"


def main():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    async def start():
        engine = Engine(SimulationClient(), "synthetic-ac", simulated=True)
        await engine.refresh()
        runner = web.AppRunner(create_app(engine, TOKEN, min_interval=0, poll_interval=None))
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        return runner, site._server.sockets[0].getsockname()[1]

    runner, port = asyncio.run_coroutine_threadsafe(start(), loop).result(timeout=5)
    try:
        serve(RemoteEngine(f"http://127.0.0.1:{port}", TOKEN))
    finally:
        asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result(timeout=5)
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)
        loop.close()
        signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    main()

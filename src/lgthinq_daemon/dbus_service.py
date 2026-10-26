"""GLib session D-Bus adapter; all I/O runs on a dedicated asyncio thread."""

import asyncio
import concurrent.futures
import json
import signal
import threading
import time

SERVICE = "org.lgthinq.LGThinq"
PATH = "/org/lgthinq/LGThinq/AirConditioner"
INTERFACE = "org.lgthinq.LGThinq.AirConditioner1"
SETUP_INTERFACE = "org.lgthinq.LGThinq.Configuration1"


def serve(engine):
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GLib, GLibUnix

    DBusGMainLoop(set_as_default=True)
    loop = asyncio.new_event_loop()
    worker = threading.Thread(target=loop.run_forever, name="lgthinq-io", daemon=True)
    main = GLib.MainLoop()

    adapter = None
    timer = None
    try:
        adapter = make_adapter(engine, loop, GLib)
        worker.start()
        adapter.Refresh()

        def poll():
            if (
                time.monotonic() >= adapter.next_refresh
                and json.loads(adapter.cached)["connection"] != "auth_required"
                and json.loads(adapter.cached).get("error") != "setup_required"
            ):
                adapter.submit(engine.refresh())
            return True

        timer = GLib.timeout_add_seconds(1, poll)
        for sig in (signal.SIGINT, signal.SIGTERM):
            GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, sig, lambda: (main.quit(), False)[1])
        main.run()
    finally:
        if timer:
            GLib.source_remove(timer)
        if adapter:
            try:
                adapter.remove_from_connection()
            except LookupError:
                pass

        async def shutdown():
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            close = getattr(engine.client, "close", None)
            if close:
                await close()

        if worker.is_alive():
            try:
                asyncio.run_coroutine_threadsafe(shutdown(), loop).result(timeout=5)
            except concurrent.futures.TimeoutError:
                pass
            loop.call_soon_threadsafe(loop.stop)
            worker.join(timeout=5)
        if not loop.is_running():
            loop.close()


def make_adapter(engine, loop, GLib):
    """Create the exported object; split out for transport-free introspection tests."""
    import dbus
    import dbus.service

    class Adapter(dbus.service.Object):
        def __init__(self):
            self.bus = dbus.SessionBus()
            self.name = dbus.service.BusName(SERVICE, self.bus, do_not_queue=True)
            super().__init__(self.bus, PATH)
            self.cached = json.dumps(engine.snapshot.to_dict(), allow_nan=False)
            self.cached_settings = json.dumps(
                engine.settings() if hasattr(engine, "settings") else {"unsupported": True}
            )
            self.pending = None
            self.retry_delay = 15
            self.next_refresh = 0.0

        def publish(self, payload):
            self.cached = payload
            data = json.loads(payload)
            if data["connection"] not in {"connecting", "command_pending"}:
                self.retry_delay = (
                    15 if data["connection"] == "connected" else min(900, self.retry_delay * 2)
                )
                self.next_refresh = time.monotonic() + self.retry_delay
            self.SnapshotChanged(self.cached)
            self.cached_settings = json.dumps(
                engine.settings() if hasattr(engine, "settings") else {"unsupported": True}
            )
            self.ConfigurationChanged(self.cached_settings)
            return False

        def submit(self, coroutine):
            if self.pending and not self.pending.done():
                coroutine.close()
                return False

            async def run():
                task = asyncio.create_task(coroutine)
                # Engine sets connecting/command_pending before first awaited I/O.
                await asyncio.sleep(0)
                GLib.idle_add(self.publish, json.dumps(engine.snapshot.to_dict(), allow_nan=False))
                try:
                    await task
                except asyncio.CancelledError:
                    raise
                except Exception:
                    engine.snapshot.connection = "operational_error"
                    engine.snapshot.error = "internal_error"
                finally:
                    GLib.idle_add(
                        self.publish, json.dumps(engine.snapshot.to_dict(), allow_nan=False)
                    )

            self.pending = asyncio.run_coroutine_threadsafe(run(), loop)
            return True

        @dbus.service.method(INTERFACE, in_signature="", out_signature="s")
        def GetSnapshot(self):
            return self.cached

        @dbus.service.method(INTERFACE, in_signature="", out_signature="b")
        def Refresh(self):
            return self.submit(getattr(engine, "request_refresh", engine.refresh)())

        @dbus.service.method(INTERFACE, in_signature="ss", out_signature="b")
        def Command(self, key, value):
            try:
                parsed = json.loads(value)
            except (ValueError, TypeError):
                return False
            return self.submit(engine.command(str(key), parsed))

        @dbus.service.signal(INTERFACE, signature="s")
        def SnapshotChanged(self, snapshot):
            pass

        @dbus.service.method(SETUP_INTERFACE, in_signature="", out_signature="s")
        def GetSettings(self):
            return self.cached_settings

        @dbus.service.method(SETUP_INTERFACE, in_signature="ss", out_signature="b")
        def Configure(self, settings, credential):
            if not hasattr(engine, "settings") or len(settings) > 8192 or len(credential) > 16384:
                return False
            try:
                values = json.loads(settings)
            except (ValueError, TypeError):
                return False
            return self.submit(engine.configure(values, str(credential)))

        @dbus.service.method(SETUP_INTERFACE, in_signature="", out_signature="b")
        def Discover(self):
            if not hasattr(engine, "settings"):
                return False
            return self.submit(engine.discover())

        @dbus.service.signal(SETUP_INTERFACE, signature="s")
        def ConfigurationChanged(self, settings):
            pass

    return Adapter()

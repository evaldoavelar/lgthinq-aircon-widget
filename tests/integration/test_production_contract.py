"""Exported adapter introspection with a fake bus, never IPC or network."""

import json
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

try:
    import dbus.service
    from gi.repository import GLib
except ImportError:
    dbus = None


@unittest.skipIf(dbus is None, "dbus-python/GLib unavailable")
class ProductionContractTest(unittest.TestCase):
    def test_exported_signatures_and_invalid_json(self):
        from lgthinq_daemon.client import SimulationClient
        from lgthinq_daemon.dbus_service import INTERFACE, PATH, make_adapter
        from lgthinq_daemon.engine import Engine

        instances = []
        initialize = dbus.service.Object.__init__

        def capture(obj, *args):
            initialize(obj)
            instances.append(obj)

        class FakeBus:
            def list_exported_child_objects(self, path):
                return []

        class FakeName:
            def __init__(self, *args, **kwargs):
                pass

        with (
            patch.object(dbus, "SessionBus", return_value=FakeBus()),
            patch.object(dbus.service, "BusName", FakeName),
            patch.object(dbus.service.Object, "__init__", capture),
        ):
            adapter = make_adapter(
                Engine(SimulationClient(), "synthetic-ac", simulated=True), None, GLib
            )
            snapshot = json.loads(adapter.GetSnapshot())
            self.assertTrue(snapshot["simulated"])
            self.assertFalse(adapter.Command("key", "invalid-json"))
            xml = dbus.service.Object.Introspect(adapter, PATH, FakeBus())
            interface = ET.fromstring(xml).find(f"interface[@name='{INTERFACE}']")
            self.assertIsNotNone(interface)
            expected = {"GetSnapshot": ("", "s"), "Refresh": ("", "b"), "Command": ("ss", "b")}
            for name, signatures in expected.items():
                args = interface.find(f"method[@name='{name}']").findall("arg")
                actual = tuple(
                    "".join(a.attrib["type"] for a in args if a.attrib["direction"] == direction)
                    for direction in ("in", "out")
                )
                self.assertEqual(actual, signatures)
            signal = interface.find("signal[@name='SnapshotChanged']")
            self.assertEqual(signal.find("arg").attrib["type"], "s")

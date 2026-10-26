"""Local object and introspection checks; these do not prove D-Bus transport."""

import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import dbus.service
except ImportError:
    dbus = None


@unittest.skipIf(dbus is None, "dbus-python unavailable")
class PoCContractTest(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[2] / "poc/phase-0-dbus/service/poc_dbus_service.py"
        spec = importlib.util.spec_from_file_location("poc_service", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.module = module
        self.service = module.AirConditionerService.__new__(module.AirConditionerService)
        dbus.service.Object.__init__(self.service)
        self.service.temperature, self.service.power = 23.0, False
        self.signals = []
        self.service.StateChanged = lambda *values: self.signals.append(values)
        self.service.PropertiesChanged = lambda *values: None

    def test_update_and_rejection(self):
        self.assertTrue(self.service.SetTemperature(25.5))
        self.assertEqual(self.signals[-1], (25.5, False))
        self.assertTrue(self.service.SetPower(True))
        self.assertEqual(self.signals[-1], (25.5, True))
        for bad in (float("nan"), float("inf"), 9, 36):
            self.assertFalse(self.service.SetTemperature(bad))
        self.assertEqual(self.service.GetTemperature(), 25.5)
        self.assertTrue(self.service.GetPower())

    def test_introspection(self):
        class Connection:
            def list_exported_child_objects(self, path):
                return []

        xml = self.service.Introspect(self.module.OBJECT_PATH, Connection())
        interface = ET.fromstring(xml).find(f"interface[@name='{self.module.INTERFACE_NAME}']")
        properties = {p.attrib["name"]: p.attrib["type"] for p in interface.findall("property")}
        self.assertEqual(properties, {"targetTemperature": "d", "power": "b"})
        method = interface.find("method[@name='SetTemperature']")
        self.assertEqual(
            [(a.attrib["type"], a.attrib["direction"]) for a in method.findall("arg")],
            [("d", "in"), ("b", "out")],
        )
        signal = interface.find("signal[@name='StateChanged']")
        self.assertEqual("".join(a.attrib["type"] for a in signal.findall("arg")), "db")
        self.assertEqual(set(self.service.GetAll(self.module.INTERFACE_NAME)), set(properties))


if __name__ == "__main__":
    unittest.main()

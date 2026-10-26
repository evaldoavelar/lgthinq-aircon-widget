#!/usr/bin/env python3
"""Synthetic PoC: dbus-python + GLib, never connects to LG."""

import argparse
import math
import signal

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, GLibUnix

SERVICE_NAME = "org.lgthinq.LGThinq"
OBJECT_PATH = "/org/lgthinq/LGThinq/AirConditioner"
INTERFACE_NAME = "org.lgthinq.LGThinq.AirConditioner"
PROPERTIES = "org.freedesktop.DBus.Properties"


class AirConditionerService(dbus.service.Object):
    def __init__(self, bus):
        self.name = dbus.service.BusName(SERVICE_NAME, bus, do_not_queue=True)
        super().__init__(bus, OBJECT_PATH)
        self.temperature = 23.0
        self.power = False

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="d")
    def GetTemperature(self):
        return self.temperature

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="b")
    def GetPower(self):
        return self.power

    @dbus.service.method(INTERFACE_NAME, in_signature="d", out_signature="b")
    def SetTemperature(self, value):
        if not math.isfinite(value) or not 10 <= value <= 35:
            return False
        self.temperature = float(value)
        self.changed()
        print(f"POC temperature={self.temperature}", flush=True)
        return True

    @dbus.service.method(INTERFACE_NAME, in_signature="b", out_signature="b")
    def SetPower(self, value):
        self.power = bool(value)
        self.changed()
        print(f"POC power={self.power}", flush=True)
        return True

    @dbus.service.signal(INTERFACE_NAME, signature="db")
    def StateChanged(self, temperature, power):
        pass

    @dbus.service.signal(PROPERTIES, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    @dbus.service.method(
        "org.freedesktop.DBus.Introspectable",
        in_signature="",
        out_signature="s",
        path_keyword="object_path",
        connection_keyword="connection",
    )
    def Introspect(self, object_path, connection):
        xml = super().Introspect(object_path, connection)
        marker = f'<interface name="{INTERFACE_NAME}">'
        properties = (
            '<property name="targetTemperature" type="d" access="read"/>'
            '<property name="power" type="b" access="read"/>'
        )
        return xml.replace(marker, marker + properties)

    @dbus.service.method(PROPERTIES, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != INTERFACE_NAME:
            raise dbus.exceptions.DBusException(
                "Unknown interface", name="org.freedesktop.DBus.Error.UnknownInterface"
            )
        return {
            "targetTemperature": dbus.Double(self.temperature),
            "power": dbus.Boolean(self.power),
        }

    @dbus.service.method(PROPERTIES, in_signature="ss", out_signature="v")
    def Get(self, interface, property_name):
        values = self.GetAll(interface)
        if property_name not in values:
            raise dbus.exceptions.DBusException(
                "Unknown property", name="org.freedesktop.DBus.Error.UnknownProperty"
            )
        return values[property_name]

    def changed(self):
        self.StateChanged(self.temperature, self.power)
        self.PropertiesChanged(INTERFACE_NAME, self.GetAll(INTERFACE_NAME), [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo-tick", action="store_true", help="synthetic backend update every 5s"
    )
    args = parser.parse_args()
    DBusGMainLoop(set_as_default=True)
    service = AirConditionerService(dbus.SessionBus())
    loop = GLib.MainLoop()
    if args.demo_tick:

        def tick():
            service.SetTemperature(24 if service.temperature == 23 else 23)
            return True

        GLib.timeout_add_seconds(5, tick)
    for sig in (signal.SIGINT, signal.SIGTERM):
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, sig, lambda: (loop.quit(), False)[1])
    print("POC ready; synthetic state only", flush=True)
    try:
        loop.run()
    finally:
        service.remove_from_connection()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

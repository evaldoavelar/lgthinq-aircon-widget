#!/usr/bin/env python3
"""Real session-bus activation and graphical setup, with synthetic clients only."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = "org.lgthinq.LGThinq"
PATH = "/org/lgthinq/LGThinq/AirConditioner"
SETUP = "org.lgthinq.LGThinq.Configuration1"
CONTROL = "org.lgthinq.LGThinq.AirConditioner1"


def wait_for(read, predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.05)
    raise AssertionError("Synthetic local setup did not reach expected state")


def inside():
    import dbus

    sys.path.insert(0, str(ROOT / "scripts"))
    from qt_tools import RUNNER_ENV, executable

    bus = dbus.SessionBus()
    # Publish registration after the bus starts, as during a real installation.
    activation = Path(os.environ["LOCAL_ACTIVATION_FILE"])
    activation.with_suffix(".pending").replace(activation)
    sys.path.insert(0, str(ROOT / "scripts"))
    from install_local import reload_activation

    reload_activation()
    assert SERVICE in bus.list_activatable_names()
    proxy = bus.get_object(SERVICE, PATH)
    setup = dbus.Interface(proxy, SETUP)
    control = dbus.Interface(proxy, CONTROL)
    assert json.loads(setup.GetSettings())["country"] == "BR"
    assert json.loads(control.GetSnapshot())["error"] == "setup_required"
    assert setup.Configure(json.dumps({"country": "BR", "allow_control": False}), "synthetic-pat")
    state = wait_for(
        lambda: json.loads(control.GetSnapshot()), lambda s: s["connection"] == "connected"
    )
    assert not any(c["writable"] for c in state["capabilities"].values())
    assert "synthetic-pat" not in str(setup.GetSettings())
    assert setup.Configure(json.dumps({"allow_control": True}), "")
    wait_for(
        lambda: json.loads(control.GetSnapshot()),
        lambda s: (
            s["capabilities"].get("temperatureInUnits.targetTemperature.C", {}).get("writable")
        ),
    )
    assert control.Command("temperatureInUnits.targetTemperature.C", "25")
    wait_for(
        lambda: json.loads(control.GetSnapshot()),
        lambda s: s["state"].get("temperatureInUnits", [{}])[0].get("targetTemperature") == 25,
    )
    daemon = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
    pid = int(daemon.GetConnectionUnixProcessID(SERVICE, dbus_interface="org.freedesktop.DBus"))
    os.kill(pid, signal.SIGKILL)
    wait_for(lambda: bus.name_has_owner(SERVICE), lambda owned: not owned)
    # A fresh call activates a new process and reloads stable selection/configuration.
    proxy = bus.get_object(SERVICE, PATH)
    setup = dbus.Interface(proxy, SETUP)
    control = dbus.Interface(proxy, CONTROL)
    assert json.loads(setup.GetSettings())["device_id"] == "synthetic-ac"
    wait_for(lambda: json.loads(control.GetSnapshot()), lambda s: s["connection"] == "connected")
    # A QML harness opens the real configuration component on this private bus.
    (Path(os.environ["XDG_CONFIG_HOME"]) / "multiple").touch()
    assert setup.Discover()
    wait_for(
        lambda: json.loads(setup.GetSettings()), lambda s: len(s["devices"]) == 2 and not s["busy"]
    )
    result = subprocess.run(
        [
            executable(os.environ[RUNNER_ENV]),
            "-platform",
            "offscreen",
            "-input",
            os.environ["LOCAL_QML_TEST"],
            "-o",
            "-,txt",
        ],
        timeout=30,
        check=True,
    )
    assert result.returncode == 0
    pid = int(daemon.GetConnectionUnixProcessID(SERVICE, dbus_interface="org.freedesktop.DBus"))
    os.kill(pid, signal.SIGTERM)
    print(
        "PASS: D-Bus activation, first setup, control opt-in, confirmed synthetic command, "
        "crash/reactivation, QML configuration"
    )


def main():
    if "--inside" in sys.argv:
        inside()
        return
    sys.path.insert(0, str(ROOT / "scripts"))
    from qt_tools import RUNNER_ENV, resolve_runner

    runner_path = resolve_runner()
    (ROOT / "dist").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-activation-", dir=ROOT / "dist") as directory:
        work = Path(directory)
        data = work / "data"
        services = data / "dbus-1/services"
        services.mkdir(parents=True)
        # Only this fixture's activatable services, never the host's catalog.
        bus_config = work / "session.conf"
        bus_config.write_text(
            "<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen>"
            '<auth>EXTERNAL</auth><policy context="default">'
            '<allow own="*"/><allow send_destination="*"/>'
            '<allow receive_sender="*"/></policy>'
            f"<servicedir>{services}</servicedir></busconfig>"
        )
        runner = work / "synthetic_service.py"
        runner.write_text("""
from pathlib import Path
import os
from lgthinq_daemon.local import LocalController
from lgthinq_daemon.client import SimulationClient
from lgthinq_daemon.dbus_service import serve
class Client(SimulationClient):
    def __init__(self, **kwargs): super().__init__()
    async def close(self): pass
    async def discover(self):
        devices = await super().discover()
        if (Path(os.environ['XDG_CONFIG_HOME']) / 'multiple').exists():
            devices.append({'deviceId': 'synthetic-second',
                'deviceInfo': {'deviceType': 'DEVICE_AIR_CONDITIONER'}})
        return devices
class Vault:
    def store(self, account, token): pass
serve(LocalController(Path(os.environ['XDG_CONFIG_HOME']) / 'config.json',
    client_factory=Client, vault_factory=Vault))
""")
        (services / f"{SERVICE}.pending").write_text(
            f'[D-BUS Service]\nName={SERVICE}\nExec="{sys.executable}" "{runner}"\n'
        )
        qml = work / "qml"
        qml.mkdir()
        # QtTest does not install Plasma's translation context. Use the actual
        # Ki18n implementation in the fixture, with the production domain.
        connection = work / "Connection.qml"
        connection.write_text(
            "import org.kde.ki18n\n"
            + (ROOT / "plasmoid/contents/ui/configConnection.qml")
            .read_text()
            .replace(
                "id: page",
                "id: page\n"
                "KI18nContext { id: translations; translationDomain: "
                '"plasma_applet_org.lgthinq.aircon" }\n'
                "function i18n(message, value) { return value === undefined ? "
                "translations.i18n(message) : translations.i18n(message, value) }",
                1,
            )
        )
        (qml / "tst_connection.qml").write_text(
            """
import QtQuick
import QtQuick.Controls
import QtTest
TestCase {
    name: "LocalConnection"
    when: windowShown
    width: 900; height: 800
    Loader { id: page; anchors.fill: parent; source: "SOURCE" }
    function test_setup() {
        tryCompare(page, "status", Loader.Ready)
        tryCompare(page.item, "loaded", true, 10000)
        const field = findChild(page.item, "patField")
        compare(field.echoMode, TextInput.Password)
        field.text = "synthetic-qml-pat"
        const devices = findChild(page.item, "deviceSelector")
        compare(devices.count, 2)
        verify(devices.enabled)
        devices.currentIndex = 1
        devices.activated(1)
        const save = findChild(page.item, "saveConnection")
        tryCompare(save, "enabled", true, 10000)
        save.clicked()
        compare(field.text, "")
        tryCompare(page.item, "working", false, 10000)
        compare(page.item.settings.device_id, "synthetic-second")
        verify(JSON.stringify(page.item.settings).indexOf("synthetic-qml-pat") < 0)
        page.item.acceptSettings(JSON.stringify({country: "BR", devices: []}))
        verify(!devices.enabled)
        verify(devices.displayText.indexOf("Buscar aparelhos") >= 0)
        page.item.reachable = false
        compare(devices.displayText, "Aguardando componente local")
        verify(!save.enabled)
    }
}
""".replace("SOURCE", str(connection))
        )
        env = dict(
            os.environ,
            XDG_DATA_HOME=str(data),
            XDG_CONFIG_HOME=str(work / "config"),
            XDG_CACHE_HOME=str(work / "cache"),
            XDG_STATE_HOME=str(work / "state"),
            PYTHONPATH=str(ROOT / "src"),
            LOCAL_QML_TEST=str(qml),
            LOCAL_ACTIVATION_FILE=str(services / f"{SERVICE}.service"),
            QT_QUICK_BACKEND="software",
            PYTHONDONTWRITEBYTECODE="1",
        )
        env[RUNNER_ENV] = runner_path
        # Prevent inheriting the host's actual connection/keyring overrides.
        env.pop("PYTHON_KEYRING_BACKEND", None)
        subprocess.run(
            [
                "dbus-run-session",
                f"--config-file={bus_config}",
                "--",
                sys.executable,
                str(Path(__file__).resolve()),
                "--inside",
            ],
            env=env,
            timeout=60,
            check=True,
        )


if __name__ == "__main__":
    main()

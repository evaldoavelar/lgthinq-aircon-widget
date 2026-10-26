#!/usr/bin/env python3
"""Synthetic Plasma integration with private bus, controls, loss and recovery."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = "org.lgthinq.LGThinq"
OBJECT = "/org/lgthinq/LGThinq/AirConditioner"


def wait_for(predicate, viewer=None, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        if viewer is not None and viewer.poll() is not None:
            raise RuntimeError(f"Viewer exited: {viewer.returncode}")
        time.sleep(0.1)
    raise RuntimeError("Timed out waiting for integration evidence")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside-bus", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--offscreen", action="store_true")
    parser.add_argument("--compact-layout", action="store_true", help="Exercise a 360px card")
    parser.add_argument(
        "--check-menu", action="store_true", help="Check menu bounds in the card window"
    )
    parser.add_argument(
        "--panel", action="store_true", help="Validate horizontal-panel compact item and popup"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Test HTTP homelab simulation through D-Bus"
    )
    parser.add_argument(
        "--check-config", action="store_true", help="Open native widget settings in isolated config"
    )
    parser.add_argument(
        "--production", action="store_true", help="Use final widget, simulated backend"
    )
    parser.add_argument(
        "--temperature-edit", action="store_true", help="Check rapid temperature clicks coalesce"
    )
    parser.add_argument("--evidence-dir", type=Path, help="Save only synthetic service/QML logs")
    args = parser.parse_args()
    if not args.inside_bus:
        (ROOT / "dist").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="viewer-bus-", dir=ROOT / "dist") as directory:
            config = Path(directory) / "session.conf"
            # No host service directories: introspection/recovery must never activate
            # the installed backend or a real credential store on this test bus.
            config.write_text(
                "<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen>"
                '<auth>EXTERNAL</auth><policy context="default">'
                '<allow own="*"/><allow send_destination="*"/>'
                '<allow receive_sender="*"/></policy></busconfig>'
            )
            return subprocess.call(
                [
                    "dbus-run-session",
                    f"--config-file={config}",
                    "--",
                    sys.executable,
                    __file__,
                    "--inside-bus",
                    *sys.argv[1:],
                ]
            )
    processes = []
    with tempfile.TemporaryDirectory(prefix="lgthinq-phase0-") as directory, ExitStack() as stack:
        work = Path(directory)
        env = dict(
            os.environ,
            XDG_CONFIG_HOME=str(work / "config"),
            XDG_CACHE_HOME=str(work / "cache"),
            XDG_DATA_HOME=str(work / "data"),
            XDG_STATE_HOME=str(work / "state"),
            PYTHONPATH=str(ROOT / "src"),
            QT_FORCE_STDERR_LOGGING="1",
            QT_LOGGING_TO_CONSOLE="1",
            QT_LOGGING_RULES="default.debug=true",
            QT_ACCESSIBILITY="0",
            QT_NO_XDG_DESKTOP_PORTAL="1",
            PYTHONDONTWRITEBYTECODE="1",
        )
        if args.offscreen:
            env["QT_QPA_PLATFORM"] = "offscreen"
        package = work / "plasmoid"
        source_package = ROOT / ("plasmoid" if args.production else "poc/phase-0-dbus/plasmoid")
        shutil.copytree(source_package, package)
        qml = package / "contents/ui/main.qml"
        source = qml.read_text()
        if args.production:
            source = source.replace(
                "Component.onCompleted: readSnapshot()",
                """Component.onCompleted: {
                    console.log("TEST_CONNECTION_MESSAGES",
                        connectionMessage({error: "network_error"}) ===
                            i18n("Não foi possível acessar a LG. Confira sua conexão."),
                        connectionMessage({error: "device_offline"}) ===
                            i18n("O aparelho está desconectado. Confira sua conexão Wi-Fi."),
                        connectionMessage({error: "unknown_synthetic_error"}) ===
                            i18n("Não foi possível concluir. Atualize o estado e tente novamente."),
                        connectionMessage({connection: "connected"}) === i18n("Conectado"),
                        connectionMessage({connection: "unknown_synthetic_state"}) ===
                            i18n("Estado indisponível"))
                    readSnapshot()
                }""",
                1,
            )
            source = source.replace(
                "snapshot = data",
                'snapshot = data; console.log("TEST_SNAPSHOT", JSON.stringify(data))',
            )
            source = source.replace(
                "onRegisteredChanged: {",
                'onRegisteredChanged: { console.log("TEST_AVAILABLE", registered)',
            )
            source = source.replace(
                "property var keys: []",
                "property var keys: []; property bool testEnumSent: false; "
                "property bool testPlusSent: false; property bool testScreenshotTaken: false",
            )
            # Trigger actual controls in the copied popup; the backend is always synthetic.
            source = source.replace(
                "id: powerButton",
                r"""id: powerButton
                Timer {
                    interval: 1800
                    running: !root.testEnumSent && powerButton.enabled && powerButton.visible
                    repeat: false
                    onTriggered: {
                        root.testEnumSent = true
                        powerButton.clicked()
                        console.log("TEST_POWER_CLICKED")
                    }
                }
""",
            )
            source = source.replace(
                "id: increaseButton",
                r"""id: increaseButton
                Timer {
                    interval: 3500
                    running: !root.testPlusSent && increaseButton.enabled && increaseButton.visible
                    repeat: false
                    onTriggered: {
                        root.testPlusSent = true
                        increaseButton.clicked()
                        console.log("TEST_PLUS_CLICKED")
                    }
                }
""",
            )
            if args.temperature_edit:
                source = source.replace(
                    "function command(key, value, acknowledgment) {",
                    "function command(key, value, acknowledgment) { "
                    'console.log("TEST_COMMAND", key, value)',
                )
                source = source.replace(
                    'console.log("TEST_PLUS_CLICKED")',
                    'console.log("TEST_PLUS_CLICKED"); '
                    "Qt.callLater(() => { increaseButton.clicked(); increaseButton.clicked(); "
                    'console.log("TEST_DRAFT", temperatureEditor.displayValue, '
                    "root.targetTemperature); "
                    'console.log("TEST_PREVIEW_LABEL", selectedTemperatureLabel.text, '
                    "targetSlider.value); popupRoot.grabToImage(result => { "
                    'result.saveToFile("EDITOR_PATH") }) })',
                )
                source = source.replace("EDITOR_PATH", str(work / "editor.png"))
            source = source.replace(
                "id: popupRoot",
                r"""id: popupRoot
                Timer {
                    interval: 2500
                    running: root.available && !root.testScreenshotTaken
                    repeat: false
                    onTriggered: {
                        root.testScreenshotTaken = true
                        console.log("TEST_POPUP_GEOMETRY", popupRoot.width, popupRoot.height,
                                    popupRoot.visible, root.inPanel)
                        popupRoot.grabToImage(result => { result.saveToFile("SCREENSHOT_PATH") })
                        if (root.inPanel) {
                            console.log("TEST_POPUP_BACKGROUND", cardDialog.backgroundHints,
                                        cardDialog.visible)
                            root.compactRepresentationItem.grabToImage(result => {
                                result.saveToFile("COMPACT_PATH")
                            })
                        }
                    }
                }
""".replace("SCREENSHOT_PATH", str(work / "popup.png")).replace(
                    "COMPACT_PATH", str(work / "compact.png")
                ),
            )
            if args.check_config:
                source = source.replace(
                    "id: popupRoot",
                    r"""id: popupRoot
                    Timer {
                        interval: 1000; running: true; repeat: false
                        onTriggered: {
                            Plasmoid.internalAction("configure").trigger()
                            console.log("TEST_CONFIG_OPEN")
                        }
                    }
""",
                )
            if args.check_menu:
                # Exercise the extra notice shown by a real read-only connection.
                source = source.replace(
                    "root.available && root.keys.length > 0 && !root.snapshot.simulated\n"
                    "                            && !root.controlsAllowed",
                    "true",
                )
                if args.compact_layout:
                    source = source.replace(
                        "Math.max(240, Screen.desktopAvailableHeight - 80)", "360"
                    )
                source = source.replace(
                    "id: popupRoot",
                    """id: popupRoot
                    Timer {
                        interval: 3200; running: true; repeat: false
                        onTriggered: { settingsButton.clicked(); menuCheck.start() }
                    }
                    Timer {
                        id: menuCheck
                        interval: 250
                        onTriggered: {
                            const content = settingsMenu.contentItem
                            const pos = content.mapToItem(popupRoot, 0, 0)
                            console.log("TEST_MENU_POSITION", pos.x, pos.y,
                                content.width, content.height, popupRoot.width, popupRoot.height,
                                settingsMenu.x, settingsMenu.y)
                            console.log("TEST_MENU_BOUNDS", settingsMenu.visible,
                                settingsMenu.parent === popupRoot
                                    && content.Window.window === popupRoot.Window.window,
                                pos.x >= 0 && pos.y >= 0
                                    && pos.x + content.width <= popupRoot.width
                                    && pos.y + content.height <= popupRoot.height)
                            const bottom = footer.mapToItem(popupRoot, 0, footer.height)
                            console.log("TEST_FOOTER_BOUNDS", bottom.y <= popupRoot.height - 20,
                                contentScroll.y + contentScroll.height <= footer.y - 12,
                                readOnlyNotice.visible)
                            content.parent.grabToImage(result => {
                                result.saveToFile("MENU_PATH")
                            })
                            settingsMenu.close()
                            contentScroll.contentItem.contentY = Math.max(0,
                                contentScroll.contentItem.contentHeight - contentScroll.height)
                            Qt.callLater(() => popupRoot.grabToImage(result => {
                                result.saveToFile("LAYOUT_PATH")
                            }))
                        }
                    }
""".replace("MENU_PATH", str(work / "menu.png")).replace("LAYOUT_PATH", str(work / "layout.png")),
                )
            if args.panel:
                source = source.replace(
                    'call("Refresh", "", [], () => readSnapshot())',
                    'console.log("TEST_REFRESH_ON_OPEN"); '
                    'call("Refresh", "", [], () => readSnapshot())',
                )
                source = source.replace(
                    "id: panelIcon",
                    "id: panelIcon; Component.onCompleted: "
                    'console.log("TEST_PANEL_ICON_READY", width, height, root.Plasmoid.icon)',
                )
                source = source.replace(
                    "id: root",
                    r"""id: root
                    Timer {
                        interval: 800; running: true; repeat: false
                        onTriggered: root.popupOpen = true
                    }
                    Timer {
                        interval: 1100; running: true; repeat: false
                        onTriggered: root.popupOpen = false
                    }
                    Timer {
                        interval: 1400; running: true; repeat: false
                        onTriggered: root.popupOpen = true
                    }
""",
                    1,
                )
            command = (
                [sys.executable, str(ROOT / "tests/integration/run_http_bridge.py")]
                if args.remote
                else [sys.executable, "-m", "lgthinq_daemon", "--simulate", "serve"]
            )
            iface = "org.lgthinq.LGThinq.AirConditioner1"
            required = ("Command", "SnapshotChanged", "GetSnapshot")
        else:
            source = source.replace(
                "    fullRepresentation: Item {",
                r"""
    fullRepresentation: Item {
        Timer {
            interval: 7000; running: true; repeat: false
            onTriggered: { increaseButton.clicked(); console.log("POC_BUTTON_CLICKED") }
        }
""",
            )
            command = [sys.executable, str(ROOT / "poc/phase-0-dbus/service/poc_dbus_service.py")]
            iface = "org.lgthinq.LGThinq.AirConditioner"
            required = ("SetTemperature", "StateChanged", "GetPower")
        qml.write_text(source)
        service_log = stack.enter_context((work / "service.log").open("w+"))
        qml_log = stack.enter_context((work / "qml.log").open("w+"))

        def start_service(tick=False):
            process = subprocess.Popen(
                command + (["--demo-tick"] if tick else []),
                stdout=service_log,
                stderr=subprocess.STDOUT,
                env=env,
            )
            processes.append(process)
            return process

        def logs():
            return (work / "qml.log").read_text()

        def introspect():
            result = subprocess.run(
                [
                    "gdbus",
                    "introspect",
                    "--session",
                    "--dest",
                    SERVICE,
                    "--object-path",
                    OBJECT,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout if result.returncode == 0 else ""

        try:
            service = start_service(tick=not args.production)
            wait_for(lambda: all(name in introspect() for name in required))
            viewer = subprocess.Popen(
                ["plasmoidviewer", "-a", str(package)]
                + (["-f", "horizontal", "-l", "topedge", "-s", "480x60"] if args.panel else []),
                stdout=qml_log,
                stderr=subprocess.STDOUT,
                env=env,
            )
            processes.append(viewer)
            if args.production:
                wait_for(
                    lambda: (
                        "TEST_PLUS_CLICKED" in logs()
                        and (
                            '"targetTemperature":27'
                            if args.temperature_edit
                            else '"targetTemperature":25'
                        )
                        in logs()
                        and '"airConOperationMode":"POWER_ON"' in logs()
                    ),
                    viewer,
                )
            else:
                wait_for(
                    lambda: (
                        "StateChanged recebido: 24" in logs()
                        and "POC_BUTTON_CLICKED" in logs()
                        and "StateChanged recebido: 25" in logs()
                    ),
                    viewer,
                )
                assert "POC temperature=25" in (work / "service.log").read_text()
            checkpoint = len(logs())
            service.terminate()
            service.wait(timeout=5)
            missing = "TEST_AVAILABLE false" if args.production else "POC_SERVICE_AVAILABLE false"
            wait_for(lambda: missing in logs()[checkpoint:], viewer)
            checkpoint = len(logs())
            service = start_service()
            restored = '"targetTemperature":24' if args.production else "POC_INITIAL_TEMPERATURE 23"
            wait_for(lambda: restored in logs()[checkpoint:], viewer)
            assert viewer.poll() is None
            if args.temperature_edit:
                assert "TEST_DRAFT 27 24" in logs(), (
                    "Preview must update without changing confirmed state"
                )
                assert "TEST_PREVIEW_LABEL 27 27" in logs(), (
                    "Label and slider must show the selection"
                )
                temperatures = [
                    line
                    for line in logs().splitlines()
                    if "TEST_COMMAND temperatureInUnits.targetTemperature.C" in line
                ]
                assert len(temperatures) == 1 and temperatures[0].endswith(" 27"), temperatures
            if args.check_config:
                assert "TEST_CONFIG_OPEN" in logs(), "Settings action did not fire"
            if args.production:
                assert "TEST_CONNECTION_MESSAGES true true true true true" in logs(), (
                    "Connection messages must translate known errors and use a safe fallback"
                )
            if args.check_menu:
                assert "TEST_MENU_BOUNDS true true true" in logs(), "Menu must fit inside the card"
                assert "TEST_FOOTER_BOUNDS true true true" in logs(), "Footer/notice must fit"
            own_errors = [
                line
                for line in logs().splitlines()
                if "/plasmoid/contents/" in line
                and any(word in line for word in ("TypeError", "ReferenceError", "is not a type"))
            ]
            if args.panel:
                icon_lines = [
                    line for line in logs().splitlines() if "TEST_PANEL_ICON_READY" in line
                ]
                assert icon_lines and all("file://" not in line for line in icon_lines), (
                    "Icon must use a filesystem path"
                )

                assert "TEST_POPUP_BACKGROUND 0 true" in logs(), "Dialog must use NoBackground"
                assert logs().count("TEST_REFRESH_ON_OPEN") >= 2, (
                    "Each popup opening must request Refresh, including a recent cache"
                )
                assert any(
                    "TEST_POPUP_GEOMETRY" in line and line.endswith("true true")
                    for line in logs().splitlines()
                ), "Panel popup did not become visible"
            assert not own_errors, "Project QML errors: " + "\n".join(own_errors)
            print(
                f"PASS: {iface}; introspection, Python→QML, actual control handlers→Python→QML, "
                "service loss/recovery; synthetic only"
            )
        except (AssertionError, RuntimeError, subprocess.SubprocessError) as error:
            print(f"FAIL: {error}", file=sys.stderr)
            for name in ("service.log", "qml.log"):
                print((work / name).read_text(), file=sys.stderr)
            return 1
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            if args.evidence_dir:
                args.evidence_dir.mkdir(parents=True, exist_ok=True)
                prefix = (
                    "panel"
                    if args.panel
                    else "remote"
                    if args.remote
                    else "production"
                    if args.production
                    else "phase0"
                )
                for name in ("service.log", "qml.log"):
                    shutil.copyfile(work / name, args.evidence_dir / f"{prefix}-{name}")
                for picture in ("compact.png", "editor.png", "menu.png", "layout.png"):
                    if (work / picture).exists():
                        shutil.copyfile(work / picture, args.evidence_dir / f"{prefix}-{picture}")
                if (work / "popup.png").exists():
                    shutil.copyfile(
                        work / "popup.png",
                        args.evidence_dir
                        / ("panel-popup-preview.png" if args.panel else "popup-preview.png"),
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Synthetic checks; loopback HTTP and temporary package installation, never LG."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from qt_tools import RUNNER_ENV, resolve_runner

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
commands = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests/unit", "-v"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests/integration", "-v"],
    [sys.executable, "-m", "lgthinq_daemon", "--simulate", "discover"],
    [
        sys.executable,
        "-m",
        "lgthinq_daemon",
        "--simulate",
        "command",
        "temperatureInUnits.targetTemperature.C",
        "25",
    ],
]
qmlrunner = resolve_runner()
env[RUNNER_ENV] = qmlrunner
commands.append([qmlrunner, "-platform", "offscreen", "-input", "tests/qml", "-o", "-,txt"])
failed = False
for command in commands:
    result = subprocess.run(command, env=env, check=False)
    failed |= result.returncode != 0
for metadata in [ROOT / "plasmoid/metadata.json", ROOT / "poc/phase-0-dbus/plasmoid/metadata.json"]:
    data = json.loads(metadata.read_text())
    assert data["KPackageStructure"] == "Plasma/Applet"
    assert data["KPlugin"]["Id"]
    assert (metadata.parent / "contents/ui/main.qml").is_file()
    print("Metadata OK:", metadata.relative_to(ROOT))
lint = shutil.which("qmllint6") or "/usr/lib/qt6/bin/qmllint"
if Path(lint).is_file():
    for qml in [
        Path("poc/phase-0-dbus/plasmoid/contents/ui/main.qml"),
        *Path("plasmoid/contents/ui").glob("*.qml"),
        Path("plasmoid/contents/config/config.qml"),
    ]:
        result = subprocess.run([lint, "-I", "/usr/lib/qt6/qml", qml], env=env, check=False)
        failed |= result.returncode != 0
else:
    print("SKIP: qmllint unavailable; visual acceptance not established")
raise SystemExit(int(failed))

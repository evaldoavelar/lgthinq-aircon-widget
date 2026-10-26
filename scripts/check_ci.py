#!/usr/bin/env python3
"""Host-neutral CI entry: synthetic tests, private bus/XDG, local builds; no publish."""

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import unquote

from package_manifest import anchors, validate_archive
from qt_tools import RUNNER_ENV, resolve_runner

ROOT = Path(__file__).resolve().parents[1]


def run(command, env, **kwargs):
    print("CHECK:", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True, timeout=180, **kwargs)


def documents(env):
    files = [ROOT / n for n in ["README.md", "CONTRIBUTING.md", "MANIFEST.md", "po/README.md"]]
    files += [ROOT / "plasmoid/README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    links = blocks = 0
    for path in files:
        text = path.read_text()
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
            target = match[1].strip().strip("<>")
            if ":" in target.split("#")[0]:
                continue
            relative, _, fragment = unquote(target).partition("#")
            destination = (path.parent / relative).resolve() if relative else path
            if not destination.is_file():
                raise ValueError(f"Broken local link in {path.relative_to(ROOT)}: {target}")
            if fragment and destination.suffix == ".md":
                if fragment not in anchors(destination.read_text()):
                    raise ValueError(f"Broken anchor in {path.relative_to(ROOT)}: {target}")
            links += 1
        for block in re.findall(r"^```(?:sh|bash)\s*\n(.*?)^```", text, re.MULTILINE | re.DOTALL):
            # Parse only. Never execute installation, credential or cloud examples.
            subprocess.run(["bash", "-n"], input=block, text=True, env=env, check=True)
            blocks += 1
    print(f"PASS: {links} local links/anchors; {blocks} shell blocks parsed, not executed")


def main():
    missing = [
        name
        for name in ["bash", "dbus-run-session", "kpackagetool6", "systemd-analyze", "openssl"]
        if not shutil.which(name)
    ]
    for name in ["dbus", "gi", "aiohttp", "ruff"]:
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    runner = resolve_runner()
    for name in ["qmllint"]:
        if not (shutil.which(name + "6") or Path(f"/usr/lib/qt6/bin/{name}").is_file()):
            missing.append(name)
    if missing:
        raise SystemExit("Missing CI prerequisites (no auto-install): " + ", ".join(missing))
    (ROOT / "dist").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ci-", dir=ROOT / "dist") as directory:
        work = Path(directory)
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        for kind in ["CONFIG", "DATA", "CACHE", "STATE"]:
            location = work / kind.lower()
            location.mkdir()
            env[f"XDG_{kind}_HOME"] = str(location)
        env["TMPDIR"] = str(work)
        env["QT_QUICK_BACKEND"] = "software"
        env[RUNNER_ENV] = runner
        env.pop("PYTHON_KEYRING_BACKEND", None)
        config = work / "session.conf"
        config.write_text(
            "<busconfig><type>session</type><listen>unix:tmpdir=/tmp</listen>"
            '<auth>EXTERNAL</auth><policy context="default">'
            '<allow own="*"/><allow send_destination="*"/>'
            '<allow receive_sender="*"/></policy></busconfig>'
        )
        private = ["dbus-run-session", f"--config-file={config}", "--"]
        run(
            [sys.executable, "-m", "ruff", "check", "--no-cache", "src", "scripts", "tests", "poc"],
            env,
        )
        run(
            [sys.executable, "-m", "ruff", "format", "--check", "src", "scripts", "tests", "poc"],
            env,
        )
        run([*private, sys.executable, "scripts/check.py"], env)
        run([sys.executable, "scripts/audit_distribution.py", "check-rights"], env)
        documents(env)
        metadata = json.loads((ROOT / "plasmoid/metadata.json").read_text())
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        from lgthinq_daemon import __version__

        assert __version__ == project["version"]
        assert metadata["KPlugin"]["Version"] == project["version"]
        assert metadata["X-Plasma-API-Minimum-Version"] == "6.4"
        run([sys.executable, "tests/integration/local_activation.py"], env)
        run([sys.executable, "scripts/check_i18n.py"], env)
        run([sys.executable, "scripts/catalogs.py", "check"], env)
        run(
            [
                sys.executable,
                "scripts/check_python_packages.py",
                "--output",
                str(work / "python-packages"),
            ],
            env,
        )
        bundle = work / "lgthinq-local.pyz"
        package = work / "package"
        run([sys.executable, "scripts/build_local.py", "--output", str(bundle)], env)
        run(
            [
                sys.executable,
                "scripts/prepare_deploy.py",
                "--output",
                str(package),
                "--python",
                sys.executable,
                "--config",
                str(work / "config.json"),
            ],
            env,
        )
        for artifact, kind in [(bundle, "pyz"), (package / "lgthinq.plasmoid", "plasmoid")]:
            members = validate_archive(artifact, kind)
            print("VERIFIED INVENTORY:", kind, members)
            print("LOCAL BUILD:", artifact.name, hashlib.sha256(artifact.read_bytes()).hexdigest())
        run([sys.executable, str(bundle), "--help"], env, stdout=subprocess.DEVNULL)
        print("PASS: synthetic CI; local build products removed with temporary directory")
        print(
            "PENDING: environmental acceptance, translations, "
            "Docker compliance and Store submission"
        )


if __name__ == "__main__":
    main()

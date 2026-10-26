#!/usr/bin/env python3
"""Offline wheel/sdist inventories and isolated smoke; internal artifacts only."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

from package_manifest import BACKEND, LEGAL, backend_catalogs, source_file

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd, env):
    print("PACKAGE CHECK:", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True, timeout=120)


def verify_wheel(path, version):
    metadata = f"lgthinq_aircon_widget-{version}.dist-info"
    expected = (
        {f"{metadata}/licenses/{name}" for name in LEGAL}
        | {f"lgthinq_daemon/{name}" for name in BACKEND}
        | {p.removeprefix("src/") for p in backend_catalogs()}
        | {
            f"{metadata}/{name}"
            for name in ("METADATA", "WHEEL", "entry_points.txt", "top_level.txt", "RECORD")
        }
    )
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert set(names) == expected, f"Unexpected wheel payload: {set(names) ^ expected}"
        assert archive.testzip() is None
        assert all(not stat.S_ISLNK(entry.external_attr >> 16) for entry in archive.infolist())
        for name in LEGAL:
            assert archive.read(f"{metadata}/licenses/{name}") == (ROOT / name).read_bytes()
        text = archive.read(f"{metadata}/METADATA").decode()
        assert "pacote Python técnico interno" in text
        assert "scripts/build_local.py" not in text
    return sorted(expected)


def check(output, build_python):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in [*[f"src/lgthinq_daemon/{n}" for n in BACKEND], *backend_catalogs()]:
        source_file(ROOT, name)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PIP_NO_INDEX="1")
    env.pop("PYTHONPATH", None)
    run([build_python, "-B", "-c", "import setuptools, wheel"], output, env)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    with tempfile.TemporaryDirectory(prefix="python-packages-") as temporary:
        stage = Path(temporary) / "source"
        stage.mkdir()
        # Copy the real package tree, including unselected resources: exclusion is
        # exercised by setuptools, not simulated by pre-filtering package-data.
        shutil.copytree(
            ROOT / "src", stage / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info")
        )
        for name in ("pyproject.toml", "BACKEND.md", "MANIFEST.in", "README.md", *LEGAL):
            shutil.copyfile(source_file(ROOT, name), stage / name)
        # Synthetic unexpected resources must never become package payload.
        for name in ("locale/zz/LC_MESSAGES/unexpected.mo", "unexpected.txt"):
            path = stage / "src/lgthinq_daemon" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic-unselected-resource")
        for name in ("tests/test_unselected.py", "scripts/unselected.py", "docs/unselected.md"):
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic-unselected-checkout-material")
        run(
            [
                build_python,
                "-B",
                "-c",
                "import setuptools.build_meta as b; "
                f"b.build_wheel({str(output)!r}); b.build_sdist({str(output)!r})",
            ],
            stage,
            env,
        )
        wheel = next(output.glob("*.whl"))
        sdist = next(output.glob("*.tar.gz"))
        inventories = {wheel.name: verify_wheel(wheel, version)}
        prefix = f"lgthinq_aircon_widget-{version}"
        egg = "src/lgthinq_aircon_widget.egg-info"
        expected = (
            {f"src/lgthinq_daemon/{name}" for name in BACKEND}
            | set(backend_catalogs())
            | {
                *LEGAL,
                "pyproject.toml",
                "BACKEND.md",
                "MANIFEST.in",
                "PKG-INFO",
                "setup.cfg",
                *(
                    f"{egg}/{name}"
                    for name in (
                        "PKG-INFO",
                        "SOURCES.txt",
                        "dependency_links.txt",
                        "entry_points.txt",
                        "requires.txt",
                        "top_level.txt",
                    )
                ),
            }
        )
        extracted = Path(temporary) / "extracted"
        with tarfile.open(sdist) as archive:
            members = archive.getmembers()
            files = [m.name.removeprefix(prefix + "/") for m in members if m.isfile()]
            assert len(files) == len(set(files))
            assert set(files) == expected, f"Unexpected sdist payload: {set(files) ^ expected}"
            assert all(m.isfile() or m.isdir() for m in members)
            assert all(m.name == prefix or m.name.startswith(prefix + "/") for m in members)
            assert all(".." not in Path(m.name).parts for m in members)
            for name in LEGAL:
                assert archive.extractfile(f"{prefix}/{name}").read() == (ROOT / name).read_bytes()
            archive.extractall(extracted, filter="data")
        inventories[sdist.name] = sorted(files)
        rebuilt = output / "rebuilt"
        rebuilt.mkdir()
        run(
            [
                build_python,
                "-B",
                "-c",
                f"import setuptools.build_meta as b; b.build_wheel({str(rebuilt)!r})",
            ],
            extracted / prefix,
            env,
        )
        rebuilt_wheel = next(rebuilt.glob("*.whl"))
        inventories["rebuilt/" + rebuilt_wheel.name] = verify_wheel(rebuilt_wheel, version)
        with zipfile.ZipFile(wheel) as first, zipfile.ZipFile(rebuilt_wheel) as second:
            for member in [
                *[f"lgthinq_daemon/{name}" for name in BACKEND],
                *[p.removeprefix("src/") for p in backend_catalogs()],
            ]:
                assert first.read(member) == second.read(member)
                assert first.read(member) == (ROOT / "src" / member).read_bytes()
        installed = Path(temporary) / "installed"
        run(
            [
                build_python,
                "-B",
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--no-index",
                "--target",
                str(installed),
                str(wheel),
            ],
            output,
            env,
        )
        smoke_env = dict(env, PYTHONPATH=str(installed))
        for arguments in (["--help"], ["--simulate", "status"]):
            run([sys.executable, "-B", "-m", "lgthinq_daemon", *arguments], output, smoke_env)
        result = {
            "inventories": inventories,
            "sha256": {
                str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (wheel, sdist, rebuilt_wheel)
            },
            "build_python": build_python,
        }
        (output / "inventory.json").write_text(json.dumps(result, indent=2) + "\n")
        print("PASS: wheel/sdist + rebuilt wheel exact payloads and isolated smoke", flush=True)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--build-python", default=os.environ.get("LGTHINQ_BUILD_PYTHON", sys.executable)
    )
    args = parser.parse_args()
    check(args.output, args.build_python)

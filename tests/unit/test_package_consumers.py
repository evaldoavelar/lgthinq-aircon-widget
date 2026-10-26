"""Required packaging inputs must survive the real installer and Docker staging."""

import fnmatch
import importlib.util
import os
import shlex
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
README = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["readme"]
REQUIRED = ("pyproject.toml", README, "MANIFEST.in", "LICENSE", "LICENSE-DOCS", "NOTICE")


class PackageConsumers(unittest.TestCase):
    def test_installer_preserves_inputs_at_pip_boundary(self):
        spec = importlib.util.spec_from_file_location(
            "consumer_installer", ROOT / "scripts/install_local.py"
        )
        installer_module = importlib.util.module_from_spec(spec)
        with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
            spec.loader.exec_module(installer_module)
        captured = {}

        class StagingCaptured(Exception):
            pass

        def run(arguments, **kwargs):
            if arguments[1:4] == ["-m", "pip", "install"]:
                source = Path(arguments[-1].removesuffix("[thinq]"))
                captured.update({p.name: p.read_bytes() for p in source.iterdir() if p.is_file()})
                raise StagingCaptured
            return subprocess.CompletedProcess(arguments, 0)

        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.dict(
                    os.environ,
                    {"XDG_DATA_HOME": temporary + "/data", "XDG_CONFIG_HOME": temporary + "/cfg"},
                ),
                patch.object(installer_module.Installer, "preflight"),
                patch.object(installer_module, "run", side_effect=run),
            ):
                with self.assertRaises(StagingCaptured):
                    installer_module.Installer().install(ROOT)
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertIn(name, set(captured), "R09: installer lost a required packaging input")
                self.assertEqual(captured[name], (ROOT / name).read_bytes())

    def test_docker_copy_and_context_preserve_required_inputs(self):
        dockerfile = ROOT / "packaging/docker/Dockerfile"
        rules = (ROOT / "packaging/docker/Dockerfile.dockerignore").read_text().splitlines()
        copied = set()
        for line in dockerfile.read_text().splitlines():
            if not line.startswith("COPY "):
                continue
            words = shlex.split(line)
            if words and words[0] == "COPY" and words[-1] == "./":
                copied.update(words[1:-1])
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertIn(name, copied, "R09: Docker COPY lost a required packaging input")
                allowed = True
                # Required inputs are root files; evaluate their ordered ignore rules.
                for rule in rules:
                    if rule and not rule.startswith("#"):
                        if fnmatch.fnmatchcase(name, rule.removeprefix("!")):
                            allowed = rule.startswith("!")
                self.assertTrue(allowed, "R09: Docker context excludes a required packaging input")
                self.assertTrue((ROOT / name).is_file())

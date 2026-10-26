"""Evidence invariants and closed deployment gate, all with synthetic inputs."""

import email.message
import importlib.metadata
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_c1_regressions import script

ROOT = Path(__file__).resolve().parents[2]


class DistributionAuditTests(unittest.TestCase):
    def test_dependency_metadata_records_native_and_missing_not_clearance(self):
        audit = script("audit_distribution")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                '[build-system]\nrequires=[]\n[project]\ndependencies=["example==1"]\n'
                "[project.optional-dependencies]\n"
            )
            (root / "LICENSE").write_text("Synthetic notice, no real license")
            (root / "native.so").write_bytes(b"synthetic, never loaded")
            info = email.message.Message()
            info["License-Expression"] = "MIT"

            class Distribution:
                metadata = info
                version = "1"
                requires = ['conditional>=2; python_version < "3.12"']
                files = [Path("LICENSE"), Path("native.so")]

                def locate_file(self, item):
                    return root / item

            def lookup(name):
                if name == "example":
                    return Distribution()
                raise importlib.metadata.PackageNotFoundError(name)

            result = audit.dependencies(root, lookup)
            rows = {r["name"]: r for r in result["components"]}
            self.assertFalse(rows["conditional"]["installed"])
            self.assertEqual(rows["example"]["evidence"], "partial")
            self.assertEqual(rows["example"]["license_expression"], "MIT")
            self.assertEqual(len(rows["example"]["legal_files"]), 1)
            self.assertEqual(len(rows["example"]["native_files"]), 1)
            self.assertIn("unevaluated", result["scope"])

    def test_homelab_gate_before_tools_prompts_or_secret_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "called"
            for tool in ["python3", "docker", "openssl"]:
                path = root / tool
                path.write_text('#!/bin/sh\ntouch "$SENTINEL"\nexit 99\n')
                path.chmod(0o700)
            for args in [
                [],
                ["--image", "example:latest"],
                ["--show-token"],
                ["--renew-cert"],
                ["--help", "--show-token"],
            ]:
                result = subprocess.run(
                    ["/bin/bash", str(ROOT / "scripts/install_homelab.sh"), *args],
                    env=dict(os.environ, PATH=str(root), SENTINEL=str(sentinel)),
                    input="synthetic-answer\n",
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("suspended", result.stderr)
                self.assertFalse(sentinel.exists())
            help_result = subprocess.run(
                ["/bin/bash", str(ROOT / "scripts/install_homelab.sh"), "--help"],
                env=dict(os.environ, PATH=str(root), SENTINEL=str(sentinel)),
                text=True,
                capture_output=True,
            )
            self.assertEqual(help_result.returncode, 0)
            self.assertFalse(sentinel.exists())

    def test_build_only_uses_mock_docker_and_never_publishes(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            calls = work / "calls"
            docker = work / "docker"
            docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\n')
            docker.chmod(0o700)
            result = subprocess.run(
                ["/bin/bash", str(ROOT / "scripts/publish_image.sh"), "--build-only"],
                env=dict(os.environ, PATH=f"{work}:/usr/bin", CALLS=str(calls)),
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            operations = [line.split()[0] for line in calls.read_text().splitlines()]
            self.assertEqual(operations, ["info", "build", "run"])
            self.assertIn("publication remains suspended", result.stdout)

    def test_rights_coverage_hash_and_explicit_publication_authorization(self):
        audit = script("audit_distribution")
        self.assertGreaterEqual(audit.check_rights(ROOT), 113)
        rows = json.loads((ROOT / "docs/rights-provenance.json").read_text())
        for mutate, expected in [
            (lambda r: r.append(r[0]), "Duplicate"),
            (lambda r: r[0].update(redistribution_authorized=False), "authorization"),
            (lambda r: r[0].update(publication_authorization="unreviewed"), "authorization"),
            (lambda r: r[0].update(reviewed_sha256="0" * 64), "Stale"),
            (lambda r: r.pop(), "coverage"),
        ]:
            changed = json.loads(json.dumps(rows))
            mutate(changed)
            original = Path.read_text

            def read(path, *args, **kwargs):
                if path == ROOT / "docs/rights-provenance.json":
                    return json.dumps(changed)
                return original(path, *args, **kwargs)

            with (
                patch.object(Path, "read_text", read),
                self.assertRaisesRegex(ValueError, expected),
            ):
                audit.check_rights(ROOT)

    def test_real_qml_template_marks_source_without_creating_translations(self):
        catalogs = script("catalogs")
        with tempfile.TemporaryDirectory() as directory:
            template = catalogs.extract(
                ROOT, catalogs.WIDGET_DOMAIN, Path(directory) / "source.pot"
            )
            text = template.read_text()
            self.assertIn('msgid "Temperatura selecionada %1"', text)
            self.assertIn('msgctxt "Feature name and value"', text)
            self.assertIn('msgid "Conexão e credenciais"', text)
            self.assertIn("#, kde-format", text)
            self.assertEqual(len(catalogs.CATALOGS), 4)
            self.assertNotIn("POT-Creation-Date", text)
            self.assertIn('msgid "Aplicando seleção…  Confirmada: %1"', text)
            again = catalogs.extract(ROOT, catalogs.WIDGET_DOMAIN, Path(directory) / "again.pot")
            self.assertEqual(template.read_bytes(), again.read_bytes())
            python_template = catalogs.extract(
                ROOT, catalogs.PYTHON_DOMAIN, Path(directory) / "python.pot"
            )
            self.assertIn(
                'msgid "LG ThinQ AirCon Widget diagnostics and control"',
                python_template.read_text(),
            )

"""Installer lifecycle in temporary XDG directories; no pip/network or host services."""

import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
        spec.loader.exec_module(result)
    return result


class InstallTests(unittest.TestCase):
    def test_old_widget_error_gives_exact_safe_commands_without_removing(self):
        self.installer.widget.mkdir(parents=True)
        with (
            patch.object(os, "getuid", return_value=1000),
            patch.object(shutil, "which", return_value="/bin/true"),
            patch.object(self.module, "run", self.fake_run),
            patch.object(
                sys, "argv", [str(Path(self.temp.name) / "installer with space.pyz"), "install"]
            ),
        ):
            with self.assertRaises(ValueError) as failure:
                self.installer.preflight(removing=True)
            message = str(failure.exception)
            commands = [line.strip() for line in message.splitlines() if line.startswith("  ")]
            self.assertEqual(
                shlex.split(commands[0]),
                [
                    "kpackagetool6",
                    "--type",
                    "Plasma/Applet",
                    "--packageroot",
                    str(self.installer.packages),
                    "--remove",
                    "org.lgthinq.aircon",
                ],
            )
            self.assertEqual(shlex.split(commands[1]), [sys.executable, sys.argv[0], "install"])
            subprocess.run(["bash", "-n"], input="\n".join(commands), text=True, check=True)
            self.assertIn("PAT", message)
            self.assertTrue(self.installer.widget.exists())
            self.assertFalse(any("--remove" in command for command in self.calls))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lgthinq install ")
        self.addCleanup(self.temp.cleanup)
        directory = Path(self.temp.name)
        self.env = patch.dict(
            os.environ,
            {
                "XDG_DATA_HOME": str(directory / "data"),
                "XDG_CONFIG_HOME": str(directory / "config"),
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        self.module = module("install_local")
        self.installer = self.module.Installer()
        self.calls = []
        self.failure = None

    def fake_run(self, arguments, **kwargs):
        self.calls.append(arguments)
        if arguments[:3] == [sys.executable, "-m", "venv"]:
            binary = Path(arguments[-1]) / "bin/python"
            binary.parent.mkdir(parents=True)
            binary.symlink_to(sys.executable)
        if arguments[0] in {"kpackagetool6", "systemd-analyze"}:
            # Exercise the real package lifecycle with an explicit temporary packageroot.
            return subprocess.run(arguments, check=True, capture_output=True, text=True)
        if self.failure and self.failure(arguments):
            self.failure = None  # Rollback itself must be allowed to run.
            raise subprocess.CalledProcessError(1, arguments)
        return subprocess.CompletedProcess(arguments, 0, stdout="")

    @unittest.skipUnless(shutil.which("kpackagetool6"), "KPackage unavailable")
    def test_install_update_remove_preserve_config_and_vault(self):
        config = self.installer.config / "lgthinq-kde/config.json"
        config.parent.mkdir(parents=True)
        config.write_text('{"synthetic": "preserved"}')
        with (
            patch.object(self.installer, "preflight"),
            patch.object(self.module, "run", self.fake_run),
        ):
            self.installer.install(ROOT)
            original = self.installer.current.resolve()
            self.assertTrue(self.installer.widget.exists())
            self.assertIn("serve-local", self.installer.activation.read_text())
            unit = self.installer.unit.read_text()
            command = shlex.split(
                next(
                    line.removeprefix("ExecStart=")
                    for line in unit.splitlines()
                    if line.startswith("ExecStart=")
                )
            )
            self.assertEqual(command[0], str(self.installer.current / "venv/bin/python"))
            self.assertNotIn(str(ROOT / "src"), unit)
            self.assertIn("Type=dbus", self.installer.unit.read_text())
            self.assertIn("StartLimitBurst=3", self.installer.unit.read_text())
            self.assertEqual(
                sum(a[-1] == "org.freedesktop.DBus.ReloadConfig" for a in self.calls), 1
            )
            self.assertFalse((original / "source/.venv-runtime").exists())
            self.installer.install(ROOT)
            self.assertNotEqual(original, self.installer.current.resolve())
            self.installer.remove()
            self.assertFalse(self.installer.root.exists())
            self.assertFalse(self.installer.widget.exists())
            self.assertFalse(self.installer.activation.exists())
            self.assertEqual(config.read_text(), '{"synthetic": "preserved"}')
        self.assertFalse(any("enable" in args for args in self.calls))
        self.assertEqual(sum(a[-1] == "org.freedesktop.DBus.ReloadConfig" for a in self.calls), 3)

    @unittest.skipUnless(shutil.which("kpackagetool6"), "KPackage unavailable")
    def test_failed_update_rolls_back_registration_runtime_and_widget(self):
        with (
            patch.object(self.installer, "preflight"),
            patch.object(self.module, "run", self.fake_run),
        ):
            self.installer.install(ROOT)
            original = self.installer.current.resolve()
            registration = self.installer.unit.read_bytes()
            self.failure = lambda args: args[:3] == ["systemctl", "--user", "daemon-reload"]
            with self.assertRaises(subprocess.CalledProcessError):
                self.installer.install(ROOT)
            self.assertEqual(original, self.installer.current.resolve())
            self.assertEqual(registration, self.installer.unit.read_bytes())
            self.assertTrue(self.installer.widget.exists())

    def test_unknown_files_and_process_owner_are_not_overwritten(self):
        self.installer.unit.parent.mkdir(parents=True)
        self.installer.unit.write_text("unmanaged")
        with (
            patch.object(os, "getuid", return_value=1000),
            patch.object(shutil, "which", return_value="/bin/true"),
            patch.object(self.module, "run", self.fake_run),
        ):
            with self.assertRaisesRegex(ValueError, "não gerenciado"):
                self.installer.preflight(removing=True)
        self.installer.unit.write_text(self.module.MARKER)
        with patch.object(
            self.module, "run", return_value=subprocess.CompletedProcess([], 0, stdout="123")
        ):
            # A matching active unit PID is allowed; absent registration is rejected.
            self.installer.check_owner()
            self.installer.unit.unlink()
            with self.assertRaisesRegex(ValueError, "Backend anterior"):
                self.installer.check_owner()

    def source_fixture(self):
        root = Path(self.temp.name) / "payload"
        selected = [
            "README.md",
            "pyproject.toml",
            "BACKEND.md",
            "MANIFEST.in",
            "LICENSE",
            "LICENSE-DOCS",
            "NOTICE",
        ]
        selected += [f"src/lgthinq_daemon/{n}" for n in self.module.BACKEND]
        selected += self.module.backend_catalogs()
        selected += [
            str(path.relative_to(ROOT)) for path in self.module.sources(ROOT, "plasmoid").values()
        ]
        for name in selected:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        return root

    @unittest.skipUnless(shutil.which("kpackagetool6"), "KPackage unavailable")
    def test_source_install_uses_exact_manifest_and_excludes_sentinels(self):
        payload = self.source_fixture()
        for directory in ["src/lgthinq_daemon", "plasmoid", "plasmoid/contents/ui"]:
            for name in [".env", ".env.local", "private.key", "credentials.json", "surprise.py"]:
                (payload / directory / name).write_text("SYNTHETIC-PRIVATE-SENTINEL")
            (payload / directory / "external").symlink_to(payload / "README.md")
        with (
            patch.object(self.installer, "preflight"),
            patch.object(self.module, "run", self.fake_run),
        ):
            self.installer.install(payload)
        release = self.installer.current.resolve()
        with zipfile.ZipFile(release / "lgthinq.plasmoid") as archive:
            expected = set(self.module.sources(ROOT, "plasmoid"))
            self.assertEqual(set(archive.namelist()), expected)
        self.module.validate_archive(release / "lgthinq.plasmoid", "plasmoid")
        staged = release / "source"
        for path in staged.rglob("*"):
            if path.is_file():
                self.assertNotIn(b"SYNTHETIC-PRIVATE-SENTINEL", path.read_bytes())
                self.assertFalse(path.is_symlink())
        with zipfile.ZipFile(release / "lgthinq.plasmoid") as archive:
            self.assertNotIn(".env", archive.namelist())

    def test_source_install_rejects_selected_symlink_before_mutation(self):
        payload = self.source_fixture()
        path = payload / "src/lgthinq_daemon/local.py"
        path.unlink()
        path.symlink_to(ROOT / "src/lgthinq_daemon/local.py")
        with (
            patch.object(self.installer, "preflight"),
            patch.object(self.module, "run", self.fake_run),
        ):
            with self.assertRaisesRegex(ValueError, "Symlink"):
                self.installer.install(payload)
        self.assertFalse(self.installer.root.exists())
        self.assertEqual(self.calls, [])

    @unittest.skipUnless(shutil.which("kpackagetool6"), "KPackage unavailable")
    def test_source_install_preserves_explicit_backend_catalog(self):
        payload = self.source_fixture()
        relative = "src/lgthinq_daemon/locale/pt_BR/LC_MESSAGES/lgthinq-kde-widget.mo"
        catalog = payload / relative
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_bytes(b"SYNTHETIC-CATALOG-RESOURCE")
        with (
            patch.object(self.installer, "preflight"),
            patch.object(self.module, "run", self.fake_run),
            patch.object(self.module, "backend_catalogs", return_value=[relative]),
        ):
            self.installer.install(payload)
        staged = self.installer.current.resolve() / "source" / relative
        self.assertEqual(staged.read_bytes(), catalog.read_bytes())

    def test_standalone_bundle_excludes_private_build_and_cache_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "dist") as directory:
            path = module("build_local").build(Path(directory) / "installer.pyz")
            with zipfile.ZipFile(path) as bundle:
                names = bundle.namelist()
                self.assertIn("__main__.py", names)
                self.assertIn("payload/src/lgthinq_daemon/local.py", names)
                self.assertFalse(
                    any(
                        ".venv" in n or "__pycache__" in n or n.endswith("config.json")
                        for n in names
                    )
                )
            subprocess.run([sys.executable, str(path), "--help"], check=True, capture_output=True)

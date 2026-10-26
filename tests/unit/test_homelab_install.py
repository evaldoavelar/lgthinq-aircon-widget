"""Exercise the standalone installer without root, Docker, PATs or LG access."""

import contextlib
import io
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lgthinq_daemon.container_server import tls_context

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    (ROOT / "scripts/install_homelab.sh")
    .read_text()
    .split("<<'PYTHON'\n", 1)[1]
    .rsplit("\nPYTHON\n", 1)[0]
)
INSTALL = {"__name__": "installer"}
exec(compile(SOURCE, "install_homelab.sh:python", "exec"), INSTALL)


class InstallerTests(unittest.TestCase):
    def test_host_validation_and_guide_excludes_credentials(self):
        validate = INSTALL["host_name"]
        self.assertEqual(validate("192.168.1.50"), ("192.168.1.50", "IP"))
        self.assertEqual(validate("Homelab.local"), ("homelab.local", "DNS"))
        self.assertEqual(validate("fd00::123"), ("fd00::123", "IP"))
        for value in [
            "",
            "localhost",
            "127.0.0.1",
            "::1",
            "0.0.0.0",
            "::",
            "fe80::1%eth0",
            "999.1.1.1",
            "host/path",
            "host\n",
            "https://host",
            "host;touch x",
        ]:
            with self.subTest(value=value), self.assertRaises(INSTALL["InstallError"]):
                validate(value)
        guide = INSTALL["guide"]("https://192.168.1.50:8765", Path("/opt/lgthinq"))
        self.assertIn("SSL_CERT_FILE", guide)
        self.assertIn("api-credential-set", guide)
        self.assertNotIn("synthetic-private-pat", guide)

    def test_reject_unsafe_paths_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "unexpected").write_text("synthetic")
            with self.assertRaises(INSTALL["InstallError"]):
                INSTALL["check_tree"](root)
            (root / "unexpected").unlink()
            (root / "config.json").symlink_to("/dev/null")
            with self.assertRaises(INSTALL["InstallError"]):
                INSTALL["check_tree"](root)
            with self.assertRaises(INSTALL["InstallError"]):
                INSTALL["installation_directory"](root / "config.json" / "nested")

    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL required for installer TLS test")
    def test_installer_manifest_reexecution_and_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = "localhost/lgthinq@sha256:" + "a" * 64
            calls = []
            actual_run = INSTALL["run"]

            def command(args, capture=False):
                calls.append(args)
                if args[0] == "openssl":
                    return actual_run(args, capture)
                if args[:3] == ["docker", "info", "--format"]:
                    return json.dumps({"OSType": "linux", "Architecture": "x86_64"})
                if args[:3] == ["docker", "image", "inspect"]:
                    return json.dumps([digest])
                return ""

            class Opener:
                def open(self, request, **kwargs):
                    if isinstance(request, str):
                        return io.StringIO('{"status":"ok"}')
                    self_auth = request.get_header("Authorization")
                    assert (
                        self_auth.startswith("Bearer ") and "synthetic-private-pat" not in self_auth
                    )
                    return io.StringIO('{"connection":"connected"}')

            def execute(answers, extra=(), fail=None):
                output = io.StringIO()
                output.isatty = lambda: True
                with contextlib.ExitStack() as stack:
                    stack.enter_context(
                        patch.dict(
                            INSTALL, installation_directory=lambda p: directory, run=fail or command
                        )
                    )
                    stack.enter_context(
                        patch("sys.argv", ["installer", "--directory", str(directory), *extra])
                    )
                    stack.enter_context(patch("os.geteuid", return_value=0))
                    stack.enter_context(patch("os.chown"))
                    stack.enter_context(patch("sys.stdin.isatty", return_value=True))
                    stack.enter_context(patch("sys.stdout.isatty", return_value=True))
                    stack.enter_context(patch("shutil.which", return_value="/synthetic/tool"))
                    stack.enter_context(patch("builtins.input", side_effect=answers))
                    stack.enter_context(
                        patch("getpass.getpass", return_value="synthetic-private-pat")
                    )
                    stack.enter_context(patch("urllib.request.build_opener", return_value=Opener()))
                    stack.enter_context(contextlib.redirect_stdout(output))
                    previous_umask = os.umask(0o077)
                    try:
                        INSTALL["main"]()
                    finally:
                        os.umask(previous_umask)
                return output.getvalue()

            output = execute(["192.168.1.50", "", "", "", "", "s", "n"])
            manifest = json.loads((directory / "compose.yaml").read_text())
            service = manifest["services"]["lgthinq"]
            self.assertEqual(service["image"], digest)
            self.assertEqual(service["restart"], "unless-stopped")
            self.assertEqual(service["command"][0], "--tls-cert")
            self.assertTrue(service["read_only"])
            self.assertEqual(service["ports"], ["8765:8765"])
            settings = json.loads((directory / "config.json").read_text())
            self.assertFalse(settings["allow_control"])
            self.assertEqual((directory / "secrets/lg_pat").stat().st_mode & 0o777, 0o600)
            self.assertEqual((directory / "config.json").stat().st_mode & 0o777, 0o600)
            token = (directory / "secrets/api_token").read_text().strip()
            self.assertGreaterEqual(len(token), 32)
            self.assertNotIn(token, output)
            self.assertNotIn("synthetic-private-pat", output)
            self.assertNotIn(token, (directory / "KDE.txt").read_text())
            self.assertIsInstance(
                tls_context(directory / "tls/server.crt", directory / "tls/server.key"),
                ssl.SSLContext,
            )
            before = {
                name: (directory / name).read_bytes()
                for name in [
                    "config.json",
                    "secrets/lg_pat",
                    "secrets/api_token",
                    "tls/server.crt",
                    "tls/server.key",
                    "ca/ca.crt",
                    "ca/ca.key",
                ]
            }
            execute(["s", "", "", "", "", "", "n"])
            for name, content in before.items():
                self.assertEqual((directory / name).read_bytes(), content, name)
            execute(["n"])  # Reject reconfiguration without touching secrets.
            for name, content in before.items():
                self.assertEqual((directory / name).read_bytes(), content, name)
            with self.assertRaises(INSTALL["InstallError"]):
                execute(["s", "192.168.1.51", "", "", "", ""])
            for stage in ("pull", "up"):

                def failed_command(args, capture=False):
                    if stage in args:
                        raise INSTALL["InstallError"]("synthetic Docker failure")
                    return command(args, capture)

                with self.subTest(stage=stage), self.assertRaises(INSTALL["InstallError"]):
                    execute(["s", "", "", "", "", ""], fail=failed_command)
                for name in ("secrets/lg_pat", "secrets/api_token", "ca/ca.key"):
                    self.assertEqual((directory / name).read_bytes(), before[name])
            shown = execute([], extra=("--show-token",))
            self.assertIn(token, shown)
            self.assertNotIn("synthetic-private-pat", shown)
            execute(["s", "", "", "", "", "", "n"], extra=("--renew-cert",))
            self.assertNotEqual(
                (directory / "tls/server.crt").read_bytes(), before["tls/server.crt"]
            )
            for name in (
                "config.json",
                "secrets/lg_pat",
                "secrets/api_token",
                "ca/ca.key",
                "ca/ca.crt",
            ):
                self.assertEqual((directory / name).read_bytes(), before[name])
            self.assertTrue(any(call[-3:] == ["up", "-d", "--force-recreate"] for call in calls))
            # The same file is accepted by the actual Docker Compose parser; no daemon/network.
            if shutil.which("docker"):
                subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(directory / "compose.yaml"),
                        "config",
                        "--quiet",
                    ],
                    check=True,
                )

    def test_tls_pair_validation(self):
        self.assertIsNone(tls_context(None, None))
        for cert, key in [("missing", None), (None, "missing")]:
            with self.assertRaises(ValueError):
                tls_context(cert, key)
        with self.assertRaises(OSError):
            tls_context("/missing/certificate", "/missing/key")

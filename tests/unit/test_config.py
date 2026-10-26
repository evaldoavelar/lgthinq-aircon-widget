"""Configuration and packaging checks, exclusively in temporary directories."""

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from lgthinq_daemon.cli import parser
from lgthinq_daemon.config import configure, load, resolve, validate


class ConfigTests(unittest.TestCase):
    def test_simulation_never_inherits_live_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            configure(path, {"endpoint": "https://synthetic.example", "allow_control": True})
            args, _ = resolve(parser().parse_args(["--config", str(path), "--simulate", "command"]))
            self.assertIsNone(args.endpoint)
            self.assertIsNone(args.allow_control)
            for arguments in [
                ["--simulate", "--endpoint", "https://synthetic.example", "status"],
                ["--simulate", "serve-local"],
            ]:
                with self.assertRaises(ValueError):
                    resolve(parser().parse_args(arguments))

    def test_uuid_stable_and_no_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "connection.json"
            first = configure(path, {"country": "br", "device_index": 0})
            second = configure(path, {"country": "US"})
            self.assertEqual(first["client_id"], second["client_id"])
            self.assertEqual(load(path)["country"], "US")
            for field in ["token", "pat", "password", "Authorization"]:
                with self.assertRaises(ValueError):
                    validate({**first, field: "synthetic"})

    def test_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "connection.json"
            configure(path, {"country": "BR", "device_index": 2})
            args, _ = resolve(
                parser().parse_args(["--config", str(path), "--country", "US", "status"])
            )
            self.assertEqual(args.country, "US")
            self.assertEqual(args.device_index, 2)
            args, _ = resolve(
                parser().parse_args(["--config", str(path), "--device", "synthetic", "status"])
            )
            self.assertIsNone(args.device_index)

    def test_remote_endpoint_is_persisted_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "connection.json"
            configure(path, {"endpoint": "https://homelab.example"})
            args, _ = resolve(parser().parse_args(["--config", str(path), "serve"]))
            self.assertEqual(args.endpoint, "https://homelab.example")
            with self.assertRaises(ValueError):
                configure(path, {"endpoint": "https://user:secret@example.test"})
            self.assertEqual(load(path)["endpoint"], "https://homelab.example")

    def test_invalid_input_no_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "connection.json"
            for index in [-1, True, "0"]:
                with self.assertRaises(ValueError):
                    configure(path, {"device_index": index})
                self.assertFalse(path.exists())
            path.write_text(json.dumps({"pat": "synthetic"}))
            with self.assertRaises(ValueError):
                load(path)

    def test_stage_only(self):
        script = Path(__file__).resolve().parents[2] / "scripts/prepare_deploy.py"
        spec = importlib.util.spec_from_file_location("prepare_deploy", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            archive = module.prepare(
                directory, Path("/tmp/python with space"), Path("/tmp/settings.json")
            )
            with zipfile.ZipFile(archive) as package:
                self.assertIn("metadata.json", package.namelist())
                self.assertIn("contents/ui/main.qml", package.namelist())
            unit = (Path(directory) / "lgthinq.service").read_text()
            self.assertIn('--config "/tmp/settings.json" serve', unit)
            self.assertIn('ExecStart="/tmp/python with space"', unit)
            self.assertNotIn("LG_PAT=", unit)
            self.assertIn(f"WorkingDirectory={module.ROOT}\n", unit)

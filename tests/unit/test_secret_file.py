"""Explicit file secret boundary, only temporary synthetic data."""

import tempfile
import unittest
from pathlib import Path

from lgthinq_daemon.client import BackendError
from lgthinq_daemon.container_server import ContainerClient, read_secret


class SecretFileTests(unittest.TestCase):
    def test_regular_file_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            path.write_text("synthetic-file-value\n")
            for mode in [0o400, 0o600]:
                path.chmod(mode)
                self.assertEqual(read_secret(path), "synthetic-file-value")
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                read_secret(path)

    def test_reject_symlink_large_empty_nonregular(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "secret"
            path.write_text("synthetic")
            path.chmod(0o600)
            link = root / "link"
            link.symlink_to(path)
            for rejected in [link, root, root / "absent"]:
                with self.assertRaises(ValueError):
                    read_secret(rejected)
            for body in ["", "x" * 16385, "two words", "á"]:
                path.write_text(body)
                with self.assertRaises(ValueError):
                    read_secret(path)


class ContainerClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_control_hard_denied_without_sdk_or_secret(self):
        client = ContainerClient({})
        self.assertIsNone(client._session)
        with self.assertRaisesRegex(BackendError, "not_authorized"):
            await client.control("synthetic", {})
        await client.close()

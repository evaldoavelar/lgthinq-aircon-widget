"""A suspended publication must fail before even invoking Docker."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class PublishGateTests(unittest.TestCase):
    def test_publication_fails_before_docker(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            sentinel = work / "called"
            docker = work / "docker"
            docker.write_text('#!/bin/sh\ntouch "$DOCKER_SENTINEL"\nexit 0\n')
            docker.chmod(0o700)
            for arguments in [[], ["--publish"], ["--build-only", "extra"]]:
                result = subprocess.run(
                    ["/bin/bash", str(root / "scripts/publish_image.sh"), *arguments],
                    env=dict(os.environ, PATH=f"{work}:/usr/bin", DOCKER_SENTINEL=str(sentinel)),
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("suspended", result.stderr)
                self.assertFalse(sentinel.exists())

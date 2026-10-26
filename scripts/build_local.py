#!/usr/bin/env python3
"""Build a standalone installer zipapp; never install or activate anything."""

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path

from package_manifest import sources, validate_archive

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT) and not output.is_relative_to(Path("/tmp")):
        raise ValueError("Output must be inside the workspace or /tmp")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        for member, source in sources(ROOT, "pyz").items():
            destination = stage / member
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        zipapp.create_archive(stage, output, interpreter="/usr/bin/env python3", compressed=True)
    validate_archive(output, "pyz")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/lgthinq-local.pyz")
    print(build(parser.parse_args().output))

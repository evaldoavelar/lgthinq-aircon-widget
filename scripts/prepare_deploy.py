#!/usr/bin/env python3
"""Stage a Plasmoid archive and service units. Never install or enable anything."""

import argparse
import zipfile
from pathlib import Path

from package_manifest import sources, validate_archive

ROOT = Path(__file__).resolve().parents[1]


def systemd_quote(value):
    value = str(value)
    if any(char in value for char in "\n\r\0"):
        raise ValueError("Invalid newline/NUL in path")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'


def prepare(output, python, config):
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT) and not output.is_relative_to(Path("/tmp")):
        raise ValueError("Staging output must be inside the repository or /tmp")
    output.mkdir(parents=True, exist_ok=True)
    replacements = {
        "@PROJECT_DIR@": str(ROOT).replace("%", "%%"),
        "@PYTHON@": systemd_quote(python),
        "@CONFIG@": systemd_quote(config),
        "@PYTHONPATH@": systemd_quote(f"PYTHONPATH={ROOT / 'src'}"),
    }
    for name, arguments in [
        ("lgthinq.service", "--config @CONFIG@ serve"),
        ("lgthinq-simulated.service", "--simulate serve"),
    ]:
        text = (ROOT / "packaging/lgthinq-config.service.in").read_text()
        text = text.replace("@ARGUMENTS@", arguments)
        for key, value in replacements.items():
            text = text.replace(key, value)
        (output / name).write_text(text)
    archive = output / "lgthinq.plasmoid"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for member, path in sources(ROOT, "plasmoid").items():
            package.write(path, member)
    validate_archive(archive, "plasmoid")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/local")
    parser.add_argument("--python", type=Path, default=ROOT / ".venv-runtime/bin/python")
    parser.add_argument(
        "--config", type=Path, default=Path.home() / ".config/lgthinq-kde/config.json"
    )
    args = parser.parse_args()
    print(prepare(args.output, args.python.absolute(), args.config.absolute()))


if __name__ == "__main__":
    main()

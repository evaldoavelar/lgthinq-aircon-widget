"""Resolve Qt tools once and pass absolute paths explicitly to child checks."""

import os
import shutil
import subprocess
from pathlib import Path

RUNNER_ENV = "LGTHINQ_QMLTESTRUNNER"


def executable(path):
    candidate = Path(path).absolute()
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise ValueError(f"Qt runner is not an executable file: {candidate}")
    resolved = str(candidate.resolve())
    try:
        subprocess.run(
            [resolved, "-help"],
            check=True,
            timeout=10,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f"Qt runner is not usable: {resolved}") from error
    return resolved


def resolve_runner(environ=None, defaults=None):
    environ = os.environ if environ is None else environ
    if RUNNER_ENV in environ:
        # An explicit handoff must be valid; never silently pick another runner.
        return executable(environ[RUNNER_ENV])
    # The unversioned PATH name can be Qt 5 (as on the current host).
    # Other Qt 6 layouts can pass their exact executable via RUNNER_ENV.
    found = shutil.which("qmltestrunner6", path=environ.get("PATH", ""))
    if found:
        return executable(found)
    candidates = defaults if defaults is not None else ("/usr/lib/qt6/bin/qmltestrunner",)
    for path in candidates:
        try:
            return executable(path)
        except ValueError:
            continue
    raise ValueError("Missing executable qmltestrunner (PATH or Qt installation)")

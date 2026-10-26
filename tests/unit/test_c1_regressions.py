"""Synthetic C1 sentinels, package extraction and deterministic Qt discovery."""

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
        spec.loader.exec_module(module)
    return module


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="c1-synthetic-", dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "checkout"
        self.root.mkdir()
        self.policy = script("package_manifest")
        # Only explicit source inputs, never the checkout's local configuration.
        required = set(self.policy.inventory("pyz").values())
        required.add("packaging/lgthinq-config.service.in")
        for name in required:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def build(self, kind):
        builder = script("build_local" if kind == "pyz" else "prepare_deploy")
        with patch.object(builder, "ROOT", self.root):
            if kind == "pyz":
                return builder.build(self.work / "local.pyz")
            return builder.prepare(self.work / "deploy", sys.executable, self.work / "config.json")

    def test_unknown_private_files_and_unselected_links_are_excluded(self):
        outside = self.work / "outside.key"
        outside.write_text("SYNTHETIC-PRIVATE-SENTINEL")
        for directory in ["src", "src/lgthinq_daemon", "plasmoid", "plasmoid/contents/ui"]:
            parent = self.root / directory
            for name in [".env", ".env.local", "private.key", "credentials.json", "surprise.py"]:
                (parent / name).write_text("SYNTHETIC-PRIVATE-SENTINEL")
            (parent / "external-link").symlink_to(outside)
            (parent / "directory-link").symlink_to(self.work, target_is_directory=True)
            (parent / "internal-link").symlink_to(parent / ".env")
        for kind in ["pyz", "plasmoid"]:
            with self.subTest(kind=kind):
                artifact = self.build(kind)
                self.policy.validate_archive(artifact, kind)
                with zipfile.ZipFile(artifact) as archive:
                    files = {n for n in archive.namelist() if not n.endswith("/")}
                    self.assertEqual(files, set(self.policy.inventory(kind)))
                    self.assertTrue(
                        all(b"SYNTHETIC-PRIVATE-SENTINEL" not in archive.read(n) for n in files)
                    )
                    self.assertIn(
                        "payload/src/lgthinq_daemon/local.py"
                        if kind == "pyz"
                        else "contents/ui/main.qml",
                        files,
                    )

    def test_selected_file_and_parent_symlinks_fail_including_internal_links(self):
        for kind in ["pyz", "plasmoid"]:
            for internal in [False, True]:
                with self.subTest(kind=kind, internal=internal):
                    path = self.root / "plasmoid/metadata.json"
                    content = path.read_bytes()
                    path.unlink()
                    target = self.root / "metadata-copy" if internal else self.work / "external"
                    target.write_bytes(content)
                    path.symlink_to(target)
                    with self.assertRaisesRegex(ValueError, "Symlink"):
                        self.build(kind)
                    path.unlink()
                    path.write_bytes(content)
        ui = self.root / "plasmoid/contents/ui"
        ui.rename(self.root / "ui-copy")
        ui.symlink_to(self.root / "ui-copy", target_is_directory=True)
        for kind in ["pyz", "plasmoid"]:
            with self.assertRaisesRegex(ValueError, "Symlink"):
                self.build(kind)

    def test_actual_zip_inventory_rejects_injected_member(self):
        for kind in ["pyz", "plasmoid"]:
            artifact = self.build(kind)
            with zipfile.ZipFile(artifact, "a") as archive:
                archive.writestr("private.key", "SYNTHETIC")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                self.policy.validate_archive(artifact, kind)

    def test_broken_package_documentation_reference_fails(self):
        path = self.root / "plasmoid/README.md"
        path.write_text(path.read_text() + "\n[Required guide](../docs/missing.md)\n")
        for kind in ["pyz", "plasmoid"]:
            with self.assertRaisesRegex(ValueError, "Documentation escapes|Unavailable package"):
                self.build(kind)

    def test_package_documentation_anchors_are_checked(self):
        path = self.root / "plasmoid/README.md"
        original = path.read_text()
        for target in ["#missing-section", "README.md#missing-section"]:
            path.write_text(original + f"\n[Broken section]({target})\n")
            for kind in ["pyz", "plasmoid"]:
                with self.subTest(kind=kind, target=target):
                    with self.assertRaisesRegex(ValueError, "Unavailable package anchor"):
                        self.build(kind)
        path.write_text(original + "\n## Synthetic section\n[Valid](#synthetic-section)\n")
        for kind in ["pyz", "plasmoid"]:
            self.policy.validate_archive(self.build(kind), kind)

    def test_required_member_missing_duplicate_symlink_and_special_file_fail(self):
        for kind in ["pyz", "plasmoid"]:
            for mutation in ["missing", "duplicate", "symlink", "fifo"]:
                artifact = self.build(kind)
                with zipfile.ZipFile(artifact) as archive:
                    contents = {
                        n: archive.read(n) for n in archive.namelist() if not n.endswith("/")
                    }
                name = "README.md"
                with zipfile.ZipFile(artifact, "w") as archive:
                    for member, content in contents.items():
                        if member == name and mutation == "missing":
                            continue
                        entry = zipfile.ZipInfo(member)
                        mode = stat.S_IFREG
                        if member == name:
                            mode = {"symlink": stat.S_IFLNK, "fifo": stat.S_IFIFO}.get(
                                mutation, mode
                            )
                        entry.create_system = 3
                        entry.external_attr = (mode | 0o600) << 16
                        archive.writestr(entry, content)
                    if mutation == "duplicate":
                        with self.assertWarns(UserWarning):
                            archive.writestr(name, contents[name])
                with self.subTest(kind=kind, mutation=mutation):
                    with self.assertRaises(ValueError):
                        self.policy.validate_archive(artifact, kind)

    def test_fenced_headings_do_not_create_package_anchors(self):
        path = self.root / "plasmoid/README.md"
        original = path.read_text()
        for fence in ["```sh", "~~~~"]:
            closing = "```" if fence.startswith("`") else "~~~~"
            path.write_text(
                original + f"\n{fence}\n# Ghost section\n{closing}\n[Bad](#ghost-section)\n"
            )
            for kind in ["pyz", "plasmoid"]:
                with self.assertRaisesRegex(ValueError, "Unavailable package anchor"):
                    self.build(kind)
        path.write_text(original + "\n## Actual section ###\n[Good](#actual-section)\n")
        for kind in ["pyz", "plasmoid"]:
            self.policy.validate_archive(self.build(kind), kind)
        self.assertEqual(self.policy.anchors("# A\n# A\n# A-1\n"), {"a", "a-1", "a-1-1"})

    def test_extracted_documentation_is_self_contained_without_checkout(self):
        artifacts = {kind: self.build(kind) for kind in ["pyz", "plasmoid"]}
        # Remove access to even the isolated source tree during extraction/checks.
        self.root.rename(self.work / "unavailable-checkout")
        for kind, artifact in artifacts.items():
            extracted = self.work / f"extracted-{kind}"
            self.policy.validate_archive(artifact, kind)
            with zipfile.ZipFile(artifact) as archive:
                archive.extractall(extracted)
            readme = (extracted / "README.md").read_text()
            self.assertNotIn("/home/", readme)
            self.assertNotIn("$HOME/Documents", readme)
            self.assertIn("Distribuição pública autorizada", readme)
            self.assertIn("GPL-3.0-or-later", readme)
            self.assertIn("CC BY 4.0", readme)
            self.assertIn("KWallet/Secret Service", readme)
            for name in self.policy.LEGAL:
                self.assertEqual((extracted / name).read_bytes(), (ROOT / name).read_bytes())
            if kind == "pyz":
                subprocess.run(
                    [sys.executable, str(artifact), "--help"], check=True, capture_output=True
                )


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.qt = script("qt_tools")
        self.temp = tempfile.TemporaryDirectory(prefix="c1-qt-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def runner(self, name):
        path = self.work / name
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o700)
        return path

    def test_default_path(self):
        runner = self.runner("default")
        self.assertEqual(self.qt.resolve_runner({"PATH": ""}, [runner]), str(runner))

    def test_only_path(self):
        runner = self.runner("qmltestrunner6")
        self.assertEqual(self.qt.resolve_runner({"PATH": str(self.work)}, []), str(runner))

    def test_absent_and_nonexecutable(self):
        with self.assertRaisesRegex(ValueError, "Missing executable"):
            self.qt.resolve_runner({"PATH": ""}, [])
        runner = self.runner("qmltestrunner6")
        runner.chmod(0o600)
        with self.assertRaises(ValueError):
            self.qt.resolve_runner({"PATH": str(self.work)}, [runner])
        for bad in [runner, self.work, self.work / "absent"]:
            with self.assertRaisesRegex(ValueError, "not an executable file"):
                self.qt.resolve_runner({self.qt.RUNNER_ENV: str(bad)}, [])

    def test_executable_with_invalid_format_or_failed_startup(self):
        runner = self.runner("bad-runner")
        for content in ["not an executable format", "#!/bin/sh\nexit 1\n"]:
            runner.write_text(content)
            with self.assertRaisesRegex(ValueError, "not usable"):
                self.qt.resolve_runner({self.qt.RUNNER_ENV: str(runner)}, [])

    def test_explicit_handoff_survives_changed_path_without_fallback(self):
        runner = self.runner("qmltestrunner6")
        resolved = self.qt.resolve_runner({"PATH": str(self.work)}, [])
        env = {"PATH": "", self.qt.RUNNER_ENV: resolved}
        self.assertEqual(self.qt.resolve_runner(env, []), resolved)
        subprocess.run([self.qt.executable(env[self.qt.RUNNER_ENV])], check=True)
        runner.unlink()
        with self.assertRaises(ValueError):
            self.qt.resolve_runner(env, [sys.executable])

    def test_preflight_and_integration_pass_the_resolved_runner_explicitly(self):
        # Exercise both entry points up to child invocation, without host activation.
        ci = script("check_ci")
        integration_spec = importlib.util.spec_from_file_location(
            "activation", ROOT / "tests/integration/local_activation.py"
        )
        activation = importlib.util.module_from_spec(integration_spec)
        integration_spec.loader.exec_module(activation)
        runner = self.runner("qmltestrunner6")
        captured = {}

        def stop_ci(command, env, **kwargs):
            if "tests/integration/local_activation.py" in command:
                captured["ci"] = env[self.qt.RUNNER_ENV]
                raise RuntimeError("child captured")

        def stop_activation(command, **kwargs):
            captured["integration"] = kwargs["env"][self.qt.RUNNER_ENV]
            raise RuntimeError("child captured")

        env = {self.qt.RUNNER_ENV: str(runner)}
        with (
            patch.dict(os.environ, env),
            patch.object(ci, "run", stop_ci),
            patch.object(ci, "documents"),
        ):
            with self.assertRaisesRegex(RuntimeError, "child captured"):
                ci.main()
        with (
            patch.dict(os.environ, env),
            patch.object(sys, "argv", ["activation.py"]),
            patch.object(activation.subprocess, "run", stop_activation),
            patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]),
            patch("qt_tools.resolve_runner", return_value=str(runner)),
        ):
            with self.assertRaisesRegex(RuntimeError, "child captured"):
                activation.main()
        self.assertEqual(captured, {"ci": str(runner), "integration": str(runner)})


class GettextTests(unittest.TestCase):
    def test_real_extraction_merge_and_format_negatives(self):
        # Required toolchain: absence is a failure, never a passing skipped check.
        with tempfile.TemporaryDirectory(prefix="c1-gettext-") as directory:
            script("check_i18n").validate(Path(directory))

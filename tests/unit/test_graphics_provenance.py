"""Review-bound graphics: no legal clearance inferred from payload or rendering."""

import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

import test_c1_regressions as fixtures
from test_c1_regressions import script

ROOT = Path(__file__).resolve().parents[2]


class GraphicsProvenanceTests(unittest.TestCase):
    def test_svg_is_self_contained_geometry_without_visible_lettering(self):
        root = ET.parse(ROOT / "plasmoid/contents/images/lgthinq.svg").getroot()
        allowed = {"svg", "title", "desc", "g", "rect"}
        for item in root.iter():
            self.assertIn(item.tag.rsplit("}", 1)[-1], allowed)
            self.assertFalse(any("href" in a for a in item.attrib))
        self.assertEqual(root.attrib["viewBox"], "0 0 24 24")
        self.assertEqual(len(root.findall(".//{*}rect")), 5)
        text = (ROOT / "plasmoid/contents/ui/AirConditioner.qml").read_text()
        self.assertNotIn("ThinQ", text)
        self.assertNotIn("Canvas", text)
        self.assertNotIn("Text {", text)

    def test_new_geometry_retains_evidence_and_explicit_publication_permission(self):
        rows = json.loads((ROOT / "docs/graphics-provenance.json").read_text())
        for row in rows:
            self.assertTrue(row["redistribution_authorized"])
            self.assertEqual(row["publication_authorization"], "maintainer-2026-10-26")
            self.assertEqual(
                row["reviewed_sha256"],
                hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(),
            )
            self.assertTrue(row["recipe"])
            self.assertIn("Codex", row["creation_process"])
            self.assertIn("not a title certification", row["review_status"])
            self.assertTrue(row["retired_versions"])

    def test_selected_sources_and_zip_bytes_reject_retired_fingerprint(self):
        policy = script("package_manifest")
        synthetic = b"synthetic retired illustration, never a real third-party asset"
        fingerprint = hashlib.sha256(synthetic).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "renamed.svg").write_bytes(synthetic)
            with patch.object(policy, "RETIRED_GRAPHICS_SHA256", {fingerprint}):
                with self.assertRaisesRegex(ValueError, "Retired graphic"):
                    policy.source_file(root, "renamed.svg")
                artifact = root / "candidate.zip"
                with zipfile.ZipFile(artifact, "w") as archive:
                    archive.writestr("renamed.svg", synthetic)
                with patch.object(policy, "inventory", return_value={"renamed.svg": "renamed.svg"}):
                    with self.assertRaisesRegex(ValueError, "Retired graphic"):
                        policy.validate_archive(artifact, "plasmoid")


class GraphicsPackageTests(unittest.TestCase):
    setUp = fixtures.PackageTests.setUp
    build = fixtures.PackageTests.build

    def test_actual_zip_members_exclude_retired_versions_and_contain_candidate_art(self):
        # Inherited fixture copies only declared sources, never preserved originals.
        for kind in ["pyz", "plasmoid"]:
            artifact = self.build(kind)
            with zipfile.ZipFile(artifact) as archive:
                for member in archive.namelist():
                    if not member.endswith("/"):
                        self.assertNotIn(
                            hashlib.sha256(archive.read(member)).hexdigest(),
                            self.policy.RETIRED_GRAPHICS_SHA256,
                        )

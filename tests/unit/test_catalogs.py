"""Exercise extraction from source calls and the actual package catalog mapping."""

import gettext
import subprocess
import unittest
from unittest.mock import patch

import test_c1_regressions as fixtures
from test_c1_regressions import script


class CatalogTests(unittest.TestCase):
    setUp = fixtures.PackageTests.setUp
    build = fixtures.PackageTests.build

    def test_extract_compile_lookup_and_package_without_unselected_catalogs(self):
        catalogs = script("catalogs")
        checker = script("check_i18n")
        qml = self.root / "plasmoid/contents/ui/main.qml"
        qml.write_text('import QtQuick\nQtObject { property string label: i18n("Device %1", 1) }')
        template = catalogs.extract(self.root, catalogs.WIDGET_DOMAIN, self.work / "widget.pot")
        self.assertIn("#, kde-format", template.read_text())
        po = self.work / "draft.po"
        po.write_text(checker.HEADER + '#, kde-format\nmsgid "Device %1"\nmsgstr "Aparelho %1"\n')
        relative = self.policy.catalog_sources(catalogs.WIDGET_DOMAIN, "pt_BR")[0]
        mo = self.root / relative
        catalogs.compile_catalog(po, template, mo)
        with mo.open("rb") as stream:
            self.assertEqual(gettext.GNUTranslations(stream).gettext("Device %1"), "Aparelho %1")
        unselected = self.policy.catalog_sources(catalogs.WIDGET_DOMAIN, "zz")[0]
        self.assertNotIn(unselected, self.policy.inventory("pyz").values())
        with patch.object(self.policy, "CATALOGS", ((catalogs.WIDGET_DOMAIN, "pt_BR"),)):
            # Builders import the shared policy module, so validate its exact selection
            # directly rather than changing the project's language release selection.
            import package_manifest

            with patch.object(package_manifest, "CATALOGS", self.policy.CATALOGS):
                for kind in ["pyz", "plasmoid"]:
                    self.assertIn(relative, self.policy.inventory(kind).values())
                    self.policy.validate_archive(self.build(kind), kind)
        before = mo.read_bytes()
        for translated in ["Aparelho", "Aparelho %2"]:
            po.write_text(checker.HEADER + f'msgid "Device %1"\nmsgstr "{translated}"\n')
            with self.assertRaises((subprocess.CalledProcessError, ValueError)):
                catalogs.compile_catalog(po, template, mo)
            self.assertEqual(mo.read_bytes(), before)

    def test_python_context_plural_and_untranslated_fallback(self):
        catalogs = script("catalogs")
        checker = script("check_i18n")
        (self.root / "src/lgthinq_daemon/cli.py").write_text(
            'pgettext("Status", "Connected")\nngettext("%d device", "%d devices", 2)\n'
            'gettext("Failed {step}").format(step="synthetic")\n'
        )
        template = catalogs.extract(self.root, catalogs.PYTHON_DOMAIN, self.work / "python.pot")
        self.assertIn('msgctxt "Status"', template.read_text())
        self.assertIn('msgid_plural "%d devices"', template.read_text())
        self.assertIn("python-brace-format", template.read_text())
        po = self.work / "draft.po"
        po.write_text(checker.HEADER + 'msgctxt "Status"\nmsgid "Connected"\nmsgstr ""\n')
        output = self.work / "messages.mo"
        catalogs.compile_catalog(po, template, output)
        with output.open("rb") as stream:
            self.assertEqual(
                gettext.GNUTranslations(stream).pgettext("Status", "Connected"), "Connected"
            )
        po.write_text(
            checker.HEADER + 'msgid "%d device"\nmsgid_plural "%d devices"\n'
            'msgstr[0] "%d aparelho"\nmsgstr[1] "aparelhos"\n'
        )
        with self.assertRaises((subprocess.CalledProcessError, ValueError)):
            catalogs.compile_catalog(po, template, output)
        po.write_text(checker.HEADER + 'msgid "Failed {step}"\nmsgstr "Falha"\n')
        with self.assertRaises((subprocess.CalledProcessError, ValueError)):
            catalogs.compile_catalog(po, template, output)
        po.write_text(
            checker.HEADER + '#, fuzzy\nmsgctxt "Status"\nmsgid "Connected"\nmsgstr "Conectado"\n'
        )
        with self.assertRaisesRegex(ValueError, "Fuzzy"):
            catalogs.compile_catalog(po, template, output)
        with patch.object(self.policy, "CATALOGS", ((catalogs.PYTHON_DOMAIN, "pt_BR"),)):
            import package_manifest

            relative = self.policy.backend_catalogs()[0]
            selected = self.root / relative
            selected.parent.mkdir(parents=True, exist_ok=True)
            selected.write_bytes(output.read_bytes())
            with patch.object(package_manifest, "CATALOGS", self.policy.CATALOGS):
                members = self.policy.validate_archive(self.build("pyz"), "pyz")
                self.assertIn(f"payload/{relative}", members)
                self.assertIn(relative.removeprefix("src/lgthinq_daemon/"), members)
        self.assertFalse(any(x["status"] == "approved" for x in catalogs.inventory(self.root)))

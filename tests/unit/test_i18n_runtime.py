"""Actual Python/zipapp and Ki18n loaders with synthetic translations only."""

import gettext
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from test_c1_regressions import script

from lgthinq_daemon.i18n import load_translation

ROOT = Path(__file__).resolve().parents[2]


class TranslationRuntimeTests(unittest.TestCase):
    def test_prepared_catalogs_and_missing_language_fall_back_to_source(self):
        for language in ("en_US", "pt_BR", "zz_ZZ", "C", "../../outside"):
            with self.subTest(language=language):
                translation = load_translation([language])
                self.assertEqual(translation.gettext("Untranslated source"), "Untranslated source")
                self.assertEqual(translation.pgettext("Status", "Connected"), "Connected")
                self.assertEqual(translation.ngettext("one", "many", 2), "many")
        policy = script("package_manifest")
        for domain, language in policy.CATALOGS:
            for name in policy.catalog_sources(domain, language):
                with (ROOT / name).open("rb") as stream:
                    translation = gettext.GNUTranslations(stream)
                self.assertEqual(translation.info()["language"], language)
                self.assertEqual(set(translation._catalog), {""})  # Draft, zero translations.

    def test_python_loader_context_plural_and_language_fallback(self):
        checker = script("check_i18n")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            template = checker.extract(work)
            result, binary = checker.compile_catalog(work, template, checker.CATALOG)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = binary.read_bytes()

            def resource(module, path):
                return data if "/pt_BR/" in path else None

            with patch("lgthinq_daemon.i18n.pkgutil.get_data", resource):
                translation = load_translation(["missing", "pt_BR.UTF-8"])
            self.assertEqual(translation.pgettext("CLI status", "Connected"), "Conectado")
            self.assertEqual(translation.ngettext("%1 device", "%1 devices", 2), "%1 aparelhos")

    def test_standalone_zipapp_loads_selected_catalog_without_checkout(self):
        builder = script("build_local")
        catalogs = script("catalogs")
        checker = script("check_i18n")
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            work = Path(directory)
            source = (
                "Instala LG ThinQ AirCon Widget no seu usuário KDE: widget e conexão "
                "local automática."
            )
            template = work / "fixture.pot"
            po = work / "fixture.po"
            import json

            template.write_text(
                catalogs.HEADER + f'msgid {json.dumps(source, ensure_ascii=False)}\nmsgstr ""\n'
            )
            po.write_text(
                checker.HEADER
                + f'msgid {json.dumps(source, ensure_ascii=False)}\nmsgstr "SYNTHETIC LOADED"\n'
            )
            binary = work / "fixture.mo"
            catalogs.compile_catalog(po, template, binary)
            original = builder.build(work / "original.pyz")
            candidate = work / "synthetic.pyz"
            with zipfile.ZipFile(original) as first, zipfile.ZipFile(candidate, "w") as second:
                for name in first.namelist():
                    data = first.read(name)
                    if name == "locale/pt_BR/LC_MESSAGES/lgthinq-kde-widget.mo":
                        data = binary.read_bytes()
                    second.writestr(name, data)
            result = subprocess.run(
                [sys.executable, "-B", str(candidate), "--help"],
                cwd=work,
                env=dict(os.environ, PYTHONPATH="", LANGUAGE="pt_BR"),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("SYNTHETIC LOADED", result.stdout)

    def test_native_ki18n_loads_context_plural_and_falls_back(self):
        checker = script("check_i18n")
        domain = script("package_manifest").WIDGET_DOMAIN
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            result, binary = checker.compile_catalog(work, checker.extract(work), checker.CATALOG)
            self.assertEqual(result.returncode, 0, result.stderr)
            dest = work / "data/locale/pt_BR/LC_MESSAGES" / (domain + ".mo")
            dest.parent.mkdir(parents=True)
            dest.write_bytes(binary.read_bytes())
            qml = work / "tst_locale.qml"
            qml.write_text(
                """import QtQuick
import QtTest
import org.kde.ki18n
TestCase {
    name: "NativeCatalogLoading"
    KI18nContext { id: catalog; translationDomain: "DOMAIN" }
    function test_lookup() {
        compare(catalog.i18n("Device %1", 3), "Aparelho 3")
        compare(catalog.i18nc("Connection status", "Connected %1", 4), "Conectado 4")
        compare(catalog.i18np("%1 device", "%1 devices", 1), "1 aparelho")
        compare(catalog.i18np("%1 device", "%1 devices", 2), "2 aparelhos")
        compare(catalog.i18n("Missing source"), "Missing source")
    }
}""".replace("DOMAIN", domain)
            )
            result = subprocess.run(
                [script("qt_tools").resolve_runner(), "-platform", "offscreen", "-input", str(qml)],
                env=dict(
                    os.environ,
                    XDG_DATA_HOME=str(work / "data"),
                    LANGUAGE="pt_BR",
                    LC_ALL="pt_BR.UTF-8",
                ),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

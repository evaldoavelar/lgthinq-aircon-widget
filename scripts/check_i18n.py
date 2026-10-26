#!/usr/bin/env python3
"""Exercise real gettext extraction/merge with synthetic KDE format regressions."""

import ast
import gettext
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QML_MESSAGES = 4
HEADER = (
    "# Synthetic fixture, not a production catalog.\n"
    'msgid ""\nmsgstr ""\n'
    '"Project-Id-Version: synthetic-fixture\\n"\n'
    '"PO-Revision-Date: 2026-10-23 00:00+0000\\n"\n'
    '"Last-Translator: Synthetic fixture\\n"\n'
    '"Language-Team: Synthetic fixture\\n"\n'
    '"Language: pt_BR\\n"\n'
    '"MIME-Version: 1.0\\n"\n'
    '"Content-Type: text/plain; charset=UTF-8\\n"\n'
    '"Content-Transfer-Encoding: 8bit\\n"\n'
    '"Plural-Forms: nplurals=2; plural=(n > 1);\\n"\n\n'
)
CATALOG = HEADER + (
    '#, kde-format\nmsgid "Device %1"\nmsgstr "Aparelho %1"\n\n'
    '#, kde-format\nmsgctxt "Connection status"\n'
    'msgid "Connected %1"\nmsgstr "Conectado %1"\n\n'
    'msgctxt "CLI status"\nmsgid "Connected"\nmsgstr "Conectado"\n\n'
    '#, kde-format\nmsgid "%1 device"\nmsgid_plural "%1 devices"\n'
    'msgstr[0] "%1 aparelho"\nmsgstr[1] "%1 aparelhos"\n\n'
    '#, kde-format\nmsgctxt "Review plurality"\n'
    'msgid "One device"\nmsgid_plural "%1 devices"\n'
    'msgstr[0] "Um aparelho"\nmsgstr[1] "%1 aparelhos"\n'
)
# Includes the removed plural placeholder described by C1; never production PO.
INVALID_CASES = {
    "removed-i18n": ('msgstr "Aparelho %1"', 'msgstr "Aparelho"'),
    "replaced-i18n": ('msgstr "Aparelho %1"', 'msgstr "Aparelho %2"'),
    "removed-context": ('msgstr "Conectado %1"', 'msgstr "Conectado"'),
    "removed-singular": ('msgstr[0] "%1 aparelho"', 'msgstr[0] "aparelho"'),
    "removed-plural": ('msgstr[1] "%1 aparelhos"', 'msgstr[1] "aparelhos"'),
    "replaced-plural": ('msgstr[1] "%1 aparelhos"', 'msgstr[1] "%2 aparelhos"'),
    "c1-described-catalog": (
        'msgstr[0] "Um aparelho"\nmsgstr[1] "%1 aparelhos"',
        'msgstr[0] "Um aparelho"\nmsgstr[1] "aparelhos"',
    ),
}


def extract(work):
    qml = work / "fixture.qml"
    qml.write_text(
        "import QtQuick\nQtObject {\n"
        'property string device: i18n("Device %1", "synthetic")\n'
        'property string label: i18nc("Connection status", "Connected %1", "synthetic")\n'
        'property string count: i18np("%1 device", "%1 devices", 2)\n'
        'property string review: i18ncp("Review plurality", "One device", "%1 devices", 2)\n}\n'
    )
    python = work / "fixture.py"
    python.write_text('from gettext import pgettext\nlabel = pgettext("CLI status", "Connected")\n')
    template = work / "messages.pot"
    common = ["--from-code=UTF-8", "--no-location", "--package-name=synthetic-fixture"]
    # Explicit argument positions are required: --kde alone does not mark QML calls.
    keywords = {"i18n": (1,), "i18nc": (2,), "i18np": (1, 2), "i18ncp": (2, 3)}
    subprocess.run(
        [
            "xgettext",
            *common,
            "--language=C++",
            "--kde",
            "--keyword=",
            "--keyword=i18n:1",
            "--keyword=i18nc:1c,2",
            "--keyword=i18np:1,2",
            "--keyword=i18ncp:1c,2,3",
            *[f"--flag={name}:{arg}:kde-format" for name, args in keywords.items() for arg in args],
            "--output",
            str(template),
            str(qml),
        ],
        check=True,
    )
    subprocess.run(
        [
            "xgettext",
            *common,
            "--language=Python",
            "--keyword=",
            "--keyword=pgettext:1c,2",
            "--join-existing",
            "--output",
            str(template),
            str(python),
        ],
        check=True,
    )
    extracted = template.read_text()
    assert extracted.count("#, kde-format") == QML_MESSAGES, extracted
    for message in [
        'msgctxt "Connection status"',
        'msgctxt "CLI status"',
        'msgctxt "Review plurality"',
        'msgid_plural "%1 devices"',
    ]:
        assert message in extracted
    return template


def check_placeholders(catalog, *, allow_untranslated=False):
    """Compare each KDE singular/plural pair, including msgstr[0].

    GNU KDE format checks permit omission of the count in some singular forms.
    This project requires the placeholders present in each source form to survive.
    Parse PO directives and continued quoted strings; never evaluate PO as code.
    """
    for block in re.split(r"\n\s*\n", catalog.read_text()):
        if not any(line.startswith("#,") and "kde-format" in line for line in block.splitlines()):
            continue
        fields = {}
        current = None
        for line in block.splitlines():
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?) (".*")', line)
            if match:
                current = match[1]
                fields[current] = ast.literal_eval(match[2])
            elif line.startswith('"') and current:
                fields[current] += ast.literal_eval(line)
            else:
                raise ValueError(f"Unsupported PO directive: {line}")
        for key, translated in fields.items():
            if not key.startswith("msgstr"):
                continue
            if allow_untranslated and not translated:
                continue
            source = fields["msgid" if key in ("msgstr", "msgstr[0]") else "msgid_plural"]

            def placeholders(value):
                return set(re.findall(r"%[1-9][0-9]*", value))

            if placeholders(source) != placeholders(translated):
                raise ValueError(f"KDE format specification mismatch in {key}: {fields['msgid']}")


def compile_catalog(work, template, text):
    catalog = work / "pt_BR.po"
    catalog.write_text(text)
    merged = work / "merged.po"
    subprocess.run(
        [
            "msgmerge",
            "--quiet",
            "--no-fuzzy-matching",
            "--output-file",
            str(merged),
            str(catalog),
            str(template),
        ],
        check=True,
    )
    assert merged.read_text().count("#, kde-format") == QML_MESSAGES
    binary = work / "messages.mo"
    result = subprocess.run(
        ["msgfmt", "--check", "--check-format", "--output-file", str(binary), str(merged)],
        capture_output=True,
        text=True,
        env=dict(os.environ, LC_ALL="C"),
    )
    if result.returncode == 0:
        try:
            check_placeholders(merged)
        except ValueError as error:
            result = subprocess.CompletedProcess(result.args, 1, stderr=str(error))
    return result, binary


def validate(work):
    template = extract(work)
    result, binary = compile_catalog(work, template, CATALOG)
    assert result.returncode == 0, result.stderr
    with binary.open("rb") as stream:
        translation = gettext.GNUTranslations(stream)
    assert translation.gettext("Device %1") == "Aparelho %1"
    assert translation.pgettext("Connection status", "Connected %1") == "Conectado %1"
    assert translation.pgettext("CLI status", "Connected") == "Conectado"
    assert translation.ngettext("%1 device", "%1 devices", 1) == "%1 aparelho"
    assert translation.ngettext("%1 device", "%1 devices", 2) == "%1 aparelhos"
    assert (
        translation.npgettext("Review plurality", "One device", "%1 devices", 2) == "%1 aparelhos"
    )
    # MO stores compiled messages, not PO flags. Verify lookup after format checking.
    for name, (before, after) in INVALID_CASES.items():
        assert before in CATALOG
        result, _ = compile_catalog(work, template, CATALOG.replace(before, after))
        assert result.returncode != 0, f"Accepted broken KDE format: {name}"
        assert "format specification" in result.stderr, result.stderr
        print(f"PASS: rejected synthetic {name}: {result.stderr.strip()}")


def main():
    for tool in ["xgettext", "msgfmt", "msgmerge"]:
        if not shutil.which(tool):
            raise SystemExit(f"Missing translation tool: {tool}; production i18n pending")
    (ROOT / "dist").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="i18n-", dir=ROOT / "dist") as directory:
        validate(Path(directory))
    print("PASS: synthetic extraction/merge preserves kde-format; valid MO lookup; 7 negatives")
    print("PENDING: production English strings, pt_BR catalogs and Ki18n runtime in Plasma")


if __name__ == "__main__":
    main()

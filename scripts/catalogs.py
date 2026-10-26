#!/usr/bin/env python3
"""Extract actual marked sources; merge/check/compile draft catalogs without approval."""

import argparse
import ast
import json
import re
import subprocess
import tempfile
from pathlib import Path

from check_i18n import check_placeholders
from package_manifest import CATALOGS, PYTHON_DOMAIN, WIDGET_DOMAIN, catalog_sources

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = (WIDGET_DOMAIN, PYTHON_DOMAIN)
HEADER = (
    "# Source template; rights and linguistic review pending.\n"
    'msgid ""\nmsgstr ""\n'
    '"Project-Id-Version: LG ThinQ AirCon Widget 1.0.0rc1\\n"\n'
    '"MIME-Version: 1.0\\n"\n'
    '"Content-Type: text/plain; charset=UTF-8\\n"\n'
    '"Content-Transfer-Encoding: 8bit\\n"\n\n'
)


def source_paths(root, domain):
    if domain == WIDGET_DOMAIN:
        return sorted((root / "plasmoid/contents").rglob("*.qml"))
    return [*sorted((root / "src/lgthinq_daemon").glob("*.py")), root / "scripts/install_local.py"]


def extract(root, domain, output):
    paths = source_paths(root, domain)
    common = [
        "xgettext",
        "--from-code=UTF-8",
        "--force-po",
        "--no-wrap",
        "--add-comments=TRANSLATORS",
        "--keyword=",
    ]
    if domain == WIDGET_DOMAIN:
        common += [
            "--language=C++",
            "--kde",
            "--keyword=i18n:1",
            "--keyword=i18nc:1c,2",
            "--keyword=i18np:1,2",
            "--keyword=i18ncp:1c,2,3",
            *[
                f"--flag={name}:{arg}:kde-format"
                for name, args in {
                    "i18n": (1,),
                    "i18nc": (2,),
                    "i18np": (1, 2),
                    "i18ncp": (2, 3),
                }.items()
                for arg in args
            ],
        ]
    else:
        common += [
            "--language=Python",
            "--keyword=gettext:1",
            "--keyword=pgettext:1c,2",
            "--keyword=ngettext:1,2",
            "--keyword=npgettext:1c,2,3",
        ]
    output = Path(output).absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="catalog-extract-") as directory:
        body = Path(directory) / "body.pot"
        subprocess.run(
            [*common, "--output", str(body), *[str(p.relative_to(root)) for p in paths]],
            cwd=root,
            check=True,
        )
        # Let xgettext emit its charset header: --omit-header can lose UTF-8
        # msgids on supported gettext versions. Replace only the generated header
        # block (including variable timestamp), retaining Unicode message bytes.
        extracted = body.read_text(encoding="utf-8") if body.exists() else ""
        _, _, messages = extracted.partition("\n\n")
        output.write_text(HEADER + messages, encoding="utf-8")
    return output


def merge(catalog, template, output):
    if Path(output).resolve() in {Path(catalog).resolve(), Path(template).resolve()}:
        raise ValueError("Use a new output path; input catalogs are preserved")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "msgmerge",
            "--quiet",
            "--no-fuzzy-matching",
            "--no-wrap",
            "--output-file",
            str(output),
            str(catalog),
            str(template),
        ],
        check=True,
    )


def compile_catalog(catalog, template, output):
    """Check merged source flags, including untranslated fallback; never mark reviewed."""
    if Path(output).resolve() in {Path(catalog).resolve(), Path(template).resolve()}:
        raise ValueError("Output must not replace source catalogs")
    with tempfile.TemporaryDirectory(prefix="catalog-compile-") as directory:
        merged = Path(directory) / "merged.po"
        binary = Path(directory) / "messages.mo"
        merge(catalog, template, merged)
        if re.search(r"^#,.*\bfuzzy\b", merged.read_text(), re.MULTILINE):
            raise ValueError("Fuzzy translations require human review")
        subprocess.run(
            ["msgfmt", "--check", "--check-format", "--output-file", str(binary), str(merged)],
            check=True,
        )
        check_placeholders(merged, allow_untranslated=True)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_bytes(binary.read_bytes())


def inventory(root):
    """Conservative triage inventory: literals include technical IDs, never translations."""
    rows = []
    for domain in DOMAINS:
        for path in source_paths(root, domain):
            text = path.read_text()
            if path.suffix == ".py":
                values = [
                    (n.lineno, n.value)
                    for n in ast.walk(ast.parse(text))
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                ]
            else:
                values = [
                    (text.count("\n", 0, m.start()) + 1, ast.literal_eval(m[0]))
                    for m in re.finditer(r'"(?:[^"\\\n]|\\.)*"', text)
                ]
            for line, value in sorted(values):
                if value and any(c.isalpha() for c in value):
                    rows.append(
                        {
                            "domain": domain,
                            "path": str(path.relative_to(root)),
                            "line": line,
                            "source": value,
                            "status": "needs_triage",
                        }
                    )
    # KConfig defaults and localized metadata have separate extraction/review paths.
    for relative in ["plasmoid/contents/config/main.xml", "plasmoid/metadata.json"]:
        rows.append({"path": relative, "status": "separate_metadata_or_kconfig_review"})
    return rows


def check(root):
    with tempfile.TemporaryDirectory(prefix="catalog-check-") as directory:
        work = Path(directory)
        for domain in DOMAINS:
            template = extract(root, domain, work / f"{domain}.pot")
            if template.read_bytes() != (root / "po/templates" / template.name).read_bytes():
                raise ValueError(f"Stale source template: {domain}; run extract")
            count = len(re.findall(r'^msgid "', template.read_text(), re.MULTILINE)) - 1
            print(f"SOURCE CATALOG: {domain}: {count} marked messages")
        for domain, locale in CATALOGS:
            source = root / "po" / locale / f"{domain}.po"
            compiled = work / "compiled.mo"
            compile_catalog(source, root / "po/templates" / f"{domain}.pot", compiled)
            for relative in catalog_sources(domain, locale):
                if (root / relative).read_bytes() != compiled.read_bytes():
                    raise ValueError(f"Stale compiled catalog: {relative}")
    print(f"CHECKED: {len(CATALOGS)} explicitly selected catalogs")
    print(
        "DRAFT: empty en/pt_BR catalogs use source fallback; human "
        "translation/rights review required"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    e = commands.add_parser("extract")
    e.add_argument("--output-dir", type=Path, required=True)
    i = commands.add_parser("inventory")
    i.add_argument("--output", type=Path, required=True)
    for name in ["merge", "compile"]:
        c = commands.add_parser(name)
        c.add_argument("--catalog", type=Path, required=True)
        c.add_argument("--template", type=Path, required=True)
        c.add_argument("--output", type=Path, required=True)
    commands.add_parser("check")
    args = parser.parse_args()
    if args.action == "extract":
        for domain in DOMAINS:
            extract(ROOT, domain, args.output_dir / f"{domain}.pot")
    elif args.action == "inventory":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(inventory(ROOT), ensure_ascii=False, indent=2) + "\n")
    elif args.action == "check":
        check(ROOT)
    else:
        operation = merge if args.action == "merge" else compile_catalog
        operation(args.catalog, args.template, args.output)


if __name__ == "__main__":
    main()

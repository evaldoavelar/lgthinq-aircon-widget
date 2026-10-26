"""Exact package inventories. Unlisted checkout content is excluded by default.

New resources, translations and authorized legal notices require an exact mapping
here and inventory review; extensions, Git tracking and gitignore grant no access.
"""

import hashlib
import re
import stat
import unicodedata
import zipfile
from pathlib import Path
from urllib.parse import unquote

# Exact historical visual revisions retired under H02-H04. This catches byte-for-
# byte reinstatement only; it does not establish independent creation or rights.
RETIRED_GRAPHICS_SHA256 = frozenset(
    {
        "4a48996307d848876ea77ca52b0e9c8e5b2184c9b711d2fa9fa439b2272c717e",
        "562d0aab368fd10223f4f1300c39fe6ee20318eb20d1dba3851668299364eae9",
        "5b5b2214e572a1c3e5f4fbf97a60b74d5a012e6aaa7a3c1ee4ee1dd330c22869",
        "8e60d7faccc160f2f9badafe97049833dbc33493e73f215e03829d7ac56cd9da",
        "aa6be856883297f0a255e1a26986ef11aabe1cbaa28d4a11e7b2fa1ebed188e0",
        "b3a3febf46f19268dbe4d3f992cea96f2f024feb67345f121147cc12a0851ad5",
        "e90f6752bb6332c8dba3b6440eec9921cc5336de843be26039296432ba4d8e1f",
        "f5ae7cab1f41b3aff0afc3a3c306968d17e85b8b3f1954f7ec5fadf4fb582e63",
    }
)


def reject_retired_graphics(data, name):
    if hashlib.sha256(data).hexdigest() in RETIRED_GRAPHICS_SHA256:
        raise ValueError(f"Retired graphic content excluded: {name}")


LEGAL = ("LICENSE", "LICENSE-DOCS", "NOTICE")


WIDGET_DOMAIN = "plasma_applet_org.lgthinq.aircon"
PYTHON_DOMAIN = "lgthinq-kde-widget"
# Prepared fallback catalogs; all translations are empty and require human review.
# Selection is a technical inventory decision, never linguistic/legal approval.
CATALOGS = tuple(
    (domain, language) for domain in (WIDGET_DOMAIN, PYTHON_DOMAIN) for language in ("en", "pt_BR")
)


def catalog_sources(domain, locale):
    if domain not in {WIDGET_DOMAIN, PYTHON_DOMAIN} or not re.fullmatch(
        r"[a-z]{2,3}(?:_[A-Z]{2})?(?:@[a-z]+)?", locale
    ):
        raise ValueError("Invalid catalog domain or locale")
    parent = "plasmoid/contents" if domain == WIDGET_DOMAIN else "src/lgthinq_daemon"
    return (f"{parent}/locale/{locale}/LC_MESSAGES/{domain}.mo",)


def backend_catalogs():
    return [
        p
        for domain, locale in CATALOGS
        if domain == PYTHON_DOMAIN
        for p in catalog_sources(domain, locale)
    ]


def anchors(text):
    found = set()
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                if not marker[2].strip():
                    fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        match = re.match(r"^ {0,3}#{1,6}\s+(.+)$", line)
        if not match:
            continue
        heading = re.sub(r"\s+#+\s*$", "", match[1])
        heading = heading.strip().lower().replace("`", "")
        slug = "".join(
            c for c in heading if c in "-_ " or unicodedata.category(c)[0] in "LN"
        ).replace(" ", "-")
        candidate = slug
        count = 0
        while candidate in found:
            count += 1
            candidate = f"{slug}-{count}"
        found.add(candidate)
    return found


BACKEND = (
    "__init__.py",
    "__main__.py",
    "cli.py",
    "client.py",
    "config.py",
    "container_server.py",
    "credentials.py",
    "dbus_service.py",
    "engine.py",
    "http_api.py",
    "i18n.py",
    "live.py",
    "local.py",
    "models.py",
    "remote.py",
)
WIDGET = (
    "README.md",
    "metadata.json",
    "contents/images/lgthinq.svg",
    "contents/config/config.qml",
    "contents/config/main.xml",
    "contents/ui/AirConditioner.qml",
    "contents/ui/CardMenu.qml",
    "contents/ui/FeatureCard.qml",
    "contents/ui/IconGlyph.qml",
    "contents/ui/PanelIcon.qml",
    "contents/ui/TemperatureEditor.qml",
    "contents/ui/configAppearance.qml",
    "contents/ui/configConnection.qml",
    "contents/ui/main.qml",
)


def inventory(kind):
    """Return archive member -> required checkout path, with no optional globs."""
    widget = {name: f"plasmoid/{name}" for name in WIDGET}
    widget.update({name: name for name in LEGAL})
    for domain, locale in CATALOGS:
        for path in catalog_sources(domain, locale):
            if domain == WIDGET_DOMAIN:
                widget[path.removeprefix("plasmoid/")] = path
    if kind == "plasmoid":
        return widget
    if kind != "pyz":
        raise ValueError(f"Unknown package kind: {kind}")
    return {
        **{name: name for name in LEGAL},
        **{f"payload/{name}": name for name in LEGAL},
        "__main__.py": "scripts/install_local.py",
        "package_manifest.py": "scripts/package_manifest.py",
        "i18n_support.py": "src/lgthinq_daemon/i18n.py",
        "README.md": "docs/packaging/LOCAL-INSTALL.md",
        "payload/README.md": "docs/packaging/LOCAL-INSTALL.md",
        "payload/pyproject.toml": "pyproject.toml",
        "payload/BACKEND.md": "BACKEND.md",
        "payload/MANIFEST.in": "MANIFEST.in",
        **{f"payload/{p}": p for p in backend_catalogs()},
        **{p.removeprefix("src/lgthinq_daemon/"): p for p in backend_catalogs()},
        **{f"payload/src/lgthinq_daemon/{n}": f"src/lgthinq_daemon/{n}" for n in BACKEND},
        **{f"payload/plasmoid/{n}": p for n, p in widget.items()},
    }


def source_file(root, relative):
    """Require a regular source with no symlink in the selected path."""
    root = Path(root)
    if root.is_symlink():
        raise ValueError(f"Symlink package root: {root}")
    path = root
    for part in Path(relative).parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlink package source: {relative}")
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"Not a regular package source: {relative}")
    reject_retired_graphics(path.read_bytes(), relative)
    return path


def sources(root, kind):
    """Reject links in every selected path, including parent directories."""
    return {member: source_file(root, relative) for member, relative in inventory(kind).items()}


def validate_archive(artifact, kind):
    """Check the actual ZIP inventory, duplicates, types and documentation scope."""
    expected = set(inventory(kind))
    directories = {str(p) + "/" for n in expected for p in Path(n).parents if str(p) != "."}
    with zipfile.ZipFile(artifact) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        files = {n for n in names if not n.endswith("/")}
        if files != expected or set(names) - files - directories:
            raise ValueError(f"Package inventory mismatch: {files ^ expected}")
        if archive.testzip() is not None:
            raise ValueError("Corrupt package")
        for entry in archive.infolist():
            if not entry.is_dir():
                reject_retired_graphics(archive.read(entry), entry.filename)
            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Symlink archive member: {entry.filename}")
            allowed = {0, stat.S_IFDIR} if entry.is_dir() else {0, stat.S_IFREG}
            if stat.S_IFMT(mode) not in allowed:
                raise ValueError(f"Not a regular archive member: {entry.filename}")
        # Resolve only against the extracted package, never the checkout.
        for name in expected:
            if not name.endswith(".md"):
                continue
            text = archive.read(name).decode("utf-8")
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                target, _, fragment = unquote(target.strip("<>")).partition("#")
                if ":" in target or target.startswith("/"):
                    raise ValueError(f"Non-package documentation reference: {name}: {target}")
                path = Path(name).parent / target if target else Path(name)
                # No parent escapes or links relying on checkout documentation.
                normalized = []
                for part in path.parts:
                    if part == "..":
                        if not normalized:
                            raise ValueError(f"Documentation escapes package: {target}")
                        normalized.pop()
                    elif part != ".":
                        normalized.append(part)
                destination = "/".join(normalized)
                if destination not in expected:
                    raise ValueError(f"Unavailable package documentation: {name}: {target}")
                if fragment and destination.endswith(".md"):
                    if fragment not in anchors(archive.read(destination).decode("utf-8")):
                        raise ValueError(f"Unavailable package anchor: {name}: {target}#{fragment}")
    return sorted(files)

#!/usr/bin/env python3
"""Read-only evidence inventory, without importing dependencies or invoking Docker.

Installed metadata is a vendor declaration, not a binary license certification.
Conditional requirements are retained as candidates; this is not a lock/resolver.
"""

import argparse
import hashlib
import importlib.metadata as metadata
import json
import platform
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {
    "comprovado por evidência suficiente",
    "evidência parcial",
    "origem desconhecida",
    "dependente de confirmação do titular",
    "não redistribuível no estado atual",
    "não aplicável",
}


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement):
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    if not match:
        raise ValueError(f"Invalid requirement: {requirement}")
    return normalize(match[1])


def dependencies(root, lookup=metadata.distribution):
    config = tomllib.loads((root / "pyproject.toml").read_text())
    project = config["project"]
    groups = {"base": project["dependencies"], **project["optional-dependencies"]}
    groups["build"] = config["build-system"]["requires"]
    groups["host"] = ["dbus-python", "PyGObject", "pip"]
    seeds = {}
    for group, requirements in groups.items():
        for req in requirements:
            seeds.setdefault(requirement_name(req), []).append({"group": group, "requirement": req})
    pending = sorted(seeds)
    seen = {}
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        row = {"name": name, "direct_declarations": seeds.get(name, []), "evidence": "partial"}
        seen[name] = row
        try:
            dist = lookup(name)
        except metadata.PackageNotFoundError:
            row.update(installed=False, reason="Not present in this interpreter; not resolved")
            continue
        info = dist.metadata
        requires = list(dist.requires or [])
        legal, native = [], []
        for item in dist.files or []:
            relative = str(item)
            path = Path(dist.locate_file(item))
            is_legal = bool(
                re.search(
                    r"(?:^|/)(?:LICENSE|LICENCE|COPYING|NOTICE|AUTHORS)[^/]*$", relative, re.I
                )
            )
            is_native = relative.endswith((".so", ".pyd", ".dll", ".dylib")) or ".so." in relative
            if not (is_legal or is_native) or not path.is_file():
                continue
            data = path.read_bytes()
            record = {
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
            (legal if is_legal else native).append(record)
        row.update(
            installed=True,
            version=dist.version,
            license_expression=info.get("License-Expression"),
            license=info.get("License"),
            license_classifiers=[
                v for v in info.get_all("Classifier", []) if v.startswith("License ::")
            ],
            project_urls=info.get_all("Project-URL", []),
            homepage=info.get("Home-page"),
            requires=requires,
            legal_files=sorted(legal, key=lambda r: r["path"]),
            native_files=sorted(native, key=lambda r: r["path"]),
            origin="installed metadata/files; download source and wheel build not attested",
        )
        for requirement in requires:
            child = requirement_name(requirement)
            if child not in seen:
                pending.append(child)
    return {
        "python": platform.python_version(),
        "platform": sys.platform,
        "scope": (
            "candidate closure including unevaluated markers/extras; not an exact runtime lock"
        ),
        "payload": (
            "dependencies are external to pyz/plasmoid/wheel/sdist; "
            "Docker installs a separate resolution"
        ),
        "components": [seen[n] for n in sorted(seen)],
    }


def docker_plan(root):
    text = (root / "packaging/docker/Dockerfile").read_text()
    base = re.findall(r"^FROM\s+(.+)$", text, re.M)
    return {
        "dockerfile_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "base": base,
        "base_digest_pinned": all("@sha256:" in b for b in base),
        "copy_instructions": re.findall(r"^COPY\s+(.+)$", text, re.M),
        "run_instructions": re.findall(r"^RUN\s+(.+?)(?=\n[A-Z]+ |\Z)", text, re.M | re.S),
        "oci_labels": re.findall(r"^LABEL\s+(.+)$", text, re.M),
        "system_packages": "inherited from mutable base; no apt install in current Dockerfile",
        "python_resolution": "server extra + thinqconnect==1.0.14; transitive versions unpinned",
        "source_delivery": "not demonstrated; exact base/packages/native source mapping required",
        "publication": "suspended; no Docker operation performed by this inventory",
    }


def check_rights(root):
    rows = json.loads((root / "docs/rights-provenance.json").read_text())
    paths = [r["path"] for r in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate rights paths")
    for row in rows:
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe rights path")
        if row["status"] not in STATUSES or not row["evidence"] or not row["action"]:
            raise ValueError(f"Incomplete rights record: {path}")
        if (
            row["redistribution_authorized"] is not True
            or row.get("publication_authorization") != "maintainer-2026-10-26"
        ):
            raise ValueError(f"Publication authorization missing or inconsistent: {path}")
        actual = root / path
        if actual.is_symlink() or not actual.is_file():
            raise ValueError(f"Missing/linked rights source: {path}")
        if str(path) == "docs/rights-provenance.json":
            if row["reviewed_sha256"] is not None:
                raise ValueError("Self-referential manifest cannot carry its own digest")
        elif hashlib.sha256(actual.read_bytes()).hexdigest() != row["reviewed_sha256"]:
            raise ValueError(f"Stale rights evidence: {path}")
    # Exact public source universe, independent of Git (works in exported copies).
    public = {
        p.name
        for p in root.iterdir()
        if p.is_file()
        and p.name
        in {
            ".gitignore",
            "LICENSE",
            "LICENSE-DOCS",
            "NOTICE",
            "BACKEND.md",
            "CONTRIBUTING.md",
            "MANIFEST.in",
            "MANIFEST.md",
            "README.md",
            "pyproject.toml",
        }
    }
    for directory in ["docs", "packaging", "plasmoid", "po", "poc", "scripts", "src", "tests"]:
        public.update(
            str(p.relative_to(root))
            for p in (root / directory).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    # STATUS and evidence are protected local files, absent in public exports.
    public -= {
        "docs/STATUS.md",
        "docs/ACCEPTANCE.md",
        "docs/PROJECT_BRIEF.md",
        "docs/REA_INVESTIGATION.md",
    }
    public = {p for p in public if not p.startswith("docs/evidence/")}
    if set(paths) != public:
        raise ValueError(f"Rights coverage mismatch: {set(paths) ^ public}")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["dependencies", "docker-plan", "check-rights"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "check-rights":
        print(
            f"Rights records checked: {check_rights(ROOT)}; "
            "maintainer publication authorized (not a title certification)"
        )
        return
    result = dependencies(ROOT) if args.action == "dependencies" else docker_plan(ROOT)
    if args.output is None:
        parser.error("--output is required; choose a new path outside a preserved tree")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()

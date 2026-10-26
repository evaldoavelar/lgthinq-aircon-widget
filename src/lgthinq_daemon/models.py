"""Stable, conservative capability model independent of transport."""

import math
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Capability:
    path: tuple[str, ...]
    writable: bool = False
    values: list[Any] = field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = None
    excluded: list[Any] = field(default_factory=list)
    supported_writable: bool = False

    def validate(self, value: Any) -> None:
        if value in self.excluded:
            raise ValueError("Value excluded by profile")
        if not self.writable:
            raise ValueError("Property is read-only")
        if self.values:
            if value not in self.values:
                raise ValueError("Value outside profile enum")
            return
        if self.minimum is None or self.maximum is None:
            raise ValueError("Writable domain unavailable; refusing command")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Expected finite number")
        if not math.isfinite(value) or not self.minimum <= value <= self.maximum:
            raise ValueError("Value outside profile range")
        if self.step and not math.isclose(
            (value - self.minimum) / self.step,
            round((value - self.minimum) / self.step),
            abs_tol=1e-7,
        ):
            raise ValueError("Value outside profile step")


def _profile_unit(raw: Any) -> str | None:
    """Resolve a literal unit or one unambiguous readable enum; never stringify metadata."""
    if isinstance(raw, str):
        return raw or None
    if isinstance(raw, dict) and raw.get("type") == "enum" and "r" in raw.get("mode", []):
        domain = raw.get("value", {})
        readable = domain.get("r") if isinstance(domain, dict) else None
        if isinstance(readable, list) and len(readable) == 1:
            return readable[0] if isinstance(readable[0], str) and readable[0] else None
    return None


def capabilities(profile: dict) -> dict[str, Capability]:
    """Only expose explicit profile modes/domains; no appliance defaults."""
    result = {}

    def visit(node, path=(), unit=None):
        if isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    visit(item, path, unit)
        elif isinstance(node, dict):
            if "unit" in node:
                unit = _profile_unit(node["unit"])
            if "mode" in node:
                domain = node.get("value", {}).get("w", {})
                result[".".join(path) + (f".{unit}" if unit else "")] = Capability(
                    path,
                    "w" in node["mode"],
                    domain if isinstance(domain, list) else [],
                    domain.get("min") if isinstance(domain, dict) else None,
                    domain.get("max") if isinstance(domain, dict) else None,
                    domain.get("step") if isinstance(domain, dict) else None,
                    unit,
                    domain.get("except", []) if isinstance(domain, dict) else [],
                    "w" in node["mode"],
                )
            else:
                for key, value in node.items():
                    if key != "unit":
                        visit(value, (*path, key), unit)

    visit(profile.get("property", {}))
    return result


@dataclass
class Snapshot:
    connection: str = "disconnected"
    state: dict = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    updated_at: float | None = None
    error: str | None = None
    simulated: bool = False

    def to_dict(self):
        return asdict(self)

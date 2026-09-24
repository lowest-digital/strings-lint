"""Format-neutral model: a source catalog and its translations, and the findings about them."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entry:
    """One string in one language: plain text or plural forms."""
    text: str | None = None
    plural: dict[str, str] | None = None
    # Forms the format evaluates in every language (Apple `zero`, ICU `=0`); required in translations too.
    explicit: tuple[str, ...] = ()

    def texts(self) -> list[str]:
        return list(self.plural.values()) if self.plural else [self.text or ""]

    def empty(self) -> bool:
        return not any(t.strip() for t in self.texts())


@dataclass
class Catalog:
    """A source file and the translations that belong to it."""
    name: str                              # shown in findings, e.g. "Localizable.xcstrings"
    source_locale: str
    source: dict[str, Entry]
    targets: dict[str, dict[str, Entry]] = field(default_factory=dict)   # locale -> key -> entry
    files: dict[str, str] = field(default_factory=dict)                  # locale -> file path (for annotations)
    notes: list[str] = field(default_factory=list)                       # skipped constructs
    findings: list["Finding"] = field(default_factory=list)              # format-specific, found while reading


@dataclass
class Finding:
    file: str
    key: str
    locale: str
    rule: str
    severity: str   # error | warning
    message: str

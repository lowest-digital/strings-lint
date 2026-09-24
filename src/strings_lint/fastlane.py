"""Store listing texts in fastlane layout (deliver: metadata/<locale>/, supply: metadata/android/<locale>/).

Limits as documented by Apple (App Store Connect Help, "App information" and "Platform version information")
and Google (Play Console Help, "Best practices for your store listing"), checked 2026-09-24.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import Finding

APPLE = {"name.txt": ("chars", 30), "subtitle.txt": ("chars", 30), "keywords.txt": ("bytes", 100),
         "promotional_text.txt": ("chars", 170), "description.txt": ("chars", 4000), "release_notes.txt": ("chars", 4000)}
GOOGLE = {"title.txt": ("chars", 30), "short_description.txt": ("chars", 80), "full_description.txt": ("chars", 4000),
          "changelogs": ("chars", 500)}  # changelog limit from the Play Console form, not in the docs above


def _words(text: str) -> set[str]:
    return {w for w in re.split(r"[^\w]+", text.lower()) if len(w) > 1}


def check(files: list[Path]) -> list[Finding]:
    out: list[Finding] = []
    for path in files:
        parts = path.parts
        if path.suffix != ".txt" or "metadata" not in parts:
            continue
        rest = parts[len(parts) - parts[::-1].index("metadata"):]
        if rest and rest[0] == "android" and len(rest) >= 3:
            locale, field = rest[1], ("changelogs" if rest[2] == "changelogs" else rest[2])
            limit = GOOGLE.get(field)
        elif len(rest) == 2:
            locale, field = rest[0], rest[1]
            limit = APPLE.get(field)
        else:
            continue
        if limit is None:
            continue
        text = path.read_text(encoding="utf-8").rstrip("\n")
        unit, maximum = limit
        n = len(text.encode("utf-8")) if unit == "bytes" else len(text)
        if n > maximum:
            out.append(Finding(str(path), field, locale, "length", "error", f"{n} {unit}, limit {maximum}"))
        if field == "keywords.txt":
            if ", " in text:
                out.append(Finding(str(path), field, locale, "keywords", "warning", "spaces after commas waste bytes"))
            words = [w.strip().lower() for w in text.split(",") if w.strip()]
            if dup := sorted({w for w in words if words.count(w) > 1}):
                out.append(Finding(str(path), field, locale, "keywords", "warning", f"duplicates: {', '.join(dup)}"))
            name = _words(_read(path.parent / "name.txt")) | _words(_read(path.parent / "subtitle.txt"))
            if wasted := [w for w in words if w in name]:
                out.append(Finding(str(path), field, locale, "keywords", "warning",
                                   f"already in name or subtitle: {', '.join(wasted)}"))
        if field == "subtitle.txt" and (rep := _words(text) & _words(_read(path.parent / "name.txt"))):
            out.append(Finding(str(path), field, locale, "subtitle", "warning",
                               f"repeats words from the app name: {', '.join(sorted(rep))}"))
    return out


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

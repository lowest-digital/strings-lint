"""Xcode String Catalogs (.xcstrings)."""

from __future__ import annotations

import json
from pathlib import Path

from ..model import Catalog, Entry


def _entry(loc: dict) -> Entry | None:
    if "stringUnit" in loc:
        return Entry(text=loc["stringUnit"].get("value", ""))
    variations = loc.get("variations", {})
    if set(variations) == {"plural"}:
        forms = {k: v.get("stringUnit", {}).get("value", "") for k, v in variations["plural"].items()}
        return Entry(plural=forms, explicit=("zero",) if "zero" in forms else ())
    return None


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    catalogs = []
    for path in files:
        if path.suffix != ".xcstrings":
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        src = source or doc.get("sourceLanguage", "en")
        cat = Catalog(path.name, src, {}, files={src: str(path)})
        for key, item in doc.get("strings", {}).items():
            if not key or item.get("shouldTranslate") is False:
                continue
            locs = item.get("localizations", {})
            entry = _entry(locs[src]) if src in locs else Entry(text=key)
            if entry is None:
                cat.notes.append(f"{path.name}: '{key}' uses device variations or substitutions, skipped")
                continue
            cat.source[key] = entry
            for lang, loc in locs.items():
                if lang == src:
                    continue
                cat.files.setdefault(lang, str(path))
                if (e := _entry(loc)) is not None:
                    cat.targets.setdefault(lang, {})[key] = e
        catalogs.append(cat)
    return catalogs

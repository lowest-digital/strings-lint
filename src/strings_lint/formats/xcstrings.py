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


def _entries(key: str, loc: dict) -> dict[str, Entry] | None:
    """One localization → entries: plain/plural under `key`, device variants as `key [iphone]`,
    substitutions as main text `key` plus plural `key [name]`. None for unknown structures."""
    variations = loc.get("variations", {})
    if "substitutions" in loc:
        main = _entry({k: v for k, v in loc.items() if k != "substitutions"})
        if main is None:
            return None
        out = {key: main}
        for name, sub in loc["substitutions"].items():
            if (e := _entry(sub)) is None or e.plural is None:
                return None
            out[f"{key} [{name}]"] = e
        return out
    if "device" in variations:
        out = {}
        for device, node in variations["device"].items():
            if (e := _entry(node)) is None:
                return None
            out[f"{key} [{device}]"] = e
        return out
    return {key: e} if (e := _entry(loc)) is not None else None


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
            entries = _entries(key, locs[src]) if src in locs else {key: Entry(text=key)}
            if entries is None:
                cat.notes.append(f"{path.name}: '{key}' uses nested variations, skipped")
                continue
            cat.source.update(entries)
            for lang, loc in locs.items():
                if lang == src:
                    continue
                cat.files.setdefault(lang, str(path))
                if (t := _entries(key, loc)) is not None:
                    cat.targets.setdefault(lang, {}).update(t)
        catalogs.append(cat)
    return catalogs

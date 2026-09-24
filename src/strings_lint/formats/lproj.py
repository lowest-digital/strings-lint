"""Older iOS localization: <locale>.lproj/*.strings and *.stringsdict."""

from __future__ import annotations

import plistlib
import re
from collections import defaultdict
from pathlib import Path

from ..model import Catalog, Entry

_ENTRY = re.compile(r'(?:/\*.*?\*/\s*|//[^\n]*\n\s*)*"(?P<key>(?:[^"\\]|\\.)*)"\s*=\s*"(?P<value>(?:[^"\\]|\\.)*)"\s*;', re.S)
_ESC = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
FORMS = ("zero", "one", "two", "few", "many", "other")


def _unesc(s: str) -> str:
    return re.sub(r"\\U([0-9a-fA-F]{4})|\\(.)",
                  lambda m: chr(int(m.group(1), 16)) if m.group(1) else _ESC.get(m.group(2), m.group(2)), s)


def _text(path: Path) -> str:
    raw = path.read_bytes()
    return raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")


def read(path: Path) -> tuple[dict[str, Entry], list[str]]:
    if path.suffix == ".strings":
        return {_unesc(m["key"]): Entry(text=_unesc(m["value"])) for m in _ENTRY.finditer(_text(path))}, []
    entries, notes = {}, []
    for key, item in plistlib.loads(path.read_bytes()).items():
        m = re.fullmatch(r"%#@(\w+)@", item.get("NSStringLocalizedFormatKey", ""))
        var = item.get(m.group(1)) if m else None
        if not var or var.get("NSStringFormatSpecTypeKey") != "NSStringPluralRuleType":
            notes.append(f"{path.name}: '{key}' has several variables, skipped")
            continue
        forms = {k: var[k] for k in FORMS if k in var}
        entries[key] = Entry(plural=forms, explicit=("zero",) if "zero" in forms else ())
    return entries, notes


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    groups: dict[tuple[Path, str], dict[str, Path]] = defaultdict(dict)
    for path in files:
        if path.parent.suffix == ".lproj" and path.suffix in (".strings", ".stringsdict"):
            groups[(path.parent.parent, path.name)][path.parent.stem] = path
    catalogs = []
    for (folder, name), by_locale in sorted(groups.items()):
        src = source if source in by_locale else next((c for c in ("en", "Base", "en-US", "en-GB") if c in by_locale), None)
        if src is None:
            continue
        entries, notes = read(by_locale[src])
        cat = Catalog(f"{folder.name}/{src}.lproj/{name}", src, entries, files={src: str(by_locale[src])}, notes=notes)
        for loc, path in sorted(by_locale.items()):
            if loc in (src, "Base"):
                continue
            cat.files[loc] = str(path)
            cat.targets[loc], more = read(path)
            cat.notes += more
        catalogs.append(cat)
    return catalogs

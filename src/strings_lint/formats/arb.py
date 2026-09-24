"""Flutter ARB files (app_en.arb, app_de.arb …); ICU plural messages are split into forms."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ..model import Catalog, Entry

_HEAD = re.compile(r"\{\s*(\w+)\s*,\s*plural\s*,")
_FORM = re.compile(r"\s*(=\d+|zero|one|two|few|many|other)\s*\{")
_SUFFIX = re.compile(r"^(?P<stem>.*?)_(?P<loc>[a-z]{2,3}(?:_[A-Za-z]{2,4})?)$")


def icu_plural(text: str) -> dict[str, str] | None:
    m = _HEAD.match(text.strip())
    if not m:
        return None
    rest, forms = text.strip()[m.end():], {}
    while f := _FORM.match(rest):
        depth, i = 1, f.end()
        while i < len(rest) and depth:
            depth += {"{": 1, "}": -1}.get(rest[i], 0)
            i += 1
        if depth:
            return None
        forms[f.group(1)] = rest[f.end():i - 1]
        rest = rest[i:]
    return forms if rest.strip() == "}" and "other" in forms else None


def read(path: Path) -> tuple[str | None, dict[str, Entry], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    m = _SUFFIX.match(path.stem)
    locale = data.get("@@locale") or (m["loc"] if m else None)
    entries, notes = {}, []
    for key, value in data.items():
        if key.startswith("@") or not isinstance(value, str):
            continue
        if (forms := icu_plural(value)) is not None:
            entries[key] = Entry(plural=forms, explicit=tuple(k for k in forms if k.startswith("=")))
        elif re.search(r",\s*(plural|select|selectordinal)\s*,", value):
            notes.append(f"{path.name}: '{key}' uses nested ICU (select or text around plural), skipped")
        else:
            entries[key] = Entry(text=value)
    return (locale.replace("_", "-") if locale else None), entries, notes


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    groups: dict[tuple[Path, str], dict[str, tuple[Path, dict, list]]] = defaultdict(dict)
    for path in files:
        if path.suffix != ".arb":
            continue
        locale, entries, notes = read(path)
        if locale is None:
            continue
        m = _SUFFIX.match(path.stem)
        groups[(path.parent, m["stem"] if m else path.stem)][locale] = (path, entries, notes)
    catalogs = []
    for (folder, stem), by_locale in sorted(groups.items()):
        src = source if source in by_locale else ("en" if "en" in by_locale else None)
        if src is None:
            continue
        path, entries, notes = by_locale[src]
        cat = Catalog(f"{folder.name}/{path.name}", src, entries, files={src: str(path)}, notes=list(notes))
        for loc, (p, e, n) in sorted(by_locale.items()):
            if loc != src:
                cat.files[loc], cat.targets[loc] = str(p), e
                cat.notes += n
        catalogs.append(cat)
    return catalogs

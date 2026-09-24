"""i18next-style JSON: locales/<locale>/<namespace>.json or <dir>/<locale>.json; nested keys, _one/_other plurals."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ..model import Catalog, Entry

LOCALE = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z]{2,4})?$")
FORMS = ("zero", "one", "two", "few", "many", "other")


def _flat(d: dict, prefix: str = ""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flat(v, f"{prefix}{k}.")
        else:
            yield f"{prefix}{k}", v


def read(path: Path) -> dict[str, Entry]:
    flat = dict(_flat(json.loads(path.read_text(encoding="utf-8"))))
    entries, done = {}, set()
    for key, value in flat.items():
        if key in done:
            continue
        base, _, form = key.rpartition("_")
        if form in FORMS and f"{base}_other" in flat:
            forms = {f: flat[f"{base}_{f}"] for f in FORMS if f"{base}_{f}" in flat}
            done |= {f"{base}_{f}" for f in forms}
            entries[base] = Entry(plural=forms, explicit=("zero",) if "zero" in forms else ())
        elif isinstance(value, str):
            entries[key] = Entry(text=value)
    return entries


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    groups: dict[str, dict[str, Path]] = defaultdict(dict)   # group id -> locale -> path
    for path in files:
        if path.suffix != ".json" or path.name in ("package.json", "tsconfig.json", "package-lock.json"):
            continue
        if LOCALE.match(path.stem) and not LOCALE.match(path.parent.name):
            groups[str(path.parent)][path.stem.replace("_", "-")] = path          # locales/en.json
        elif LOCALE.match(path.parent.name):
            groups[f"{path.parent.parent}/*/{path.name}"][path.parent.name.replace("_", "-")] = path  # locales/en/common.json
    catalogs = []
    for group, by_locale in sorted(groups.items()):
        src = source if source in by_locale else ("en" if "en" in by_locale else None)
        if src is None or len(by_locale) < 2:
            continue
        try:
            cat = Catalog(str(Path(by_locale[src]).relative_to(Path(by_locale[src]).parents[1])), src,
                          read(by_locale[src]), files={src: str(by_locale[src])})
            for loc, path in sorted(by_locale.items()):
                if loc != src:
                    cat.files[loc], cat.targets[loc] = str(path), read(path)
        except (json.JSONDecodeError, AttributeError):
            continue
        catalogs.append(cat)
    return catalogs

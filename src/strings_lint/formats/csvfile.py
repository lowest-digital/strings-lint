"""CSV with a `key` column and one column per locale."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from ..model import Catalog, Entry
from ..plurals import categories

LOCALE = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z]{2,4})?$")
NOT_LOCALES = {"key", "id", "max", "comment", "context", "note", "notes", "description", "type", "tag", "tags"}


def _is_locale(column: str) -> bool:
    return bool(LOCALE.match(column)) and column.lower() not in NOT_LOCALES and categories(column) is not None


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    catalogs = []
    for path in files:
        if path.suffix != ".csv":
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            continue
        try:
            dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        columns = [c for c in (reader.fieldnames or []) if c and _is_locale(c)]
        src = source if source in columns else ("en" if "en" in columns else None)
        if "key" not in (reader.fieldnames or []) or src is None:
            continue
        rows = [r for r in reader if (r.get("key") or "").strip() and (r.get(src) or "").strip()]
        cat = Catalog(path.name, src, {r["key"].strip(): Entry(text=r[src]) for r in rows},
                      files={c: str(path) for c in columns})
        for col in columns:
            if col != src:
                cat.targets[col] = {r["key"].strip(): Entry(text=r[col] or "") for r in rows}
        catalogs.append(cat)
    return catalogs

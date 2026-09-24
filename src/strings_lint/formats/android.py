"""Android resources: res/values/*.xml and res/values-<locale>/*.xml."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from ..model import Catalog, Entry, Finding

_QUALIFIER = re.compile(r"^values-(?:b\+(?P<b>[a-zA-Z0-9+]+)|(?P<lang>[a-z]{2,3})(?:-r(?P<region>[A-Z]{2}))?)$")
_ESC = {"n": "\n", "t": "\t", "'": "'", '"': '"', "@": "@", "?": "?", "\\": "\\"}


def locale_of(folder: str) -> str | None:
    """values-pt-rBR → pt-BR, values-b+zh+Hans → zh-Hans; None for values-night, values-v21 …"""
    m = _QUALIFIER.match(folder)
    if not m:
        return None
    if m["b"]:
        return "-".join(m["b"].split("+"))
    return m["lang"] + (f"-{m['region']}" if m["region"] else "")


def _inner(el: ET.Element) -> str:
    return (el.text or "") + "".join(ET.tostring(c, encoding="unicode") for c in el)


def unescape(raw: str) -> str:
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    else:
        raw = re.sub(r"\s+", " ", raw).strip()
    return re.sub(r"\\u([0-9a-fA-F]{4})|\\(.)",
                  lambda m: chr(int(m.group(1), 16)) if m.group(1) else _ESC.get(m.group(2), m.group(2)), raw)


def unescaped_apostrophe(raw: str) -> bool:
    """aapt rejects a bare ' outside double quotes."""
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        return False
    return re.search(r"(?<!\\)'", raw) is not None


def read(path: Path) -> tuple[dict[str, Entry], list[str], list[str]]:
    """(entries, keys with a bare apostrophe, notes)."""
    root = ET.parse(path).getroot()
    entries, apostrophes, notes = {}, [], []
    for el in root:
        name = el.get("name", "")
        if el.get("translatable") == "false":
            continue
        if el.tag == "string":
            raw = _inner(el)
            entries[name] = Entry(text=unescape(raw))
            if unescaped_apostrophe(raw):
                apostrophes.append(name)
        elif el.tag == "plurals":
            forms = {}
            for item in el.findall("item"):
                raw = _inner(item)
                forms[item.get("quantity")] = unescape(raw)
                if unescaped_apostrophe(raw):
                    apostrophes.append(name)
            entries[name] = Entry(plural=forms, explicit=("zero",) if "zero" in forms else ())
        elif el.tag == "string-array":
            notes.append(f"{path.name}: <string-array name='{name}'> skipped")
    return entries, apostrophes, notes


def discover(files: list[Path], source: str | None) -> list[Catalog]:
    groups: dict[tuple[Path, str], dict[str, Path]] = defaultdict(dict)   # (res dir, file name) -> locale -> path
    for path in files:
        if path.suffix != ".xml" or not path.parent.name.startswith("values"):
            continue
        if path.parent.name == "values":
            groups[(path.parent.parent, path.name)]["__source__"] = path
        elif (loc := locale_of(path.parent.name)) is not None:
            groups[(path.parent.parent, path.name)][loc] = path
    catalogs = []
    for (res, name), by_locale in sorted(groups.items()):
        if "__source__" not in by_locale:
            continue
        src_path = by_locale.pop("__source__")
        try:
            src_entries, apos, notes = read(src_path)
        except ET.ParseError:
            continue  # not a resource file we understand
        if not src_entries:
            continue
        cat = Catalog(f"{res.name}/values/{name}", source or "default", src_entries, files={"__source__": str(src_path)},
                      notes=notes)
        _apostrophes(cat, str(src_path), "default", apos)
        for loc, path in sorted(by_locale.items()):
            cat.files[loc] = str(path)
            try:
                entries, apos, notes = read(path)
            except ET.ParseError as e:
                cat.findings.append(Finding(str(path), "", loc, "xml", "error", f"not valid XML: {e}"))
                continue
            cat.targets[loc] = entries
            cat.notes += notes
            _apostrophes(cat, str(path), loc, apos)
        catalogs.append(cat)
    return catalogs


def _apostrophes(cat: Catalog, path: str, locale: str, keys: list[str]) -> None:
    for key in dict.fromkeys(keys):
        cat.findings.append(Finding(path, key, locale, "android-apostrophe", "error",
                                    "unescaped ' breaks the build: write \\' or wrap the text in double quotes"))

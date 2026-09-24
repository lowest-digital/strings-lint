"""Rules comparing each translation with its source."""

from __future__ import annotations

from . import placeholders, plurals
from .model import Catalog, Entry, Finding

RULES = {
    "missing": "key exists in the source but not in the translation",
    "empty": "translation is empty",
    "stale": "key exists in the translation but no longer in the source",
    "plural": "plural forms required by CLDR are missing, or forms the language does not use",
    "placeholder": "placeholders differ from the source (count, type or order)",
    "positional": "source has repeated unpositioned arguments (%d … %d); translations cannot reorder them safely",
    "android-apostrophe": "Android string contains an unescaped apostrophe",
    "xml": "Android resource file is not valid XML",
    "length": "store text exceeds the App Store / Google Play limit",
    "keywords": "App Store keywords waste bytes or repeat themselves",
    "subtitle": "App Store subtitle repeats words from the app name",
}


def check(cat: Catalog) -> list[Finding]:
    out = list(cat.findings)
    src_file = cat.files.get(cat.source_locale) or cat.files.get("__source__", cat.name)

    for key, entry in cat.source.items():
        if any(placeholders.ambiguous_repeats(t) for t in entry.texts()):
            out.append(Finding(src_file, key, cat.source_locale, "positional", "warning",
                               "repeated unpositioned arguments; use %1$lld … %2$lld so translations can reorder them"))

    for locale, entries in cat.targets.items():
        file = cat.files.get(locale, cat.name)
        for key, src in cat.source.items():
            tgt = entries.get(key)
            if tgt is None:
                out.append(Finding(file, key, locale, "missing", "warning", "not translated"))
                continue
            out += _compare(file, key, locale, src, tgt)
        for key in entries.keys() - cat.source.keys():
            out.append(Finding(file, key, locale, "stale", "warning", "not in the source any more"))
    return out


def _compare(file: str, key: str, locale: str, src: Entry, tgt: Entry) -> list[Finding]:
    out: list[Finding] = []

    def add(rule: str, severity: str, message: str) -> None:
        out.append(Finding(file, key, locale, rule, severity, message))

    if tgt.empty():
        add("empty", "error", "empty translation")
        return out
    reference = (src.plural or {}).get("other") or next(iter(src.plural.values()), "") if src.plural else src.text or ""

    if tgt.plural:
        required = plurals.categories(locale)
        if required is not None:
            explicit = [f for f in (src.explicit or ()) if f not in required]
            needed = [*required, *explicit]
            if missing := [f for f in required if not tgt.plural.get(f, "").strip()]:
                add("plural", "error", f"missing plural forms: {', '.join(missing)} (needs {', '.join(required)})")
            if special := [f for f in explicit if not tgt.plural.get(f, "").strip()]:
                add("plural", "warning", f"source has a special text for {', '.join(special)}, translation does not")
            if unused := [f for f in tgt.plural if f not in needed and f not in (tgt.explicit or ())]:
                add("plural", "warning", f"plural forms not used in {locale}: {', '.join(unused)}")
        for form, text in tgt.plural.items():
            for problem in placeholders.compare(reference, text):
                # "One day left" without %d is fine where the form stands for exactly one number
                exact = form == "zero" or form.startswith("=") or (form == "one" and plurals.one_is_exactly_one(locale))
                severity = "warning" if problem.startswith("missing") and exact else "error"
                add("placeholder", severity, f"[{form}] {problem}")
    else:
        if src.plural:
            add("plural", "error", "source has plural forms, translation is a single text")
        for problem in placeholders.compare(reference, tgt.text or ""):
            add("placeholder", "error", problem)
    return out

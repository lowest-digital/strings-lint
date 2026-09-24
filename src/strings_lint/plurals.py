"""CLDR plural categories per locale (via Babel)."""

from __future__ import annotations

from functools import lru_cache

from babel import Locale, UnknownLocaleError

ORDER = ("zero", "one", "two", "few", "many", "other")


@lru_cache(maxsize=None)
def _locale(code: str) -> Locale | None:
    try:
        return Locale.parse(code.replace("-", "_"))
    except (ValueError, UnknownLocaleError):
        try:  # e.g. "zh-CN" style Android qualifiers: fall back to the language
            return Locale.parse(code.split("-")[0].split("_")[0])
        except (ValueError, UnknownLocaleError):
            return None


def categories(code: str) -> list[str] | None:
    """Required CLDR categories, `other` always included; None if the locale is unknown."""
    loc = _locale(code)
    if loc is None:
        return None
    tags = loc.plural_form.tags | {"other"}
    return [t for t in ORDER if t in tags]


def one_is_exactly_one(code: str) -> bool:
    """True where `one` only means 1 (en, de); False where it also covers 21, 31 … (ru, uk)."""
    loc = _locale(code)
    return loc is None or loc.plural_form(21) != "one"

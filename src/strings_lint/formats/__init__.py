"""Readers per file format. Each module exposes `discover(files, source) -> list[Catalog]`, where `files` are all
candidate files below the scanned paths and `source` is a forced source locale or None (auto-detect)."""

from . import android, arb, csvfile, i18next, lproj, xcstrings

READERS = [xcstrings, lproj, android, arb, i18next, csvfile]

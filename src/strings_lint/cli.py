"""strings-lint [PATH ...] – lint localization files below the given paths (default: current directory)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

from . import __version__, fastlane, rules
from .formats import READERS
from .model import Finding

SKIP = {".git", "node_modules", "build", "Pods", "DerivedData", ".venv", "venv", ".gradle", ".dart_tool", "dist"}


def collect(paths: list[str]) -> list[Path]:
    files = []
    for p in map(Path, paths):
        if p.is_file():
            files.append(p)
            continue
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP]
            files += [Path(root) / n for n in names]
    return sorted(files)


def lint(paths: list[str], source: str | None = None) -> tuple[list[Finding], list[str], int]:
    """(findings, notes, number of catalogs)."""
    files = collect(paths)
    findings, notes, catalogs = [], [], 0
    for reader in READERS:
        for cat in reader.discover(files, source):
            catalogs += 1
            findings += rules.check(cat)
            notes += cat.notes
    findings += fastlane.check(files)
    return findings, notes, catalogs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="strings-lint", description=__doc__.split("–")[1].strip())
    p.add_argument("paths", nargs="*", default=["."])
    p.add_argument("--source", help="source locale if not detected (default: file's own, else en)")
    p.add_argument("--format", choices=["text", "json", "github"], default="text")
    p.add_argument("--ignore", default="", help="comma-separated rules to skip, e.g. missing,stale")
    p.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    p.add_argument("--list-rules", action="store_true")
    p.add_argument("--version", action="version", version=f"strings-lint {__version__}")
    a = p.parse_args(argv)

    if a.list_rules:
        for name, text in rules.RULES.items():
            print(f"{name:20} {text}")
        return 0

    findings, notes, catalogs = lint(a.paths, a.source)
    ignored = {r.strip() for r in a.ignore.split(",") if r.strip()}
    findings = [f for f in findings if f.rule not in ignored]
    count = Counter(f.severity for f in findings)

    if a.format == "json":
        print(json.dumps([f.__dict__ for f in findings], ensure_ascii=False, indent=2))
    elif a.format == "github":
        for f in findings:
            title = f"strings-lint {f.rule}"
            print(f"::{f.severity} file={f.file},title={title}::{f.locale} {f.key}: {f.message}".replace("\n", "%0A"))
    else:
        for file in dict.fromkeys(f.file for f in findings):
            print(file)
            for f in (x for x in findings if x.file == file):
                mark = "error  " if f.severity == "error" else "warning"
                print(f"  {mark} {f.locale:8} {f.rule:18} {f.key}: {f.message}")
        for n in notes:
            print(f"note: {n}")
        print(f"{catalogs} catalog(s) checked: {count['error']} error(s), {count['warning']} warning(s)")

    return 1 if count["error"] or (a.strict and count["warning"]) else 0


if __name__ == "__main__":
    sys.exit(main())

"""The fixture app contains one deliberate mistake per format; every one must be found, nothing else."""

import json
from pathlib import Path

from strings_lint.cli import lint, main

APP = Path(__file__).parent / "fixtures" / "app"

EXPECTED = {
    # (rule, severity, locale, key contains)
    ("positional", "warning", "en", "You completed %lld of %lld"),
    ("plural", "error", "pl", "%lld days left"),
    ("empty", "error", "pl", "Save"),
    ("placeholder", "error", "ja", "You completed %lld of %lld"),
    ("placeholder", "error", "de", "greeting"),
    ("stale", "warning", "de", "old"),
    ("plural", "warning", "de", "streak"),
    ("android-apostrophe", "error", "fr", "greeting"),
    ("plural", "error", "pt-BR", "habits_done"),
    ("plural", "warning", "de", "habitsLeft"),
    ("placeholder", "warning", "ru", "habitsLeft"),
    ("placeholder", "error", "ru", "habitsLeft"),
    ("placeholder", "error", "de", "welcome"),
    ("stale", "warning", "de", "legacy"),
    ("placeholder", "error", "de", "share"),
    ("length", "error", "en-US", "short_description.txt"),
    ("keywords", "warning", "de-DE", "keywords.txt"),
    ("length", "error", "de-DE", "subtitle.txt"),
    ("subtitle", "warning", "de-DE", "subtitle.txt"),
    ("length", "error", "ja", "keywords.txt"),
    ("missing", "warning", "de", "tap_to_continue [mac]"),
    ("placeholder", "error", "de", "%#@days@ and %#@hours@ left [hours]"),
    ("placeholder", "warning", "de", "%#@days@ and %#@hours@ left [hours]"),
    ("missing", "warning", "pt-BR", "pages[2]"),
    ("missing", "warning", "fr", "pages[0]"),
    ("missing", "warning", "fr", "pages[2]"),
    ("missing", "warning", "zh-Hans", "pages[0]"),
    ("missing", "warning", "zh-Hans", "pages[2]"),
}


def test_finds_every_planted_mistake_and_nothing_else():
    findings, notes, catalogs = lint([str(APP)])
    got = {(f.rule, f.severity, f.locale, f.key) for f in findings}
    for rule, severity, locale, key in EXPECTED:
        assert any(g[:3] == (rule, severity, locale) and key in g[3] for g in got), (rule, locale, key)
    for g in got:
        assert any(g[:3] == e[:3] and e[3] in g[3] for e in EXPECTED), f"unexpected finding {g}"
    assert catalogs == 7  # xcstrings, 2× lproj, android, arb, i18next, csv


def test_ignored_files():
    findings, _, _ = lint([str(APP)])
    files = {f.file for f in findings}
    assert not any("package.json" in f or "values-night" in f or "support_url" in f for f in files)


def test_exit_codes_and_options(capsys):
    assert main([str(APP)]) == 1
    assert main([str(APP / "web"), "--ignore", "placeholder,stale"]) == 0
    assert main([str(APP / "web"), "--ignore", "placeholder", "--strict"]) == 1   # stale is a warning
    capsys.readouterr()


def test_json_and_github_output(capsys):
    main([str(APP / "csv"), "--format", "json"])
    [finding] = json.loads(capsys.readouterr().out)
    assert finding["rule"] == "placeholder" and finding["key"] == "share"
    main([str(APP / "csv"), "--format", "github"])
    line = capsys.readouterr().out.strip()
    assert line.startswith("::error file=") and "title=strings-lint placeholder" in line

# Changelog

## 0.2.0

- `.xcstrings`: device variations (`key [iphone]`, `key [mac]`) and substitutions (`%#@days@` main text plus
  each substitution's plural forms as `key [days]`) are checked instead of skipped
- `%arg` inside substitutions is a placeholder
- Android `<string-array>`: every item is checked as `name[n]`; `@string/` references are ignored
- `placeholders.differences()` returns structured results for tools that word the messages themselves
- Text output in an interactive terminal ends with one line pointing to our paid localization service;
  never shown in CI, pipes, `--format json` or `--format github`

## 0.1.0

First release.

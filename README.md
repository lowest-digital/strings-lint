# strings-lint

[![PyPI](https://img.shields.io/pypi/v/strings-lint)](https://pypi.org/project/strings-lint/) [![CI](https://github.com/lowest-digital/strings-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/lowest-digital/strings-lint/actions/workflows/ci.yml)

Lint the translations already in your app repo. strings-lint compares every language with its source and
finds the mistakes that compile fine and then show up on a user's screen:

- **Placeholders** missing, added, or swapped: `%1$@`, `%lld`, `{count}`, `{{name}}`, `<b>`
- **Plural forms** a language needs by CLDR: Polish `one few many other`, Japanese only `other`
- **Repeated arguments** like `%lld of %lld` that a translator cannot reorder safely
- **Empty, missing and stale** keys
- **Android** apostrophes that break the build, invalid XML
- **App Store / Google Play** texts over the limit, keywords counted in UTF-8 bytes, wasted keywords

It reads your files as they are. Nothing is uploaded, nothing is changed.

```console
$ strings-lint ios android fastlane/metadata/ja
ios/Localizable.xcstrings
  warning en       positional         Hello, %@! You completed %lld of %lld habits today.: repeated unpositioned arguments; use %1$lld … %2$lld so translations can reorder them
  error   pl       plural             %lld days left: missing plural forms: few, many (needs one, few, many, other)
  error   pl       empty              Save: empty translation
  error   ja       placeholder        Hello, %@! You completed %lld of %lld habits today.: order %lld %@ %lld instead of %@ %lld %lld; use positional specifiers (%1$@) to reorder
ios/Legacy/de.lproj/Localizable.strings
  error   de       placeholder        greeting: missing %ld
  warning de       stale              old: not in the source any more
ios/Legacy/de.lproj/Localizable.stringsdict
  warning de       plural             streak: source has a special text for zero, translation does not
android/app/src/main/res/values-fr/strings.xml
  error   fr       android-apostrophe greeting: unescaped ' breaks the build: write \' or wrap the text in double quotes
android/app/src/main/res/values-pt-rBR/strings.xml
  error   pt-BR    plural             habits_done: missing plural forms: many (needs one, many, other)
fastlane/metadata/ja/keywords.txt
  error   ja       length             keywords.txt: 133 bytes, limit 100
4 catalog(s) checked: 7 error(s), 3 warning(s)
```

## Install

```bash
pipx install strings-lint      # or: uv tool install strings-lint
strings-lint path/to/your/app
```

Or run it once without installing: `uvx strings-lint` / `pipx run strings-lint`.

Requires Python 3.10+. The only dependency is [Babel](https://babel.pocoo.org/) for CLDR plural rules.

## Supported formats

| Format | Source | Translations |
| --- | --- | --- |
| Xcode String Catalog | `*.xcstrings` (`sourceLanguage`) | localizations in the same file |
| iOS `.strings` / `.stringsdict` | `en.lproj/`, `Base.lproj/` | `<locale>.lproj/` |
| Android resources | `res/values/*.xml` | `res/values-<qualifier>/` (`values-pt-rBR`, `values-b+zh+Hans`) |
| Flutter ARB | `app_en.arb` (`@@locale`) | `app_<locale>.arb`, ICU plurals incl. `=0` |
| i18next JSON | `locales/en/*.json` or `locales/en.json` | sibling locale folders or files, `_one`/`_other` |
| CSV | column `en` next to `key` | one column per locale |
| fastlane metadata | `metadata/<locale>/*.txt`, `metadata/android/<locale>/*.txt` | every locale is checked against the store limits |

The source locale is detected per file (`sourceLanguage`, `@@locale`, `en`). Use `--source de` if your source is
another language.

## Options

```text
strings-lint [PATH ...]            default: current directory
  --format text|json|github        github prints workflow annotations
  --ignore missing,stale           skip rules (see --list-rules)
  --strict                         exit 1 on warnings too
  --source LOCALE                  source locale if not detected
  --list-rules
```

Exit code 1 if there is any error (or any warning with `--strict`).

## GitHub Actions

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- run: pipx run strings-lint --format github --ignore missing
```

## Rules

| Rule | Severity | What it means |
| --- | --- | --- |
| `placeholder` | error | placeholders differ from the source; a missing number in `one`/`zero`/`=0` forms is only a warning where the form means exactly one value |
| `plural` | error | CLDR forms missing (warning: forms the language never uses, or the source's special `zero`/`=0` text is missing) |
| `empty` | error | translation is empty |
| `android-apostrophe`, `xml` | error | Android resource would not build |
| `length` | error | App Store / Google Play limit exceeded |
| `positional` | warning | source repeats unpositioned arguments (`%d … %d`) |
| `missing`, `stale` | warning | key not translated / no longer in the source |
| `keywords`, `subtitle` | warning | App Store keyword field wastes bytes or repeats itself |

Store limits as documented by Apple and Google, checked September 2026: app name and subtitle 30 characters,
keywords 100 bytes, promotional text 170, description and What's New 4,000; Google Play title 30, short
description 80, full description 4,000, release notes 500 (Play Console form).

## Not supported yet

Device variations and substitutions in `.xcstrings`, `.stringsdict` entries with several variables, ICU `select`,
Android `<string-array>`, XLIFF and gettext. They are reported as notes and skipped.

## Why this exists

We run a localization service for indie apps and kept finding the same bugs in apps that had been translated
by copy and paste. These are the checks we run on every delivery, as a free tool.

## License

MIT

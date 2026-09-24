# Projektregeln

- Open Source (MIT) für internationale Entwickler: Code, Kommentare, README und Ausgaben auf Englisch.
  Absprachen mit dem Nutzer und Commit-Nachrichten auf Deutsch.
- Nach jeder Änderung `uv run pytest -q`. Fehler sind blockierend.
- Die Beispielausgabe in der README ist echte Ausgabe (tests/test_readme.py). Wer Meldungen ändert, erzeugt sie neu:
  `cd tests/fixtures/app && uv run --project ../../.. strings-lint ios android fastlane/metadata/ja`
- Jede neue Regel bekommt einen absichtlichen Fehler in tests/fixtures/app und einen Eintrag in tests/test_app.py.
- Store-Grenzen stehen nur in src/strings_lint/fastlane.py, mit Quelle. Sie müssen mit
  lowest.localizationpipeline/src/l10n/store.py übereinstimmen.
- Platzhalter- und Pluralregeln stammen aus lowest.localizationpipeline; Fehler dort und hier gemeinsam beheben.
- Veröffentlichen (GitHub, PyPI) erst nach Freigabe durch den Nutzer, unter pseudonymem Konto.

## Arbeitsweise

- Es gibt nur `main`. Commit-Nachrichten beschreiben Absicht, Stand und offene Punkte so, dass ein
  anderer Agent ohne Rückfrage weiterarbeiten kann. Vor dem Start `git log --oneline -15` lesen.

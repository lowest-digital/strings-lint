from strings_lint import placeholders as p
from strings_lint.plurals import categories, one_is_exactly_one


def test_find():
    assert p.find("%1$@ has %lld items, %.2f € and %% off") == ["%1$@", "%lld", "%.2f", "%%"]
    assert p.find("Hi {name}, {{count}} new <b>messages</b>") == ["{name}", "{{count}}", "<b>", "</b>"]
    assert p.find("Save 50% off today") == []


def test_compare():
    assert p.compare("%d of %@", "%d von %@") == []
    assert p.compare("Hi %@, you have %ld", "Hallo %@") == ["missing %ld"]
    assert p.compare("%@ sent %d", "%d gesendet von %@")[0].startswith("order")
    assert p.compare("You completed %lld of %lld", "%2$lld個中%1$lld個") == []   # positions are fine
    assert p.compare("%lld days", "%1$lld Tage") == []
    assert p.compare("Hi", "Hallo {name}") == ["extra {name}"]


def test_ambiguous_repeats():
    assert p.ambiguous_repeats("You completed %lld of %lld")
    assert not p.ambiguous_repeats("%@ has %lld")
    assert not p.ambiguous_repeats("%1$lld of %2$lld")


def test_plural_categories():
    assert categories("pl") == ["one", "few", "many", "other"]
    assert categories("pt-BR") == ["one", "many", "other"]
    assert categories("zh-Hans") == ["other"]
    assert categories("key") is None
    assert one_is_exactly_one("de") and not one_is_exactly_one("ru")


def test_substitution_tokens_and_differences():
    assert p.find("%#@days@ and %arg hours") == ["%#@days@", "%arg"]
    assert p.positioned("%#@days@ of %lld and %lld") == "%#@days@ of %1$lld and %2$lld"
    assert p.differences("%arg days", "Tage") == [("missing", ["%arg"], [])]
    assert p.differences("%@ sent %d", "%d von %@") == [("order", ["%d", "%@"], ["%@", "%d"])]


def test_arg_before_cjk():
    # \b fails before 日 (a Unicode word character); %arg must still be one token
    assert p.find("%arg日") == ["%arg"] and p.compare("%arg days", "%arg日") == []

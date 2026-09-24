"""Find placeholders and compare them between source and translation."""

from __future__ import annotations

import re
from collections import Counter

# printf without the space flag, otherwise "50% off" would contain "% o"
PRINTF = r"%(?:\d+\$)?[-+0#]*(?:\d+|\*)?(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j|L)?[@dDiuUxXoOfFeEgGcCsSaAp]"
PATTERN = re.compile("|".join([
    r"%%",
    r"%#@\w+@",                        # stringsdict variables
    PRINTF,
    r"\{\{\s*[\w.-]+\s*\}\}",          # i18next, Handlebars
    r"\{[\w.-]+\}",                    # {name}, {0}
    r"</?[a-zA-Z][\w-]*(?:\s[^<>]*)?/?>",  # <b>, </b>, <a href="…">
]))


def find(text: str) -> list[str]:
    return PATTERN.findall(text)


def _unpositioned(token: str) -> bool:
    return token.startswith("%") and token != "%%" and not token.startswith("%#@") and not re.match(r"%\d+\$", token)


def positioned(text: str) -> str:
    """`%@ … %lld of %lld` → `%1$@ … %2$lld of %3$lld` when there are at least two unpositioned printf arguments."""
    tokens = [t for t in find(text) if t.startswith("%") and t != "%%" and not t.startswith("%#@")]
    if sum(map(_unpositioned, tokens)) < 2 or any(not _unpositioned(t) for t in tokens):
        return text
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        if not _unpositioned(m.group(0)):
            return m.group(0)
        n += 1
        return f"%{n}${m.group(0)[1:]}"

    return PATTERN.sub(repl, text)


def _positional(tokens: list[str]) -> bool:
    return any(re.match(r"%\d+\$", t) for t in tokens)


def _comparable(text: str, number: bool) -> list[str]:
    """Tokens for comparison; with `number` the unpositioned printf arguments are numbered first."""
    tokens = find(positioned(text) if number else text)
    printf = [t for t in tokens if t.startswith("%") and t != "%%" and not t.startswith("%#@")]
    if len(printf) == 1:
        tokens = [re.sub(r"^%1\$", "%", t) for t in tokens]
    return tokens


def compare(source: str, target: str) -> list[str]:
    """Human-readable problems; empty list means placeholders match."""
    q_raw, z_raw = find(source), find(target)
    qp = [x for x in q_raw if _unpositioned(x)]
    zp = [x for x in z_raw if _unpositioned(x)]
    if len(set(qp)) > 1 and Counter(qp) == Counter(zp) and qp != zp:
        return [f"order {' '.join(zp)} instead of {' '.join(qp)}; use positional specifiers (%1$@) to reorder"]
    # Number the arguments only when one side uses positions, so a plain "%@ … %ld" vs "%@" reports "missing %ld".
    number = _positional(q_raw) != _positional(z_raw)
    q, z = Counter(_comparable(source, number)), Counter(_comparable(target, number))
    problems = []
    if missing := q - z:
        problems.append("missing " + " ".join(missing.elements()))
    if extra := z - q:
        problems.append("extra " + " ".join(extra.elements()))
    return problems


def ambiguous_repeats(source: str) -> bool:
    """Two or more unpositioned arguments of the same type (e.g. `%lld of %lld`): a translation that swaps them
    cannot be detected. Worth a warning in the source."""
    qp = [x for x in find(source) if _unpositioned(x)]
    return len(qp) >= 2 and len(set(qp)) < len(qp)

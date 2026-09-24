"""The example output in the README must be real output."""

import os
import re
from pathlib import Path

from strings_lint.cli import main

ROOT = Path(__file__).parents[1]


def test_readme_example_is_real_output(capsys, monkeypatch):
    readme = (ROOT / "README.md").read_text()
    block = re.search(r"```console\n\$ strings-lint (.*?)\n(.*?)```", readme, re.S)
    args, expected = block.group(1).split(), block.group(2)
    monkeypatch.chdir(ROOT / "tests" / "fixtures" / "app")
    main(args)
    assert capsys.readouterr().out == expected
    assert os.getcwd().endswith("app")

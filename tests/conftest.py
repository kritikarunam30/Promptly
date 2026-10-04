import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)  # templates/ and static/ are mounted with relative paths

import assembly_helper.assembly_nlp as assembly_nlp


@pytest.fixture(autouse=True)
def no_language_tool(monkeypatch, request):
    """LanguageTool needs Java and a large download, so unit tests run without it.
    Tests marked `languagetool` use the real one."""
    if "languagetool" not in request.keywords:
        monkeypatch.setattr(assembly_nlp, "get_language_tool", lambda: None)


def pytest_configure(config):
    config.addinivalue_line("markers", "languagetool: needs Java + LanguageTool (set PROMPTLY_LT_TESTS=1)")

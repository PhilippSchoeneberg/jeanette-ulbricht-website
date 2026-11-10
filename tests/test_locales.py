"""Checks the translations in src/frontend/locales against the pages.

German is written directly in the HTML; locales/de.json must contain the same texts so that
switching back from another language restores them exactly.
"""

import json
import re
from html.parser import HTMLParser

import pytest

from src.backend.config import FRONTEND_DIR


LOCALES_DIR = FRONTEND_DIR / "locales"
PAGES = sorted(FRONTEND_DIR.glob("*.html"))
JS_FILES = sorted((FRONTEND_DIR / "js").glob("*.js"))
ATTRIBUTE_PREFIX = "data-i18n-"


def load(code):
    return json.loads((LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))


class TranslatableElements(HTMLParser):
    """Collects (key, German text) for data-i18n and (key, attribute value) for data-i18n-<attr>."""

    VOID = {"meta", "link", "img", "input", "br", "hr", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries = []   # (key, value, description)
        self._open = []     # stack of [tag, key, collected text]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name, key in attrs.items():
            if name.startswith(ATTRIBUTE_PREFIX):
                attribute = name[len(ATTRIBUTE_PREFIX):]
                self.entries.append((key, attrs.get(attribute), f"<{tag} {attribute}>"))
        if tag in self.VOID:
            return
        self._open.append([tag, attrs.get("data-i18n"), []])

    def handle_endtag(self, tag):
        while self._open:
            open_tag, key, text = self._open.pop()
            if key:
                self.entries.append((key, " ".join("".join(text).split()), f"<{open_tag}> text"))
            if open_tag == tag:
                break

    def handle_data(self, data):
        for item in self._open:
            item[2].append(data)


def page_entries(path):
    parser = TranslatableElements()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.entries


def test_locales_have_the_same_keys():
    assert set(load("de")) == set(load("en"))


@pytest.mark.parametrize("path", PAGES, ids=lambda p: p.name)
def test_page_keys_exist_and_match_german(path):
    de, en = load("de"), load("en")
    for key, value, where in page_entries(path):
        assert key in de, f"{path.name}: {key} ({where}) missing in de.json"
        assert key in en, f"{path.name}: {key} ({where}) missing in en.json"
        assert de[key] == value, f"{path.name}: {key} ({where}) differs from de.json: {value!r} != {de[key]!r}"


def test_keys_used_in_scripts_exist():
    de = load("de")
    used = set()
    for path in JS_FILES:
        used |= set(re.findall(r'"((?:form|menu|theme)_[a-z_]+)"', path.read_text(encoding="utf-8")))
    assert used, "no keys found in scripts"
    assert used <= set(de), f"missing in de.json: {sorted(used - set(de))}"


def test_no_unused_keys():
    used = set()
    for path in PAGES:
        used |= {key for key, _, _ in page_entries(path)}
    for path in JS_FILES:
        used |= set(re.findall(r'"([a-z0-9_]+)"', path.read_text(encoding="utf-8")))
    unused = set(load("de")) - used
    assert not unused, f"keys not used anywhere: {sorted(unused)}"

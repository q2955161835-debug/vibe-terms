from __future__ import annotations

from pathlib import Path

import yaml

from scripts.vibe_terms.config import HTML_LANG, LANGUAGE_NAMES, LOCALES


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
EXPECTED_LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru")


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def contains_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, key) for item in value)
    return False


def test_supported_locale_contract_excludes_removed_hindi():
    assert LOCALES == EXPECTED_LOCALES
    assert tuple(HTML_LANG) == EXPECTED_LOCALES
    assert tuple(LANGUAGE_NAMES) == EXPECTED_LOCALES
    assert tuple(load(CONTENT / "ui.yaml")) == EXPECTED_LOCALES


def test_removed_hindi_has_no_content_files_or_taxonomy_values():
    assert not list((CONTENT / "terms").glob("*/hi.yaml"))
    assert not list((CONTENT / "paths").glob("*/hi.yaml"))
    assert not contains_key(load(CONTENT / "glossaries" / "terminology.yaml"), "hi")

    for filename in ("domains.yaml", "lifecycle.yaml", "topics.yaml"):
        value = load(CONTENT / "taxonomy" / filename)
        assert not contains_key(value, "hi")

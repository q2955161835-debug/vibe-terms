from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from scripts.vibe_terms import BuildConfig, Catalog, load_catalog, validate_catalog


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")
CORE_EXAMPLES = {
    "prompt",
    "context-window",
    "ai-agent",
    "tool-calling",
    "retrieval-augmented-generation",
    "hallucination",
    "html",
    "css",
    "dom",
    "component",
    "state",
    "responsive-design",
    "accessibility",
    "api",
    "request",
    "http-status-code",
    "database",
    "authentication",
    "git",
    "testing",
}


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    return load_catalog(CONTENT, minimum_terms=500)


def test_stable_interfaces_are_frozen_and_importable(catalog: Catalog) -> None:
    config = BuildConfig(CONTENT, ROOT / "site", "", "", 500)
    with pytest.raises(FrozenInstanceError):
        config.minimum_terms = 12  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        catalog.locales = ("en",)  # type: ignore[misc]


def test_catalog_loads_500_terms_12_domains_and_eight_locales(catalog: Catalog) -> None:
    assert catalog.locales == LOCALES
    assert len(catalog.terms) == 500
    assert len(catalog.domains) == 12
    assert len({term["slug"] for term in catalog.terms}) == 500
    assert len({term["canonical_name"] for term in catalog.terms}) == 500


def test_normalized_terms_supply_rich_content_without_rewriting_yaml(catalog: Catalog) -> None:
    for term in catalog.terms:
        assert term["topics"]
        assert isinstance(term["lifecycle_stages"], list)
        assert term["example"]["mode"] in {
            "interactive",
            "stepper",
            "compare",
            "static",
        }
        for locale, localized in term["localized"].items():
            for field in (
                "short_definition",
                "mechanism",
                "why_it_matters",
                "project_example",
                "user_says",
                "ai_prompt_example",
                "common_mistake",
                "boundary",
                "sources",
                "exercise",
            ):
                assert localized[field], f"{term['slug']}/{locale} is missing {field}"
            exercise = localized["exercise"]
            option_ids = {option["id"] for option in exercise["options"]}
            assert exercise["answer"] in option_ids
            assert exercise["content_status"]


def test_only_the_twenty_core_terms_receive_enhanced_examples(catalog: Catalog) -> None:
    enhanced = {
        term["slug"]
        for term in catalog.terms
        if term["example"]["mode"] in {"interactive", "stepper", "compare"}
    }
    assert enhanced == CORE_EXAMPLES


def test_non_english_drafts_remain_explicitly_unreviewed(catalog: Catalog) -> None:
    for term in catalog.terms:
        assert term["localized"]["en"]["status"] == "published"
        for locale in LOCALES[1:]:
            localized = term["localized"][locale]
            assert localized["status"] == "draft"
            assert localized["exercise"]["content_status"] == "generated-from-local-draft"
            assert localized["sources"] == term["localized"]["en"]["sources"]


def test_internal_source_fallback_is_labeled_as_provenance(catalog: Catalog) -> None:
    legacy = next(term for term in catalog.terms if term["slug"] == "api")
    assert legacy["localized"]["en"]["sources"] == [
        {
            "title": "Canonical English Vibe Terms entry",
            "url": "/en/terms/api/",
            "kind": "internal-provenance",
        }
    ]


def test_validate_catalog_rejects_an_unknown_domain(catalog: Catalog) -> None:
    broken = dict(catalog.terms[0])
    broken["primary_domain"] = "does-not-exist"
    invalid = Catalog(
        catalog.locales,
        catalog.domains,
        catalog.topics,
        (broken, *catalog.terms[1:]),
        catalog.paths,
    )
    with pytest.raises(ValueError, match="unknown domain"):
        validate_catalog(invalid)

from __future__ import annotations

from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")
TRANSLATED_LOCALES = LOCALES[1:]

PLACEHOLDER_MARKERS = {
    "zh-cn": ("当前为待人工审校的草稿", "英文标准定义"),
    "zh-tw": ("目前為待人工審校的草稿", "英文標準定義"),
    "ja": ("現在の日本語本文はレビュー前の草稿", "英語の基準定義"),
    "ko": ("현재 한국어 본문은 검토 전 초안", "영어 기준 정의"),
    "de": ("noch nicht redigierter Entwurf", "Englische Referenzdefinition"),
    "ru": ("черновиком до редакторской проверки", "Эталонное определение на английском"),
    "hi": ("मानव समीक्षा से पहले का मसौदा", "अंग्रेज़ी मानक परिभाषा"),
}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_full_corpus_contract():
    terms = sorted(path for path in (CONTENT / "terms").iterdir() if path.is_dir())
    assert len(terms) == 500

    metas = [load(path / "meta.yaml") for path in terms]
    slugs = [meta["slug"] for meta in metas]
    canonical = [meta["canonical_name"] for meta in metas]
    assert len(set(slugs)) == 500
    assert len(set(canonical)) == 500

    for directory, meta in zip(terms, metas):
        assert directory.name == meta["slug"]
        for locale in LOCALES:
            localized = load(directory / f"{locale}.yaml")
            assert localized["source_content_version"] == meta["content_version"]
            assert localized["status"] in {"draft", "reviewed", "published"}

    path = load(CONTENT / "paths" / "zero-to-vibe.yaml")["terms"]
    assert len(path) == 500
    assert len(set(path)) == 500
    assert set(path) == set(slugs)


def test_vibehub_baseline_resolves_to_canonical_terms():
    slugs = {
        load(path / "meta.yaml")["slug"]
        for path in (CONTENT / "terms").iterdir()
        if path.is_dir()
    }
    baseline = load(CONTENT / "baselines" / "vibe-hub.yaml")
    mappings = baseline["mappings"]
    assert len(mappings) >= 250
    assert len({item["source_term"] for item in mappings}) == len(mappings)
    assert all(item["slug"] in slugs for item in mappings)


def test_non_english_corpus_has_no_generated_translation_placeholders():
    failures: dict[str, list[str]] = {locale: [] for locale in TRANSLATED_LOCALES}

    for directory in sorted(
        path for path in (CONTENT / "terms").iterdir() if path.is_dir()
    ):
        for locale in TRANSLATED_LOCALES:
            localized = load(directory / f"{locale}.yaml")
            visible = "\n".join(
                str(localized.get(field, ""))
                for field in (
                    "title",
                    "short_definition",
                    "analogy",
                    "mechanism",
                    "why_it_matters",
                    "project_example",
                    "ai_prompt_example",
                    "common_mistake",
                )
            )
            markers = PLACEHOLDER_MARKERS[locale]
            repeated = (
                bool(localized.get("mechanism"))
                and str(localized["short_definition"]).strip()
                == str(localized["mechanism"]).strip()
            ) or (
                bool(localized.get("project_example"))
                and str(localized["why_it_matters"]).strip()
                == str(localized["project_example"]).strip()
            )
            if repeated or any(marker in visible for marker in markers):
                failures[locale].append(directory.name)

    failures = {locale: slugs for locale, slugs in failures.items() if slugs}
    assert not failures, {
        locale: {"count": len(slugs), "examples": slugs[:10]}
        for locale, slugs in failures.items()
    }


def test_non_english_project_paths_have_no_english_draft_placeholders():
    failures: list[str] = []
    for path_dir in sorted(
        path for path in (CONTENT / "paths").iterdir() if path.is_dir()
    ):
        for locale in TRANSLATED_LOCALES:
            localized_path = path_dir / f"{locale}.yaml"
            if not localized_path.is_file():
                continue
            text = localized_path.read_text(encoding="utf-8")
            if "Draft —" in text or "not human reviewed" in text:
                failures.append(f"{path_dir.name}/{locale}")

    assert not failures, failures


def test_breadcrumb_uses_established_navigation_terms_in_every_locale():
    expected = {
        "zh-cn": "面包屑导航",
        "zh-tw": "麵包屑導覽",
        "ja": "パンくずリスト",
        "ko": "브레드크럼 내비게이션",
        "de": "Brotkrümelnavigation",
        "ru": "Хлебные крошки",
        "hi": "ब्रेडक्रम नेविगेशन",
    }
    directory = CONTENT / "terms" / "breadcrumb"
    assert {
        locale: load(directory / f"{locale}.yaml")["title"]
        for locale in TRANSLATED_LOCALES
    } == expected


def test_translated_prose_uses_the_target_writing_system():
    target_script = {
        "zh-cn": re.compile(r"[\u3400-\u9fff]"),
        "zh-tw": re.compile(r"[\u3400-\u9fff]"),
        "ja": re.compile(r"[\u3040-\u30ff]"),
        "ko": re.compile(r"[\uac00-\ud7a3]"),
        "ru": re.compile(r"[\u0400-\u04ff]"),
        "hi": re.compile(r"[\u0900-\u097f]"),
    }
    prose_fields = (
        "short_definition",
        "analogy",
        "mechanism",
        "why_it_matters",
        "project_example",
        "ai_prompt_example",
        "common_mistake",
    )
    failures: list[str] = []

    for directory in sorted(
        path for path in (CONTENT / "terms").iterdir() if path.is_dir()
    ):
        for locale, script in target_script.items():
            localized = load(directory / f"{locale}.yaml")
            for field in prose_fields:
                value = localized.get(field)
                if value and not script.search(str(value)):
                    failures.append(f"{directory.name}/{locale}/{field}")

    assert not failures, failures[:50]


def test_editorial_glossary_mirrors_term_titles_and_statuses():
    glossary = load(CONTENT / "glossaries" / "terminology.yaml")["terms"]
    by_slug = {entry["slug"]: entry for entry in glossary}
    term_dirs = sorted(
        path for path in (CONTENT / "terms").iterdir() if path.is_dir()
    )
    assert set(by_slug) == {path.name for path in term_dirs}

    failures: list[str] = []
    for directory in term_dirs:
        entry = by_slug[directory.name]
        canonical = load(directory / "meta.yaml")["canonical_name"]
        if entry["canonical"] != canonical:
            failures.append(f"{directory.name}/canonical")
        for locale in TRANSLATED_LOCALES:
            localized = load(directory / f"{locale}.yaml")
            if entry[locale] != localized["title"]:
                failures.append(f"{directory.name}/{locale}/title")
            if entry["status"][locale] != localized["status"]:
                failures.append(f"{directory.name}/{locale}/status")

    assert not failures, failures[:50]

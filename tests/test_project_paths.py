"""Contract checks for the three authored project-learning paths."""

from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
PATHS_ROOT = ROOT / "content" / "paths"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")
EXPECTED_CHAPTER_IDS = {
    "personal-site": (
        "project-goal",
        "audience-and-content",
        "information-architecture",
        "wireframe",
        "html-structure",
        "visual-system",
        "responsive-accessibility",
        "content-and-seo",
        "quality-check",
        "publish-static-site",
    ),
    "ai-app": (
        "problem-and-scope",
        "model-and-prompt",
        "conversation-ui",
        "application-state",
        "api-contract",
        "context-and-retrieval",
        "tool-safety",
        "evaluation",
        "error-and-observability",
        "release-and-feedback",
    ),
    "full-stack-app": (
        "product-scope",
        "architecture",
        "data-model",
        "api-design",
        "authentication",
        "frontend-flow",
        "validation-and-errors",
        "testing",
        "deployment",
        "iteration",
    ),
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_three_project_paths_have_complete_localized_chapters() -> None:
    """Catches a missing path, locale, chapter, or learner-facing checkpoint."""
    available_term_slugs = {
        item.name
        for item in (ROOT / "content" / "terms").iterdir()
        if item.is_dir() and (item / "meta.yaml").is_file()
    }

    assert available_term_slugs >= {"html", "api", "database", "testing"}
    assert {
        item.name
        for item in PATHS_ROOT.iterdir()
        if item.is_dir()
    } == set(EXPECTED_CHAPTER_IDS)

    for path_slug, expected_ids in EXPECTED_CHAPTER_IDS.items():
        path_dir = PATHS_ROOT / path_slug
        meta = load_yaml(path_dir / "meta.yaml")

        assert meta["id"] == f"path_{path_slug.replace('-', '_')}"
        assert meta["slug"] == path_slug
        assert meta["status"] == "published"
        assert meta["content_version"] >= 1
        assert 8 <= len(meta["chapters"]) <= 12
        assert tuple(chapter["id"] for chapter in meta["chapters"]) == expected_ids
        assert [chapter["order"] for chapter in meta["chapters"]] == list(
            range(1, len(expected_ids) + 1)
        )

        for chapter in meta["chapters"]:
            assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", chapter["id"])
            assert chapter["term_slugs"]
            assert set(chapter["term_slugs"]) <= available_term_slugs

        for locale in LOCALES:
            localized = load_yaml(path_dir / f"{locale}.yaml")
            assert localized["locale"] == locale
            assert localized["source_content_version"] == meta["content_version"]
            assert localized["status"] == (
                "published" if locale in {"en", "zh-cn", "zh-tw"} else "draft"
            )
            assert localized["title"].strip()
            assert localized["summary"].strip()
            assert tuple(chapter["id"] for chapter in localized["chapters"]) == expected_ids
            for chapter in localized["chapters"]:
                assert chapter["title"].strip()
                assert chapter["summary"].strip()
                assert chapter["outcome"].strip()
                assert chapter["checkpoint"].strip()

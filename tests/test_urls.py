from __future__ import annotations

import pytest

from scripts.vibe_terms.urls import UrlBuilder


def test_project_pages_prefix_internal_urls_but_not_origin_twice() -> None:
    urls = UrlBuilder(
        "https://q2955161835-debug.github.io/vibe-terms", "/vibe-terms"
    )
    assert urls.page("/zh-cn/terms/api/") == "/vibe-terms/zh-cn/terms/api/"
    assert urls.asset("assets/styles.css") == "/vibe-terms/assets/styles.css"
    assert (
        urls.absolute("/zh-cn/")
        == "https://q2955161835-debug.github.io/vibe-terms/zh-cn/"
    )


def test_root_host_uses_empty_base_path_and_supports_preview_urls() -> None:
    hosted = UrlBuilder("https://vibe-terms.example", "")
    preview = UrlBuilder("", "")
    assert hosted.page("/en/") == "/en/"
    assert hosted.absolute("/en/") == "https://vibe-terms.example/en/"
    assert preview.absolute("/en/") == "/en/"


@pytest.mark.parametrize(
    "base_path",
    (
        "vibe-terms",
        "/vibe-terms/",
        "https://example.test/vibe-terms",
        "/vibe-terms?preview=1",
        "/vibe-terms#preview",
    ),
)
def test_rejects_ambiguous_base_paths(base_path: str) -> None:
    with pytest.raises(ValueError, match="base_path"):
        UrlBuilder("", base_path)

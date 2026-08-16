from __future__ import annotations

import json
import hashlib
from html.parser import HTMLParser
from pathlib import Path

import pytest

from scripts.vibe_terms import BuildConfig, build_site, load_catalog


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru")


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_name = "src" if tag in {"script", "img"} else "href"
        if tag not in {"a", "link", "script", "img"}:
            return
        for name, value in attrs:
            if name == attr_name and value:
                self.urls.append(value)


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(CONTENT, minimum_terms=500)


@pytest.fixture(scope="module")
def generated_site(tmp_path_factory: pytest.TempPathFactory, catalog) -> Path:
    output = tmp_path_factory.mktemp("root-site")
    routes = build_site(BuildConfig(CONTENT, output, "", "", 500), catalog)
    assert len(routes) == len(set(routes))
    return output


def test_builds_all_primary_and_compatibility_routes(generated_site: Path, catalog) -> None:
    for locale in LOCALES:
        required = (
            generated_site / locale / "index.html",
            generated_site / locale / "terms" / "index.html",
            generated_site / locale / "knowledge" / "index.html",
            generated_site / locale / "paths" / "index.html",
            generated_site / locale / "practice" / "index.html",
            generated_site / locale / "learn" / "index.html",
        )
        assert all(path.is_file() for path in required)
        for domain in catalog.domains:
            assert (
                generated_site / locale / "knowledge" / domain["id"] / "index.html"
            ).is_file()
            assert (
                generated_site / locale / "categories" / domain["id"] / "index.html"
            ).is_file()
        for topic in catalog.topics:
            assert (
                generated_site
                / locale
                / "knowledge"
                / topic["domain"]
                / topic["id"]
                / "index.html"
            ).is_file()
        for path in catalog.paths:
            assert (
                generated_site / locale / "paths" / path["slug"] / "index.html"
            ).is_file()
            for chapter in path["chapters"]:
                assert (
                    generated_site
                    / locale
                    / "paths"
                    / path["slug"]
                    / chapter["id"]
                    / "index.html"
                ).is_file()


def test_every_locale_has_500_term_pages_and_static_indexes(
    generated_site: Path, catalog
) -> None:
    slugs = {term["slug"] for term in catalog.terms}
    for locale in LOCALES:
        actual = {
            page.parent.name
            for page in (generated_site / locale / "terms").glob("*/index.html")
        }
        assert actual == slugs
        terms = json.loads(
            (generated_site / "assets" / f"terms.{locale}.json").read_text(
                encoding="utf-8"
            )
        )
        exercises = json.loads(
            (generated_site / "assets" / f"exercises.{locale}.json").read_text(
                encoding="utf-8"
            )
        )
        search = json.loads(
            (generated_site / "assets" / f"search-index.{locale}.json").read_text(
                encoding="utf-8"
            )
        )
        assert len(terms) == len(exercises) == 500
        assert {item["type"] for item in search} == {"term", "topic", "path"}
        assert sum(item["type"] == "term" for item in search) == 500
        for item in search:
            assert item["title"] and item["summary"] and item["url"]
            assert item["type"] in {"term", "topic", "path"}


def test_rich_term_page_is_readable_without_javascript(generated_site: Path) -> None:
    html = (generated_site / "zh-cn" / "terms" / "api" / "index.html").read_text(
        encoding="utf-8"
    )
    for section in (
        "definition",
        "prerequisites",
        "mechanism",
        "why-it-matters",
        "project-example",
        "user-says",
        "boundary",
        "example",
        "exercise",
        "agent-prompt",
        "common-mistake",
        "sources",
        "project-paths",
    ):
        assert f'data-section="{section}"' in html
    assert "API" in html
    assert 'data-example-mode="stepper"' in html
    assert "data-example-root" in html
    assert "data-example-control" in html
    assert "data-example-state" in html
    assert "data-exercise" in html
    assert "data-exercise-payload" in html
    assert "data-exercise-feedback" in html
    assert "data-bookmark" in html
    assert 'class="term-pagination"' in html
    assert 'class="term-page-toolbar"' in html
    assert 'class="term-voice"' in html
    assert 'class="term-definition-summary"' in html
    assert 'class="example-journey"' in html
    assert html.count('class="example-stage') >= 4
    assert "data-copy-markdown" in html
    for localized_label in (
        "你可以这样说",
        "简短定义",
        "前置知识",
        "工作方式",
        "适用边界",
        "动态示例",
        "项目示例",
        "小练习",
        "项目路径",
        "来源与依据",
    ):
        assert localized_label in html
    assert "<h2>Short definition</h2>" not in html
    assert "<h2>Exercise</h2>" not in html


def test_term_page_keeps_visual_and_existing_learning_sections(
    generated_site: Path,
) -> None:
    """An authored visual explainer belongs before, never instead of, the legacy lesson."""
    html = (generated_site / "zh-cn" / "terms" / "css" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'data-section="visual-explainer"' in html
    assert 'data-explainer-pattern="code-result"' in html
    assert 'data-explainer-locale="zh-cn"' in html
    assert 'data-section="definition"' in html
    assert 'data-section="example"' in html
    assert 'data-section="exercise"' in html
    assert html.index('data-section="definition"') < html.index(
        'data-section="visual-explainer"'
    ) < html.index('data-section="example"')


def test_explainer_copy_falls_back_without_changing_page_locale(
    generated_site: Path,
) -> None:
    """Only explainer copy falls back; navigation stays in the requested locale."""
    chinese = (generated_site / "zh-tw" / "terms" / "css" / "index.html").read_text(
        encoding="utf-8"
    )
    japanese = (generated_site / "ja" / "terms" / "css" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'data-explainer-locale="zh-cn"' in chinese
    assert 'data-explainer-locale="en"' in japanese
    assert 'lang="zh-TW"' in chinese
    assert 'lang="ja"' in japanese


def test_root_is_a_discoverable_answer_first_landing_page(generated_site: Path) -> None:
    """The root route must be useful to people and crawlers, at any base path."""
    html = (generated_site / "index.html").read_text(encoding="utf-8")
    assert "500" in html and "12" in html and "42" in html and "3" in html
    assert "14 visual explanations" in html
    assert "What can I learn" in html
    assert 'rel="canonical" href="/"' in html
    assert 'hreflang="zh-CN" href="/zh-cn/"' in html
    assert 'name="twitter:card"' in html
    assert '"@type": "WebSite"' in html
    assert '"@type": "DefinedTermSet"' in html
    assert '"@type": "FAQPage"' in html
    assert "AnswerDotAI/llms-txt format (Apache-2.0)" in html
    assert "Schema.org vocabulary" in html
    assert (generated_site / "llms.txt").is_file()
    llms = (generated_site / "llms.txt").read_text(encoding="utf-8")
    assert "AnswerDotAI/llms-txt" in llms
    assert "/en/terms/css/" in llms
    assert "/en/knowledge/" in llms and "/en/paths/" in llms
    assert "Sitemap: /sitemap.xml" in (generated_site / "robots.txt").read_text(
        encoding="utf-8"
    )


def test_root_social_image_is_packaged_and_scoped_to_the_landing_page(
    generated_site: Path,
) -> None:
    """A missing or doubly-prefixed social card must fail before deployment."""
    source = ROOT / "web" / "og.png"
    copied = generated_site / "og.png"
    root = (generated_site / "index.html").read_text(encoding="utf-8")
    term = (generated_site / "en" / "terms" / "css" / "index.html").read_text(
        encoding="utf-8"
    )

    assert copied.is_file()
    assert hashlib.sha256(copied.read_bytes()).digest() == hashlib.sha256(
        source.read_bytes()
    ).digest()
    assert '<meta property="og:image" content="/og.png"/>' in root
    assert '<meta property="og:image:width" content="1731"/>' in root
    assert '<meta property="og:image:height" content="909"/>' in root
    assert '<meta property="og:image:alt" content="Vibe Terms visual explainer card"/>' in root
    assert '<meta name="twitter:image" content="/og.png"/>' in root
    assert '<meta name="twitter:image:alt" content="Vibe Terms visual explainer card"/>' in root
    assert "og:image" not in term
    assert "twitter:image" not in term


def test_term_metadata_uses_localized_labels_and_omits_empty_aliases(
    generated_site: Path,
) -> None:
    html = (
        generated_site / "zh-cn" / "terms" / "breadcrumb" / "index.html"
    ).read_text(encoding="utf-8")
    assert "面包屑导航" in html
    assert ">UI/UX 与无障碍</a>" in html
    assert '<span class="term-field">入门</span>' in html
    assert '<span class="term-field">设计体验</span>' in html
    assert '<span class="term-field">ui-ux</span>' not in html
    assert '<span class="term-field">beginner</span>' not in html
    assert '<span class="term-field">design</span>' not in html
    assert "别名: —" not in html


def test_runtime_search_labels_are_localized_by_the_static_page(
    generated_site: Path,
) -> None:
    html = (generated_site / "ja" / "index.html").read_text(encoding="utf-8")
    assert 'data-search-term-label="用語"' in html
    assert 'data-search-topic-label="トピック"' in html
    assert 'data-search-path-label="プロジェクトの流れ"' in html
    assert 'data-search-empty="一致する用語がありません。"' in html
    assert '"invalid_json":"選択したファイルは有効なJSONではありません。"' in html
    assert '"confirm_clear":"消去を確認する"' in html
    assert '"clear_failed":"ローカルデータを消去できませんでした。"' in html

    app = (generated_site / "assets" / "app.js").read_text(encoding="utf-8")
    assert "root.dataset.searchTopicLabel" in app
    assert "No matching term, topic, or path." not in app
    assert "platformMessage('invalid_json'" in app
    assert "platformMessage('confirm_clear'" in app
    assert "platformMessage('clear_failed'" in app


def test_home_is_a_clear_domain_topic_and_term_card_explorer(generated_site: Path) -> None:
    html = (generated_site / "zh-cn" / "index.html").read_text(encoding="utf-8")
    assert 'class="explorer-tabs"' in html
    assert 'class="topic-sidebar"' in html
    assert 'class="term-card-grid"' in html
    assert 'class="term-card-example"' in html
    assert 'class="term-card-quote"' in html
    assert "前端工程 VibeCoding 术语" in html
    assert 'href="/assets/clarity.css"' in html
    assert "从一句想法，走到真正上线。" not in html


def test_canonical_name_is_not_repeated_when_localized_title_already_contains_it(
    generated_site: Path,
) -> None:
    home = (generated_site / "zh-cn" / "index.html").read_text(encoding="utf-8")
    detail = (
        generated_site / "zh-cn" / "terms" / "border-radius" / "index.html"
    ).read_text(encoding="utf-8")
    terms = (generated_site / "zh-cn" / "terms" / "index.html").read_text(
        encoding="utf-8"
    )

    assert "<strong>圆角半径（Border Radius）</strong><span>Border Radius</span>" not in home
    assert "<strong>圆角半径（Border Radius）</strong><span>Border Radius</span>" not in detail
    assert "<strong>圆角半径（Border Radius）</strong><small>Border Radius</small>" not in terms


def test_static_example_pages_do_not_render_inert_controls(generated_site: Path) -> None:
    html = (
        generated_site / "en" / "terms" / "a-b-test" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-example-mode="static"' in html
    assert "data-example-control" not in html


def test_project_path_and_practice_chrome_are_localized(generated_site: Path) -> None:
    chapter = (
        generated_site
        / "zh-cn"
        / "paths"
        / "personal-site"
        / "project-goal"
        / "index.html"
    ).read_text(encoding="utf-8")
    for label in ("学习成果", "术语", "阶段检查", "在本地标记完成"):
        assert label in chapter
    assert "<h2>Outcome</h2>" not in chapter

    practice = (
        generated_site / "zh-cn" / "practice" / "index.html"
    ).read_text(encoding="utf-8")
    for label in ("<h1>练习</h1>", "练习范围", "本地数据", "导出", "导入", "清除本地数据"):
        assert label in practice
    assert '"open_exercise":"打开练习"' in practice
    assert "<h1>Practice</h1>" not in practice


def test_global_header_search_and_mobile_dialog_exist_on_every_page_kind(
    generated_site: Path,
) -> None:
    pages = (
        generated_site / "index.html",
        generated_site / "en" / "index.html",
        generated_site / "en" / "terms" / "index.html",
        generated_site / "en" / "terms" / "api" / "index.html",
        generated_site / "en" / "knowledge" / "index.html",
        generated_site / "en" / "knowledge" / "backend-apis" / "index.html",
        generated_site / "en" / "paths" / "index.html",
        generated_site / "en" / "paths" / "personal-site" / "index.html",
        generated_site / "en" / "practice" / "index.html",
    )
    for page in pages:
        html = page.read_text(encoding="utf-8")
        assert "data-global-search" in html, page
        assert "data-search-input" in html, page
        assert "data-search-results" in html, page
        assert "data-search-open" in html, page
        assert 'dialog id="mobile-search-dialog"' in html, page
        assert 'data-search-index="/assets/search-index.en.json"' in html, page


def test_draft_pages_are_noindex_without_claiming_review(generated_site: Path) -> None:
    english = (generated_site / "en" / "terms" / "api" / "index.html").read_text(
        encoding="utf-8"
    )
    chinese = (
        generated_site / "zh-cn" / "terms" / "api" / "index.html"
    ).read_text(encoding="utf-8")
    assert '<meta name="robots" content="index,follow"' in english
    assert '<meta name="robots" content="noindex,follow"' in chinese
    assert "待审校" in chinese
    assert "human reviewed" not in chinese.lower()


def test_root_build_has_complete_local_links(generated_site: Path) -> None:
    missing: list[tuple[str, str]] = []
    for page in generated_site.rglob("*.html"):
        parser = ResourceParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for url in parser.urls:
            if not url.startswith("/") or url.startswith("//"):
                continue
            path = url.split("#", 1)[0].split("?", 1)[0]
            target = generated_site / path.lstrip("/")
            if path.endswith("/"):
                target /= "index.html"
            if not target.exists():
                missing.append((str(page.relative_to(generated_site)), url))
    assert missing == []


def test_project_base_path_applies_to_html_manifest_and_sitemap(
    tmp_path: Path, catalog
) -> None:
    output = tmp_path / "project-site"
    build_site(
        BuildConfig(
            CONTENT,
            output,
            "https://q2955161835-debug.github.io/vibe-terms",
            "/vibe-terms",
            500,
        ),
        catalog,
    )
    home = (output / "en" / "index.html").read_text(encoding="utf-8")
    root = (output / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((output / "manifest.webmanifest").read_text(encoding="utf-8"))
    sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
    assert 'href="/vibe-terms/en/terms/"' in home
    assert 'src="/vibe-terms/assets/core.js"' in home
    assert 'href="/vibe-terms/assets/explainers.css"' in root
    assert 'src="/vibe-terms/assets/explainers.js"' in root
    assert 'rel="canonical" href="https://q2955161835-debug.github.io/vibe-terms/"' in root
    assert (
        '<meta property="og:image" '
        'content="https://q2955161835-debug.github.io/vibe-terms/og.png"/>'
        in root
    )
    assert "vibe-terms/vibe-terms/og.png" not in root
    assert 'hreflang="zh-CN" href="https://q2955161835-debug.github.io/vibe-terms/zh-cn/"' in root
    assert 'href="/assets/' not in home
    assert manifest["start_url"] == "/vibe-terms/"
    assert manifest["icons"][0]["src"] == "/vibe-terms/assets/logo.svg"
    assert (
        "https://q2955161835-debug.github.io/vibe-terms/en/terms/api/" in sitemap
    )
    assert "/vibe-terms/vibe-terms/" not in sitemap
    assert "Sitemap: https://q2955161835-debug.github.io/vibe-terms/sitemap.xml" in (
        output / "robots.txt"
    ).read_text(encoding="utf-8")
    llms = (output / "llms.txt").read_text(encoding="utf-8")
    assert "/vibe-terms/en/terms/css/" in llms
    assert "/vibe-terms/license/" in llms


def test_seo_and_deployment_files_use_the_url_builder(generated_site: Path) -> None:
    home = (generated_site / "en" / "index.html").read_text(encoding="utf-8")
    term = (generated_site / "en" / "terms" / "api" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'hreflang="zh-CN" href="/zh-cn/"' in home
    assert 'hreflang="x-default" href="/"' in home
    assert 'rel="canonical" href="/en/terms/api/"' in term
    assert '"@type": "DefinedTerm"' in term
    assert (
        'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        in (generated_site / "sitemap.xml").read_text(encoding="utf-8")
    )
    for relative in (
        "manifest.webmanifest",
        "robots.txt",
        "sitemap.xml",
        "404.html",
        ".nojekyll",
        "build-info.json",
        "assets/logo.svg",
        "assets/core.js",
        "assets/app.js",
        "assets/examples.js",
        "assets/explainers.js",
        "assets/styles.css",
        "assets/explainers.css",
        "assets/icons/code.svg",
        "llms.txt",
    ):
        assert (generated_site / relative).is_file(), relative


def test_generated_site_has_no_account_or_server_dependency(generated_site: Path) -> None:
    generated = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in generated_site.rglob("*")
        if path.is_file() and path.suffix in {".html", ".js", ".json"}
    ).lower()
    for forbidden in ("supabase", 'href="/login', "oauth/callback"):
        assert forbidden not in generated

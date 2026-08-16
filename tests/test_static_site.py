from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path

import pytest

from scripts.vibe_terms import BuildConfig, build_site, load_catalog


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")


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


def test_static_example_pages_do_not_render_inert_controls(generated_site: Path) -> None:
    html = (
        generated_site / "en" / "terms" / "a-b-test" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'data-example-mode="static"' in html
    assert "data-example-control" not in html


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
    assert "Draft" in chinese or "草稿" in chinese
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
    manifest = json.loads((output / "manifest.webmanifest").read_text(encoding="utf-8"))
    sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
    assert 'href="/vibe-terms/en/terms/"' in home
    assert 'src="/vibe-terms/assets/core.js"' in home
    assert 'href="/assets/' not in home
    assert manifest["start_url"] == "/vibe-terms/"
    assert manifest["icons"][0]["src"] == "/vibe-terms/assets/logo.svg"
    assert (
        "https://q2955161835-debug.github.io/vibe-terms/en/terms/api/" in sitemap
    )
    assert "/vibe-terms/vibe-terms/" not in sitemap


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
        "assets/styles.css",
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

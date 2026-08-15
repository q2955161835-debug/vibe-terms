from __future__ import annotations

import json
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {"a", "link", "script"}:
            return
        attr_name = "href" if tag in {"a", "link"} else "src"
        for name, value in attrs:
            if name == attr_name and value:
                self.links.append(value)


def local_target(url: str) -> Path | None:
    if not url.startswith("/") or url.startswith("//"):
        return None
    path = url.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return SITE / "index.html"
    target = SITE / path.lstrip("/")
    if path.endswith("/"):
        target /= "index.html"
    return target


class StaticSiteContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            ["python3", "scripts/build_static_site.py"],
            cwd=ROOT,
            check=True,
            text=True,
        )
        cls.term_slugs = sorted(
            path.name for path in (CONTENT / "terms").iterdir() if path.is_dir()
        )

    def test_builds_eight_locales_and_every_term_route(self) -> None:
        self.assertEqual(len(self.term_slugs), 12)
        for locale in LOCALES:
            self.assertTrue((SITE / locale / "index.html").is_file())
            self.assertTrue((SITE / locale / "learn" / "index.html").is_file())
            for slug in self.term_slugs:
                self.assertTrue((SITE / locale / "terms" / slug / "index.html").is_file())

    def test_repository_has_open_source_and_deployment_metadata(self) -> None:
        required = (
            ROOT / "LICENSE",
            ROOT / "LICENSE-CONTENT",
            ROOT / "CONTRIBUTING.md",
            ROOT / "requirements.txt",
            ROOT / "docs" / "deployment.md",
            ROOT / "scripts" / "verify_public_site.sh",
        )
        for path in required:
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

        self.assertIn("Apache License", (ROOT / "LICENSE").read_text(encoding="utf-8"))
        self.assertIn("CC BY-SA 4.0", (ROOT / "LICENSE-CONTENT").read_text(encoding="utf-8"))
        self.assertIn("PyYAML==6.0.3", (ROOT / "requirements.txt").read_text(encoding="utf-8"))
        verify_script = (ROOT / "scripts" / "verify_public_site.sh").read_text(encoding="utf-8")
        self.assertIn("tests/test_render_harness.py", verify_script)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("SITE_URL", readme)
        self.assertIn("site/", readme)
        self.assertIn("no login", readme.lower())

    def test_build_emits_static_host_and_seo_files(self) -> None:
        required = (
            SITE / "manifest.webmanifest",
            SITE / "robots.txt",
            SITE / "sitemap.xml",
            SITE / "404.html",
            SITE / "assets" / "logo.svg",
            SITE / "assets" / "core.js",
        )
        for path in required:
            self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")

    def test_preview_build_does_not_link_to_an_unconfirmed_repository(self) -> None:
        home = (SITE / "en" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("github.com/q2955161835-debug/vibe-terms", home)

    def test_root_page_has_a_no_script_language_fallback(self) -> None:
        root_html = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("<noscript", root_html)
        for locale in LOCALES:
            self.assertIn(f'href="/{locale}/"', root_html)

    def test_home_search_is_accessible_and_submit_driven(self) -> None:
        home = (SITE / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<form id="home-search-form"', home)
        self.assertIn('role="combobox"', home)
        self.assertIn('aria-controls="search-results"', home)
        self.assertIn('aria-expanded="false"', home)
        self.assertIn('aria-live="polite"', home)
        self.assertIn('type="submit"', home)

    def test_runtime_strings_are_localized_in_page_data(self) -> None:
        app_js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        for english_literal in ("No results", "Done for today", "Copied"):
            self.assertNotIn(english_literal, app_js)
        self.assertIn("homeSearchForm.addEventListener('submit'", app_js)
        for locale in LOCALES:
            home = (SITE / locale / "index.html").read_text(encoding="utf-8")
            learn = (SITE / locale / "learn" / "index.html").read_text(encoding="utf-8")
            self.assertIn('id="ui-messages"', home)
            self.assertIn('id="ui-messages"', learn)

    def test_learning_state_is_local_and_scheduled(self) -> None:
        app_js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("indexedDB", app_js)
        self.assertIn("nextReviewAt", app_js)
        self.assertIn("dailySessionDate", app_js)
        generated = "\n".join(
            p.read_text(encoding="utf-8")
            for p in SITE.rglob("*")
            if p.is_file() and p.suffix in {".html", ".js"}
        ).lower()
        for forbidden in ("supabase", "/login", "oauth"):
            self.assertNotIn(forbidden, generated)

    def test_category_cards_link_to_real_localized_routes(self) -> None:
        taxonomy = yaml.safe_load(
            (CONTENT / "taxonomy" / "domains.yaml").read_text(encoding="utf-8")
        )["domains"]
        for locale in LOCALES:
            home = (SITE / locale / "index.html").read_text(encoding="utf-8")
            for domain in taxonomy:
                domain_id = domain["id"]
                route = f"/{locale}/categories/{domain_id}/"
                self.assertIn(f'href="{route}"', home)
                self.assertTrue(
                    (SITE / locale / "categories" / domain_id / "index.html").is_file()
                )

    def test_build_copies_runtime_assets_from_source(self) -> None:
        for filename in ("core.js", "app.js", "styles.css", "logo.svg"):
            source = ROOT / "web" / filename
            built = SITE / "assets" / filename
            self.assertEqual(
                built.read_bytes(),
                source.read_bytes(),
                f"generated asset drifted from web/{filename}",
            )


    def test_public_surfaces_have_complete_layout_styles(self) -> None:
        css = (SITE / "assets" / "styles.css").read_text(encoding="utf-8")
        for selector in (
            ".language-grid",
            ".language-card",
            ".language-card.recommended",
            ".gateway-brand",
            ".browser-recommendation",
            ".category-hero",
            ".category-list",
            ".learn-analogy",
            ".storage-note",
        ):
            self.assertIn(selector, css, f"missing layout style for {selector}")

    def test_pages_load_core_before_app_and_use_script_driven_locale_switching(self) -> None:
        home = (SITE / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-locale-picker', home)
        self.assertNotIn('onchange=', home)
        core_position = home.index('src="/assets/core.js"')
        app_position = home.index('src="/assets/app.js"')
        self.assertLess(core_position, app_position)

    def test_source_link_is_omitted_until_a_public_repository_is_configured(self) -> None:
        home = (SITE / "en" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("github.com/q2955161835-debug/vibe-terms", home)
        self.assertNotIn(">Source code</a>", home)

    def test_language_alternates_use_bcp47_codes_and_x_default(self) -> None:
        home = (SITE / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('hreflang="zh-CN"', home)
        self.assertIn('hreflang="zh-TW"', home)
        self.assertIn('hreflang="x-default" href="/"', home)
        self.assertNotIn('hreflang="zh-cn"', home)

    def test_term_pages_include_defined_term_structured_data(self) -> None:
        term_page = SITE / "en" / "terms" / "api" / "index.html"
        html = term_page.read_text(encoding="utf-8")
        self.assertIn('type="application/ld+json"', html)
        self.assertIn('"@type": "DefinedTerm"', html)
        self.assertIn('"name": "API"', html)

    def test_every_local_asset_and_page_link_resolves(self) -> None:
        missing: list[tuple[str, str]] = []
        for page in SITE.rglob("*.html"):
            parser = LinkParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for link in parser.links:
                target = local_target(link)
                if target is not None and not target.exists():
                    missing.append((str(page.relative_to(SITE)), link))
        self.assertEqual(missing, [])

    def test_search_indexes_have_unique_complete_records(self) -> None:
        for locale in LOCALES:
            payload = json.loads(
                (SITE / "assets" / f"terms.{locale}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(payload), 12)
            slugs = [row["slug"] for row in payload]
            self.assertEqual(len(slugs), len(set(slugs)))
            for row in payload:
                for key in (
                    "slug",
                    "canonical_name",
                    "title",
                    "short_definition",
                    "primary_domain",
                    "domain_title",
                    "learning_order",
                ):
                    self.assertTrue(row[key])

    def test_non_english_localizations_do_not_ship_generic_english_placeholders(self) -> None:
        placeholders = (
            "Think of it as a practical building block in the software workflow.",
            "Knowing this term helps you tell an AI exactly which part of the product you mean.",
            "Explain the change you plan to make, the files involved, and how I can verify it before editing.",
            "Using the term loosely without checking which layer of the system is actually involved.",
        )
        for slug in self.term_slugs:
            term_dir = CONTENT / "terms" / slug
            english = yaml.safe_load((term_dir / "en.yaml").read_text(encoding="utf-8"))
            for locale in LOCALES[1:]:
                localized = yaml.safe_load((term_dir / f"{locale}.yaml").read_text(encoding="utf-8"))
                combined = "\n".join(str(localized.get(field, "")) for field in (
                    "analogy", "why_it_matters", "ai_prompt_example", "common_mistake"
                ))
                for placeholder in placeholders:
                    self.assertNotIn(placeholder, combined, f"{slug}/{locale} still contains an English placeholder")
                for field in ("analogy", "why_it_matters", "common_mistake"):
                    self.assertNotEqual(
                        localized[field],
                        english[field],
                        f"{slug}/{locale} did not localize {field}",
                    )

    def test_content_corpus_has_all_locales_and_version_metadata(self) -> None:
        for slug in self.term_slugs:
            term_dir = CONTENT / "terms" / slug
            meta = yaml.safe_load((term_dir / "meta.yaml").read_text(encoding="utf-8"))
            self.assertEqual(meta["slug"], slug)
            self.assertGreaterEqual(meta["content_version"], 1)
            for locale in LOCALES:
                path = term_dir / f"{locale}.yaml"
                self.assertTrue(path.is_file())
                content = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIn(content["status"], {"draft", "reviewed", "published"})
                self.assertEqual(content["source_content_version"], meta["content_version"])


if __name__ == "__main__":
    unittest.main()

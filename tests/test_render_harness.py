from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WEB = ROOT / "web"


def _launch_browser(playwright):
    launch_options: dict[str, object] = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if executable_path:
        launch_options["executable_path"] = executable_path
    elif Path("/usr/bin/chromium").is_file():
        launch_options["executable_path"] = "/usr/bin/chromium"
    return playwright.chromium.launch(**launch_options)


def _inline_document(relative_path: str) -> str:
    html = (SITE / relative_path).read_text(encoding="utf-8")
    css = "\n".join(
        (WEB / name).read_text(encoding="utf-8")
        for name in ("styles.css", "clarity.css", "explainers.css")
    )
    logo = quote((WEB / "logo.svg").read_text(encoding="utf-8"))

    html = re.sub(r'<link\b[^>]*>', '', html)
    html = re.sub(
        r'<script\s+src="/assets/(?:core|examples|explainers|app)\.js"\s+defer></script>',
        '',
        html,
    )
    html = html.replace('src="/assets/logo.svg"', f'src="data:image/svg+xml,{logo}"')
    return html.replace('</head>', f'<style>{css}</style></head>')


def _install_memory_storage(page: Page) -> None:
    page.evaluate(
        """
        () => {
          const values = new Map();
          const storage = {
            getItem(key) { return values.has(String(key)) ? values.get(String(key)) : null; },
            setItem(key, value) { values.set(String(key), String(value)); },
            removeItem(key) { values.delete(String(key)); },
            clear() { values.clear(); },
            key(index) { return Array.from(values.keys())[index] ?? null; },
            get length() { return values.size; },
            dump() { return Object.fromEntries(values); },
          };
          Object.defineProperty(window, 'localStorage', { value: storage, configurable: true });
        }
        """
    )


def _mount(page: Page, relative_path: str, locale: str) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text)
        if message.type == "error"
        else None,
    )
    _install_memory_storage(page)
    page.set_content(_inline_document(relative_path), wait_until="domcontentloaded")
    terms = json.loads(
        (SITE / "assets" / f"terms.{locale}.json").read_text(encoding="utf-8")
    )
    search = json.loads(
        (SITE / "assets" / f"search-index.{locale}.json").read_text(encoding="utf-8")
    )
    page.evaluate(
        "payload => { window.fetch = async url => ({ ok: true, status: 200, json: async () => String(url).includes('search-index') ? payload.search : payload.terms }); }",
        {"terms": terms, "search": search},
    )
    page.add_script_tag(content=(WEB / "core.js").read_text(encoding="utf-8"))
    page.add_script_tag(content=(WEB / "examples.js").read_text(encoding="utf-8"))
    page.add_script_tag(content=(WEB / "explainers.js").read_text(encoding="utf-8"))
    page.evaluate("window.VibeExplainers.mountAll(document)")
    page.add_script_tag(content=(WEB / "app.js").read_text(encoding="utf-8"))
    return errors


def test_home_search_theme_and_mobile_layout_without_http_navigation() -> None:
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = _mount(page, "zh-cn/index.html", "zh-cn")

            assert page.locator("h1").inner_text() == "前端工程 VibeCoding 术语"
            field = page.locator(".desktop-search [data-search-input]")
            field.fill("Authentication")
            page.wait_for_selector(".desktop-search [data-search-results] a")
            first = page.locator(".desktop-search [data-search-results] a").first
            base_path = page.locator("html").get_attribute("data-base-path") or ""
            assert first.get_attribute("href") == f"{base_path}/zh-cn/terms/authentication/"
            field.press("ArrowDown")
            assert field.get_attribute("aria-activedescendant") == "global-search-term-0"
            assert first.get_attribute("aria-selected") == "true"

            button = page.locator(".theme-toggle")
            button.click()
            selected_theme = page.locator("html").get_attribute("data-theme")
            assert selected_theme in {"light", "dark"}
            assert page.evaluate("localStorage.getItem('vibe-theme')") == selected_theme
            assert button.get_attribute("aria-label")
            assert errors == []

            mobile = browser.new_page(viewport={"width": 390, "height": 844})
            _mount(mobile, "zh-cn/index.html", "zh-cn")
            dimensions = mobile.evaluate(
                "() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth })"
            )
            assert dimensions["scrollWidth"] <= dimensions["innerWidth"]
            assert mobile.locator(".term-card").count() >= 3
            assert mobile.locator(".desktop-search [data-search-input]").is_visible()
            assert not mobile.locator(".brand span").is_visible()
        finally:
            browser.close()


def test_guest_learning_uses_local_fallback_without_login() -> None:
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            page = browser.new_page(viewport={"width": 1100, "height": 900})
            errors = _mount(page, "zh-cn/learn/index.html", "zh-cn")

            page.locator("#daily-count").fill("2")
            page.locator("#daily-count").blur()
            page.locator("#start-learning").click()
            page.wait_for_selector(".learn-title")
            assert page.locator("#learn-progress").inner_text() == "0 / 2"
            page.locator(".reveal").click()
            assert page.locator(".learn-analogy").is_visible()
            first_title = page.locator(".learn-title").inner_text()
            page.locator("[data-rating='mastered']").click()
            page.wait_for_function(
                "document.querySelector('#learn-progress').textContent === '1 / 2'"
            )
            assert page.locator(".learn-title").inner_text() != first_title

            rows = page.evaluate(
                "JSON.parse(localStorage.getItem('vibe-terms-progress-v1') || '[]')"
            )
            reviewed = next(row for row in rows if row.get("rating") == "mastered")
            assert reviewed["nextReviewAt"] > reviewed["lastReviewedAt"]
            assert reviewed["introducedOn"]
            assert reviewed["dailySessionDate"]
            assert page.locator(".storage-note").is_visible()
            assert errors == []
        finally:
            browser.close()


def test_all_locales_render_home_and_term_pages_without_horizontal_overflow() -> None:
    locales = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru")
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            for locale in locales:
                home = browser.new_page(viewport={"width": 390, "height": 844})
                errors = _mount(home, f"{locale}/index.html", locale)
                dimensions = home.evaluate(
                    "() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth })"
                )
                assert dimensions["scrollWidth"] <= dimensions["innerWidth"], locale
                assert home.locator(".term-card").count() >= 3
                assert home.locator(".desktop-search [data-search-input]").is_visible()
                assert errors == []
                home.close()

                term = browser.new_page(viewport={"width": 390, "height": 844})
                errors = _mount(term, f"{locale}/terms/authentication/index.html", locale)
                dimensions = term.evaluate(
                    "() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth })"
                )
                assert dimensions["scrollWidth"] <= dimensions["innerWidth"], locale
                assert term.locator(".term-heading h1").is_visible()
                assert term.locator(".term-definition-summary").inner_text().strip()
                assert errors == []
                term.close()
        finally:
            browser.close()


def test_visual_explainer_mounts_the_css_fallback_without_http_navigation() -> None:
    """A missing explainer runtime would leave the selected state and result unchanged."""
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            errors = _mount(page, "zh-tw/terms/css/index.html", "zh-tw")
            root = page.locator("[data-visual-explainer]")

            assert root.get_attribute("data-explainer-locale") == "zh-cn"
            root.locator('[data-explainer-state-control="override"]').click()
            assert root.locator('[aria-pressed="true"]').get_attribute(
                "data-explainer-state-control"
            ) == "override"
            assert (
                root.locator('[data-explainer-node="computed-color"] code').inner_text()
                == "#db2777"
            )
            assert root.locator(".visual-transcript-item").count() == 3
            assert errors == []
        finally:
            browser.close()

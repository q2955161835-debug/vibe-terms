from __future__ import annotations

import os

from playwright.sync_api import sync_playwright


def _browser():
    playwright = sync_playwright().start()
    executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    launch_options = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    if executable_path:
        launch_options["executable_path"] = executable_path
    browser = playwright.chromium.launch(**launch_options)
    return playwright, browser


def test_search_keyboard_and_locale_switch(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        errors: list[str] = []
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(f"{site_url}/zh-cn/", wait_until="networkidle")
        field = page.locator("#home-search")
        field.fill("Auth")
        page.wait_for_selector("#search-results a")
        field.press("ArrowDown")
        assert field.get_attribute("aria-activedescendant")
        assert page.locator("#search-results [role='option']").first.get_attribute("aria-selected") == "true"
        field.press("Enter")
        page.wait_for_url("**/zh-cn/terms/authentication/")
        page.locator(".locale-picker").select_option("de")
        page.wait_for_url("**/de/terms/authentication/")
        assert errors == []
    finally:
        browser.close()
        playwright.stop()


def test_theme_cycle_persists(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto(f"{site_url}/en/", wait_until="networkidle")
        button = page.locator(".theme-toggle")
        button.click()
        first = page.locator("html").get_attribute("data-theme")
        assert first in {"light", "dark"}
        page.reload(wait_until="networkidle")
        assert page.locator("html").get_attribute("data-theme") == first
        assert button.get_attribute("aria-label")
    finally:
        browser.close()
        playwright.stop()


def test_guest_learning_persists_without_login(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{site_url}/zh-cn/learn/", wait_until="networkidle")
        page.locator("#daily-count").fill("2")
        page.locator("#daily-count").blur()
        page.locator("#start-learning").click()
        page.wait_for_selector(".learn-title")
        assert page.locator("#learn-progress").inner_text() == "0 / 2"
        page.locator(".reveal").click()
        assert page.locator(".learn-analogy").is_visible()
        first_title = page.locator(".learn-title").inner_text()
        page.locator("[data-rating='mastered']").click()
        page.wait_for_timeout(100)
        assert page.locator("#learn-progress").inner_text() == "1 / 2"
        stored = page.evaluate("""
          async () => {
            const request = indexedDB.open('vibe-terms-guest-v1', 1);
            const db = await new Promise((resolve, reject) => {
              request.onsuccess = () => resolve(request.result);
              request.onerror = () => reject(request.error);
            });
            const tx = db.transaction('progress', 'readonly');
            const all = tx.objectStore('progress').getAll();
            const rows = await new Promise((resolve, reject) => {
              all.onsuccess = () => resolve(all.result);
              all.onerror = () => reject(all.error);
            });
            db.close();
            return rows;
          }
        """)
        reviewed = next(row for row in stored if row.get("rating") == "mastered")
        assert reviewed["nextReviewAt"] > reviewed["lastReviewedAt"]
        assert reviewed["introducedOn"]
        assert reviewed["dailySessionDate"]

        page.reload(wait_until="networkidle")
        page.locator("#start-learning").click()
        page.wait_for_selector(".learn-title")
        assert page.locator("#learn-progress").inner_text() == "0 / 1"
        assert page.locator(".learn-title").inner_text() != first_title
        assert page.locator(".storage-note").is_visible()
    finally:
        browser.close()
        playwright.stop()


def test_gateway_and_mobile_home_have_no_horizontal_overflow(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto(f"{site_url}/", wait_until="networkidle")
        assert page.locator(".language-card").count() == 8
        page.goto(f"{site_url}/zh-cn/", wait_until="networkidle")
        dimensions = page.evaluate(
            "() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth })"
        )
        assert dimensions["scrollWidth"] <= dimensions["innerWidth"]
        assert page.locator("h1").inner_text() == "从一句想法，走到真正上线。"
    finally:
        browser.close()
        playwright.stop()

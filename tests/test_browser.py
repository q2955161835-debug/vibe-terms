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
        field.fill("Authentication")
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


def test_global_search_works_from_term_page_and_mobile_focus_returns(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        desktop = browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        desktop.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error"
            else None,
        )
        desktop.goto(f"{site_url}/zh-cn/terms/api/", wait_until="networkidle")
        field = desktop.locator(".desktop-search [data-search-input]")
        field.fill("Authentication")
        desktop.wait_for_selector(".desktop-search [role='option']")
        field.press("ArrowDown")
        field.press("Enter")
        desktop.wait_for_url("**/zh-cn/terms/authentication/")
        assert errors == []

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(f"{site_url}/zh-cn/knowledge/", wait_until="networkidle")
        trigger = mobile.locator("[data-search-open]")
        trigger.click()
        assert mobile.locator("#mobile-search-dialog").get_attribute("open") is not None
        mobile.locator("#mobile-search-dialog [data-search-close]").click()
        assert trigger.evaluate("element => document.activeElement === element")
    finally:
        browser.close()
        playwright.stop()


def test_dynamic_example_and_inline_exercise_persist_in_local_v2(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.goto(f"{site_url}/zh-cn/terms/api/", wait_until="networkidle")
        example = page.locator("[data-example-root]")
        example.locator('[data-example-control="verify"]').click()
        assert example.locator('[data-example-state="verify"]').is_visible()
        assert not example.locator('[data-example-state="context"]').is_visible()

        exercise = page.locator("[data-exercise]")
        exercise.locator('input[value="definition"]').check()
        exercise.locator('button[type="submit"]').click()
        feedback = exercise.locator("[data-exercise-feedback]")
        assert feedback.get_attribute("data-correct") == "true"
        rows = page.evaluate(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('exerciseAttempts', 'readonly')
                .objectStore('exerciseAttempts').getAll();
              const result = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return result;
            }
            """
        )
        assert any(row["exerciseId"] == "api:zh-cn:1" and row["correct"] for row in rows)
    finally:
        browser.close()
        playwright.stop()


def test_project_path_chapter_and_practice_queue_are_reachable(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on(
            "console",
            lambda message: errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.goto(f"{site_url}/zh-cn/paths/personal-site/", wait_until="networkidle")
        assert page.locator(".path-chapters li").count() == 10
        page.locator(".path-chapters a").first.click()
        page.wait_for_url("**/zh-cn/paths/personal-site/project-goal/")
        assert page.locator("h1").inner_text().strip()

        page.goto(f"{site_url}/zh-cn/practice/", wait_until="networkidle")
        page.wait_for_selector("[data-practice-card] h2")
        assert page.locator("[data-practice-status]").inner_text().startswith("1 /")
        assert errors == []
    finally:
        browser.close()
        playwright.stop()

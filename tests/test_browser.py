from __future__ import annotations

import json
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
        field = page.locator(".desktop-search [data-search-input]")
        field.fill("Authentication")
        page.wait_for_selector(".desktop-search [data-search-results] a")
        field.press("ArrowDown")
        assert field.get_attribute("aria-activedescendant")
        assert page.locator(".desktop-search [data-search-results] [role='option']").first.get_attribute("aria-selected") == "true"
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
        assert page.locator("html").get_attribute("data-theme") == "light"
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
        assert page.locator(".desktop-search [data-search-input]").is_visible()
        assert not page.locator('.topbar nav a[href$="/practice/"]').is_visible()
        assert page.locator("h1").inner_text() == "前端工程 VibeCoding 术语"
        assert page.locator(".term-card-grid .term-card").count() >= 3
    finally:
        browser.close()
        playwright.stop()


def test_global_search_works_from_term_page_and_stays_visible_on_mobile(site_url: str) -> None:
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
        mobile_field = mobile.locator(".desktop-search [data-search-input]")
        assert mobile_field.is_visible()
        mobile_field.fill("API")
        mobile.wait_for_selector(".desktop-search [role='option']")
        mobile_field.press("ArrowDown")
        mobile_field.press("Enter")
        mobile.wait_for_url("**/zh-cn/terms/api/")
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
        assert example.locator('[data-example-state="context"]').is_visible()
        assert "is-active" in (example.locator('[data-example-state="verify"]').get_attribute("class") or "")

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
        page.locator("[data-path-complete]").check()
        page.wait_for_function(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('pathProgress', 'readonly')
                .objectStore('pathProgress').get('personal-site:project-goal');
              const row = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return Boolean(row?.completed);
            }
            """
        )
        page.reload(wait_until="networkidle")
        assert page.locator("[data-path-complete]").is_checked()
        path_rows = page.evaluate(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('pathProgress', 'readonly')
                .objectStore('pathProgress').getAll();
              const result = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return result;
            }
            """
        )
        assert any(row["pathId"] == "personal-site:project-goal" and row["completed"] for row in path_rows)

        page.goto(f"{site_url}/zh-cn/practice/", wait_until="networkidle")
        page.wait_for_selector("[data-practice-card] h2")
        assert page.locator("[data-practice-status]").inner_text().startswith("1 /")
        assert errors == []
    finally:
        browser.close()
        playwright.stop()


def test_bookmark_selection_restores_after_reload(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(f"{site_url}/zh-cn/terms/api/", wait_until="networkidle")
        bookmark = page.locator('[data-bookmark][data-term-slug="api"]').first
        bookmark.click()
        page.wait_for_function(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('bookmarks', 'readonly')
                .objectStore('bookmarks').get('api');
              const row = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return Boolean(row?.selected);
            }
            """
        )
        page.reload(wait_until="networkidle")
        assert page.locator('[data-bookmark][data-term-slug="api"]').first.get_attribute("aria-pressed") == "true"
    finally:
        browser.close()
        playwright.stop()


def test_local_import_validates_every_row_and_commits_atomically(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(f"{site_url}/en/practice/", wait_until="networkidle")
        empty = {
            "schemaVersion": 2,
            "termProgress": [],
            "exerciseAttempts": [],
            "pathProgress": [],
            "bookmarks": [],
            "recentViews": [],
        }
        valid = {
            **empty,
            "recentViews": [
                {"id": "imported-api", "slug": "api", "updatedAt": 200}
            ],
        }
        with page.expect_navigation(wait_until="networkidle"):
            page.locator("[data-import-local]").set_input_files(
                {
                    "name": "valid-vibe-terms.json",
                    "mimeType": "application/json",
                    "buffer": json.dumps(valid).encode("utf-8"),
                }
            )
        imported = page.evaluate(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('recentViews', 'readonly')
                .objectStore('recentViews').get('imported-api');
              const row = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return row || null;
            }
            """
        )
        assert imported and imported["slug"] == "api"
        assert page_errors == []

        invalid = {
            **empty,
            "termProgress": [
                {"slug": "must-not-write", "rating": "mastered", "updatedAt": 300}
            ],
            "bookmarks": [{"id": "", "updatedAt": 300}],
        }
        import_input = page.locator("[data-import-local]")
        import_input.set_input_files(
            {
                "name": "invalid-vibe-terms.json",
                "mimeType": "application/json",
                "buffer": json.dumps(invalid).encode("utf-8"),
            }
        )
        page.wait_for_timeout(500)
        assert import_input.evaluate("element => element.validationMessage")
        assert not page.evaluate(
            """
            async () => {
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const read = db.transaction('termProgress', 'readonly')
                .objectStore('termProgress').get('must-not-write');
              const row = await new Promise((resolve, reject) => {
                read.onsuccess = () => resolve(read.result);
                read.onerror = () => reject(read.error);
              });
              db.close();
              return Boolean(row);
            }
            """
        )
    finally:
        browser.close()
        playwright.stop()


def test_clear_removes_v2_legacy_data_and_migration_marker(site_url: str) -> None:
    playwright, browser = _browser()
    try:
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(f"{site_url}/en/practice/", wait_until="networkidle")
        page.evaluate(
            """
            async () => {
              await new Promise((resolve, reject) => {
                const remove = indexedDB.deleteDatabase('vibe-terms-guest-v1');
                remove.onsuccess = resolve;
                remove.onerror = () => reject(remove.error);
              });
              await new Promise((resolve, reject) => {
                const request = indexedDB.open('vibe-terms-guest-v1', 1);
                request.onupgradeneeded = () => {
                  request.result.createObjectStore('progress', { keyPath: 'slug' });
                };
                request.onsuccess = () => {
                  const db = request.result;
                  const transaction = db.transaction('progress', 'readwrite');
                  transaction.objectStore('progress').put({
                    slug: 'legacy-only', rating: 'mastered', updatedAt: 100,
                  });
                  transaction.oncomplete = () => { db.close(); resolve(); };
                  transaction.onerror = () => { db.close(); reject(transaction.error); };
                };
                request.onerror = () => reject(request.error);
              });
              localStorage.setItem('vibe-terms-v2-migration-complete', '1');
            }
            """
        )
        clear = page.locator("[data-clear-local]")
        clear.click()
        clear.click()
        page.wait_for_timeout(800)
        remaining = page.evaluate(
            """
            async () => {
              const stores = ['termProgress', 'exerciseAttempts', 'pathProgress', 'bookmarks', 'recentViews'];
              const request = indexedDB.open('vibe-terms-local-v2', 1);
              const db = await new Promise((resolve, reject) => {
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
              });
              const transaction = db.transaction(stores, 'readonly');
              const counts = {};
              await Promise.all(stores.map((store) => new Promise((resolve, reject) => {
                const read = transaction.objectStore(store).count();
                read.onsuccess = () => { counts[store] = read.result; resolve(); };
                read.onerror = () => reject(read.error);
              })));
              db.close();
              return {
                marker: localStorage.getItem('vibe-terms-v2-migration-complete'),
                databases: typeof indexedDB.databases === 'function'
                  ? (await indexedDB.databases()).map((entry) => entry.name)
                  : [],
                counts,
              };
            }
            """
        )
        assert remaining["marker"] is None
        assert "vibe-terms-guest-v1" not in remaining["databases"]
        assert all(count == 0 for count in remaining["counts"].values())
    finally:
        browser.close()
        playwright.stop()

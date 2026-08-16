# Vibe Terms Local Static Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前 12 词匿名静态原型扩展为搜索入口清晰、知识地图与项目路径并立、词条信息完整、含动态示例与小练、可从 GitHub Pages 公开访问的 60 词核心版本。

**Architecture:** 保留 Python 内容生成器、`content/` YAML、`web/` 原生 CSS/JavaScript 和主机无关静态产物。构建期完成 Schema/关系校验、页面与索引生成；浏览器只负责本地搜索、确定性交互示例、练习和 IndexedDB 进度，vinext/Worker 仍只是 Codex Sites 打包适配层。

**Tech Stack:** Python 3.11+、PyYAML、普通 HTML/CSS/JavaScript、IndexedDB/localStorage、Node.js 内置测试、pytest、Playwright、GitHub Actions/Pages。

## Global Constraints

- 固定保留 8 个语言路由：`en`、`zh-cn`、`zh-tw`、`ja`、`ko`、`de`、`ru`、`hi`。
- 不新增账号、登录、注册、Supabase、数据库、云同步、支付、提醒、推送和分析。
- `content/` 是唯一内容源；英文是规范含义源；本地化词条始终显示规范英文名。
- 结构化学习数据使用 IndexedDB；localStorage 只保存小偏好和显式降级数据。
- 所有核心页面关闭 JavaScript 后仍包含定义、示例说明、题目和普通链接。
- 动态示例只使用已注册的确定性渲染器；禁止 `eval`、用户代码执行和第三方嵌入。
- 首个内容门禁是 60 个规范词、3 条 8–12 章项目路径、每词至少 1 个示例模块和 1 道题、至少 20 个互动或分步示例。
- GitHub Pages 必须支持 `BASE_PATH=/vibe-terms`；自定义域名与 Codex Sites 使用空 `BASE_PATH`。
- 不手工编辑或提交 `site/`、`dist/`、浏览器 profile、`.env` 或任何真实秘密。
- 用户尚未传达正在整理的网页文件；开始 Task 1 前必须先由用户确认文件已落入仓库，再重新读取 `AGENTS.md`、分支、状态和差异。该门禁不授权创建 worktree。
- 每个可观察行为先写失败测试；每个任务通过局部测试并由独立子 agent 验收后才提交。所有任务完成后再做一次独立正式验收。

---

## Scope and Release Boundary

本计划只覆盖设计规范中的 M1 与 M2：完成体验骨架和 60 词核心体验。180 词、500 词和 8 条以上项目路径分别另写后续计划，不在本计划中顺带实现。

执行时使用普通任务分支，不创建 Git worktree。网页整理文件进入仓库后，如果它们改变了下面的文件职责，先修订本计划的文件地图并让用户确认；不得用旧行号覆盖新实现。

## Planned File Map

| Path | Responsibility |
| --- | --- |
| `scripts/build_static_site.py` | 薄命令入口：读取配置、加载目录、调用生成器 |
| `scripts/vibe_terms/config.py` | 语言、目录、站点 URL、`BASE_PATH` 和里程碑阈值 |
| `scripts/vibe_terms/models.py` | 规范化术语、主题、路径和章节数据类型 |
| `scripts/vibe_terms/content.py` | YAML 读取、Schema、版本、引用和先修图校验 |
| `scripts/vibe_terms/urls.py` | 页面、资源、规范链接和 sitemap 的统一 URL 生成 |
| `scripts/vibe_terms/render.py` | Shell、首页、术语、知识、路径、练习与兼容页渲染 |
| `scripts/vibe_terms/indexes.py` | 搜索、知识图、路径与练习静态 JSON 索引 |
| `content/taxonomy/domains.yaml` | 8 个稳定一级领域 |
| `content/taxonomy/topics.yaml` | 二级主题及其一级领域归属 |
| `content/taxonomy/lifecycle.yaml` | 横向生命周期筛选 |
| `content/terms/<slug>/meta.yaml` | 语言无关关系、难度、示例注册信息和版本 |
| `content/terms/<slug>/<locale>.yaml` | 8 语言定义、场景、误区、示例文案、题目和来源 |
| `content/paths/<slug>/meta.yaml` | 路径顺序、章节 ID、术语引用和生命周期阶段 |
| `content/paths/<slug>/<locale>.yaml` | 路径与章节教学文案、产物和验收步骤 |
| `web/core.js` | 可单测的检索、判题、队列、迁移和调度纯函数 |
| `web/app.js` | DOM 绑定、搜索层、示例、练习和本地存储适配 |
| `web/styles.css` | 响应式布局、粘性搜索、知识图、词条和练习视觉状态 |
| `tests/test_content_schema.py` | 内容 Schema、关系、规模和路径门禁 |
| `tests/test_urls.py` | 根路径与 GitHub Pages 子路径 URL 合同 |
| `tests/test_static_site.py` | 静态页面、索引、SEO、无脚本和链接合同 |
| `tests/js/core.test.cjs` | 搜索、练习、队列和本地数据迁移单元测试 |
| `tests/test_render_harness.py` | 无 localhost 的 Chromium 渲染验收 |
| `tests/test_browser.py` | 真实 HTTP 导航、持久化和响应式流程 |
| `.github/workflows/ci.yml` | 每次 push/PR 的完整验证 |
| `.github/workflows/deploy-pages.yml` | `main` 验证通过后发布 `site/` 到 GitHub Pages |
| `README.md` | 本地运行、内容范围、隐私边界和公开地址 |
| `docs/deployment.md` | 根路径/子路径构建、发布和线上读回 |
| `doc/验收/模块/验收-静态站点.md` | 长期模块验收项 |
| `doc/验收/跨模块/验收-查词到项目学习.md` | 查词→示例→小练→路径的关键流程 |
| `doc/验收/任务/验收-60词本地静态扩展.md` | 本任务汇总、风险和正式结论 |

## Stable Interfaces

后续任务统一使用以下接口，修改名称或字段时必须同步修订后续任务：

Python 数据与函数合同：

- `BuildConfig(content_root: Path, output_root: Path, site_url: str, base_path: str, minimum_terms: int)` 是不可变 dataclass；
- `Catalog(locales: tuple[str, ...], domains: tuple[dict, ...], topics: tuple[dict, ...], terms: tuple[dict, ...], paths: tuple[dict, ...])` 是不可变 dataclass；
- `load_catalog(content_root: Path, minimum_terms: int) -> Catalog` 读取并规范化全部内容；
- `validate_catalog(catalog: Catalog) -> None` 对规范模型执行跨文件校验；
- `build_site(config: BuildConfig, catalog: Catalog) -> list[str]` 返回生成的公开路由列表。

浏览器核心继续保留现有导出，并新增：

```javascript
scoreSearchDocument(document, query)
groupSearchResults(documents, query, limit)
gradeExercise(exercise, selectedIds)
buildPracticeQueue(exercises, attempts, scope, now)
migrateLocalStateV1(rows, now)
```

---

### Task 1: Define Content Schema v2 and the Eight-domain Taxonomy

**Files:**
- Create: `scripts/vibe_terms/__init__.py`
- Create: `scripts/vibe_terms/config.py`
- Create: `scripts/vibe_terms/models.py`
- Create: `scripts/vibe_terms/content.py`
- Create: `content/taxonomy/topics.yaml`
- Create: `tests/test_content_schema.py`
- Modify: `content/taxonomy/domains.yaml`
- Modify: `content/taxonomy/lifecycle.yaml`
- Modify: `content/terms/*/meta.yaml`
- Modify: `content/terms/*/{en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml`
- Modify: `scripts/build_static_site.py`

**Interfaces:**
- Consumes: existing YAML files and `BuildConfig`/`Catalog` declarations above.
- Produces: `load_catalog(content_root, minimum_terms)` and `validate_catalog(catalog)` for every renderer and index task.

- [ ] **Step 1: Write failing Schema and relationship tests**

```python
from pathlib import Path

import pytest

from scripts.vibe_terms.content import load_catalog

ROOT = Path(__file__).resolve().parents[1]

def test_catalog_has_eight_domains_and_valid_topic_links() -> None:
    catalog = load_catalog(ROOT / "content", minimum_terms=12)
    assert len(catalog.domains) == 8
    domain_ids = {item["id"] for item in catalog.domains}
    assert {item["domain"] for item in catalog.topics} <= domain_ids

def test_every_term_has_v2_relationships_example_exercise_and_source() -> None:
    catalog = load_catalog(ROOT / "content", minimum_terms=12)
    for term in catalog.terms:
        assert term["topics"]
        assert isinstance(term["lifecycle_stages"], list)
        assert term["example"]["mode"] in {"interactive", "stepper", "compare", "static"}
        for localized in term["localized"].values():
            assert localized["user_says"]
            assert localized["boundary"]
            assert localized["exercise"]["answer"]
            assert localized["sources"]
```

- [ ] **Step 2: Run the tests and confirm the old content contract fails**

Run: `python3 -m pytest tests/test_content_schema.py -q`
Expected: FAIL because `scripts.vibe_terms` and the v2 fields do not exist.

- [ ] **Step 3: Implement focused loader types and validation**

`content.py` must reject duplicate IDs/slugs, missing languages, stale `source_content_version`, unknown domains/topics/terms, missing example registrations, invalid exercise answers, paths outside the content root, and cycles in `prerequisites`.

```python
def ensure_prerequisite_dag(edges: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(slug: str) -> None:
        if slug in visiting:
            raise ValueError(f"prerequisite cycle includes {slug}")
        if slug in visited:
            return
        visiting.add(slug)
        for parent in edges.get(slug, set()):
            visit(parent)
        visiting.remove(slug)
        visited.add(slug)

    for slug in edges:
        visit(slug)
```

- [ ] **Step 4: Replace the taxonomy and migrate the existing 12 terms**

Use the eight IDs from the design: `ai-vibe`, `web-ui`, `app-platform`, `backend-api`, `data-storage`, `security-identity`, `git-quality-ship`, `product-design`. Add localized topic labels and migrate each existing term from `lifecycle_stage` to `lifecycle_stages`. Each of the existing 12 terms receives complete v2 localized fields, one exercise, one source and a valid example mode; no empty placeholder strings.

- [ ] **Step 5: Make the current build use the new loader without changing page layout**

`scripts/build_static_site.py` becomes the compatibility entry point and calls `load_catalog`. Keep the current routes and generated output green until later rendering tasks deliberately change them.

- [ ] **Step 6: Run local verification**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py -q`
Expected: PASS with 12 terms and all existing routes still generated.

- [ ] **Step 7: Request independent module acceptance and commit**

Acceptance scope: Schema v2, eight-domain taxonomy, 12-term migration, existing static build only.
Commit: `feat: define rich local content contracts`

### Task 2: Split the Generator and Add Host-independent URLs

**Files:**
- Create: `scripts/vibe_terms/urls.py`
- Create: `scripts/vibe_terms/render.py`
- Create: `scripts/vibe_terms/indexes.py`
- Create: `tests/test_urls.py`
- Modify: `scripts/build_static_site.py`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Consumes: `BuildConfig`, `Catalog`, `load_catalog`.
- Produces: `UrlBuilder.page(path)`, `UrlBuilder.asset(path)`, `UrlBuilder.absolute(path)`, `build_site(config, catalog)`.

- [ ] **Step 1: Add failing URL contract tests**

```python
from scripts.vibe_terms.urls import UrlBuilder

def test_project_pages_prefix_internal_urls_but_not_origin_twice() -> None:
    urls = UrlBuilder("https://q2955161835-debug.github.io/vibe-terms", "/vibe-terms")
    assert urls.page("/zh-cn/terms/api/") == "/vibe-terms/zh-cn/terms/api/"
    assert urls.asset("assets/styles.css") == "/vibe-terms/assets/styles.css"
    assert urls.absolute("/zh-cn/") == "https://q2955161835-debug.github.io/vibe-terms/zh-cn/"

def test_root_host_uses_empty_base_path() -> None:
    urls = UrlBuilder("https://vibe-terms.example", "")
    assert urls.page("/en/") == "/en/"
```

- [ ] **Step 2: Confirm tests fail against hard-coded root paths**

Run: `python3 -m pytest tests/test_urls.py -q`
Expected: FAIL because `UrlBuilder` does not exist.

- [ ] **Step 3: Implement URL normalization and configuration parsing**

Reject `BASE_PATH` values that contain a scheme, query, fragment or trailing slash. `SITE_URL` may be empty for local preview; when present it must omit the trailing slash. Every link, asset, canonical, alternate, sitemap entry and manifest URL must use the helper.

- [ ] **Step 4: Extract rendering and index responsibilities**

Move content-independent HTML helpers into `render.py`, JSON index generation into `indexes.py`, and leave `build_static_site.py` with configuration plus one `build_site` call. Preserve generated file names so packaging and Sites routing remain valid.

- [ ] **Step 5: Add root and `/vibe-terms` build tests**

Build twice into isolated pytest temporary directories. Parse every internal `href`, `src`, manifest and sitemap URL and assert it resolves under the correct output root.

- [ ] **Step 6: Verify both hosts and commit**

Run: `python3 -m pytest tests/test_urls.py tests/test_static_site.py tests/test_packaging.py -q`
Expected: PASS for empty and project base paths.
Commit: `refactor: make the static generator host independent`

### Task 3: Put Search in the Global Header and Expand the Search Model

**Files:**
- Modify: `scripts/vibe_terms/indexes.py`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `web/core.js`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `content/ui.yaml`
- Modify: `tests/js/core.test.cjs`
- Modify: `tests/test_render_harness.py`
- Modify: `tests/test_browser.py`

**Interfaces:**
- Consumes: per-locale catalog data and `UrlBuilder`.
- Produces: `search-index.json` documents of type `term`, `topic`, or `path`; `scoreSearchDocument` and `groupSearchResults`.

- [ ] **Step 1: Write failing grouped-search and keyboard tests**

```javascript
test('groups exact term matches ahead of topics and paths', () => {
  const docs = [
    { type: 'path', title: 'Build an API', canonical_name: '', aliases: [], summary: 'API project' },
    { type: 'term', title: 'API', canonical_name: 'Application Programming Interface', aliases: ['接口'], summary: 'contract' },
    { type: 'topic', title: 'Backend APIs', canonical_name: '', aliases: [], summary: 'HTTP endpoints' },
  ];
  const groups = groupSearchResults(docs, 'API', 8);
  assert.equal(groups.term[0].title, 'API');
  assert.equal(groups.path.length, 1);
  assert.equal(groups.topic.length, 1);
});
```

Browser tests must assert `/`, `ControlOrMeta+K`, arrows, Enter and Escape, plus focus return to the mobile trigger.

- [ ] **Step 2: Confirm old search fails the new contracts**

Run: `npm run test:js` and `python3 -m pytest tests/test_render_harness.py -q`
Expected: FAIL because indexes contain terms only and the search input is homepage-only.

- [ ] **Step 3: Generate grouped search documents**

Include title, canonical English name, aliases, short definition/summary, user phrase, domain, topic, path/chapter labels, URL and match fields. Do not place complete long-form content in the index.

- [ ] **Step 4: Implement persistent desktop search and mobile search layer**

At `>=1024px`, render a `320–520px` search box in the sticky header. Below that breakpoint render a labeled trigger that opens a full-width dialog. The homepage may repeat a wide search after no more than two lines of intro. Use one controller and one result renderer for both inputs.

- [ ] **Step 5: Implement deterministic fallbacks**

Empty query shows recent views/bookmarks when available and fixed popular terms otherwise. Index failure leaves ordinary navigation usable and exposes a retry button. No-result state preserves the query and links to knowledge topics.

- [ ] **Step 6: Run search-focused verification and commit**

Run: `npm run test:js`
Run: `python3 -m pytest tests/test_render_harness.py::test_home_search_theme_and_mobile_layout_without_http_navigation tests/test_browser.py::test_search_keyboard_and_locale_switch -q`
Expected: PASS with no horizontal overflow and correct focus behavior.
Commit: `feat: make multilingual search globally accessible`

### Task 4: Build Knowledge-map and Topic Browse Pages

**Files:**
- Modify: `scripts/vibe_terms/render.py`
- Modify: `scripts/vibe_terms/indexes.py`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `content/ui.yaml`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_render_harness.py`

**Interfaces:**
- Consumes: domains, topics, term `prerequisites`/`related_terms`, `UrlBuilder`.
- Produces: knowledge overview/domain/topic pages and `knowledge-graph.json`.

- [ ] **Step 1: Write failing route and graph-equivalence tests**

```python
def test_knowledge_routes_and_accessible_list_cover_the_same_terms(build_site) -> None:
    overview = (build_site / "zh-cn" / "knowledge" / "index.html").read_text(encoding="utf-8")
    graph = json.loads((build_site / "zh-cn" / "knowledge-graph.json").read_text(encoding="utf-8"))
    expected = {node["slug"] for node in graph["nodes"]}
    for slug in expected:
        assert f'/zh-cn/terms/{slug}/' in overview
```

- [ ] **Step 2: Confirm the routes are missing**

Run: `python3 -m pytest tests/test_static_site.py -q -k knowledge`
Expected: FAIL because only legacy category pages exist.

- [ ] **Step 3: Render overview, domain and topic pages**

Overview cards show localized name, topic examples and counts. Domain pages offer topic navigation, lifecycle/difficulty filters and complete term cards. Topic pages show recommended start, prerequisites and related nodes.

- [ ] **Step 4: Add enhanced graph without making it the only interface**

Use `knowledge-graph.json` to progressively enhance the same HTML list. Keyboard and screen-reader users retain domain/topic groups and ordinary links. On small screens, do not render an unreadable miniature graph; keep the list primary.

- [ ] **Step 5: Preserve legacy category routes**

Generate `/{locale}/categories/{domain-id}/` compatibility pages with a canonical link and clear move link to `/{locale}/knowledge/{domain-id}/` for one public release.

- [ ] **Step 6: Verify and commit**

Run: `python3 -m pytest tests/test_static_site.py tests/test_render_harness.py -q -k "knowledge or category or locale"`
Expected: PASS in all eight locales.
Commit: `feat: add the browsable Vibe Terms knowledge map`

### Task 5: Render a Dense but Progressive Term Detail Page

**Files:**
- Modify: `scripts/vibe_terms/render.py`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `content/ui.yaml`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_render_harness.py`

**Interfaces:**
- Consumes: complete v2 localized term records.
- Produces: the exact term-page section order defined in design section 9.3.

- [ ] **Step 1: Add failing semantic-section tests**

```python
def test_term_page_contains_learning_sections_without_javascript(build_site) -> None:
    html = (build_site / "zh-cn" / "terms" / "state" / "index.html").read_text(encoding="utf-8")
    required = [
        'data-section="definition"',
        'data-section="prerequisites"',
        'data-section="example"',
        'data-section="exercise"',
        'data-section="agent-prompt"',
        'data-section="sources"',
    ]
    assert all(marker in html for marker in required)
    assert "State" in html
```

- [ ] **Step 2: Confirm the existing sparse template fails**

Run: `python3 -m pytest tests/test_static_site.py -q -k term_page`
Expected: FAIL on missing prerequisites, exercise and sources.

- [ ] **Step 3: Implement the progressive layout**

Render breadcrumb, previous/next, bookmark/copy actions, local title, canonical English, aliases, fields, user phrase, concise definition, boundary, prerequisites, confusion notes, example, work scenarios, mistakes, exercise, Agent prompt, project memberships and sources. Desktop gets a sticky page outline; mobile stays single-column.

- [ ] **Step 4: Keep all teaching content in HTML**

Interactive controls may hide/reveal states, but the initial example, question, answer-independent option text, source links and path links must be present before JavaScript runs. Do not embed unsanitized content HTML.

- [ ] **Step 5: Verify representative terms and commit**

Run: `python3 -m pytest tests/test_static_site.py tests/test_render_harness.py -q -k "term or no_javascript or overflow"`
Expected: PASS for `prompt`, `state`, `api`, `database`, `authentication`, `git`, `testing` and `deployment`.
Commit: `feat: enrich every static term detail page`

### Task 6: Add the Registered Dynamic-example Framework

**Files:**
- Create: `web/examples.js`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `scripts/vibe_terms/content.py`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `tests/js/core.test.cjs`
- Modify: `tests/test_render_harness.py`
- Modify: `tests/test_static_site.py`

**Interfaces:**
- Consumes: `example.mode`, `example.id`, localized `example_copy.states`.
- Produces: `window.VibeExamples.mount(root, definition)` and static fallback markup.

- [ ] **Step 1: Write failing allow-list and interaction tests**

The content test rejects an unknown `example.id`. The render harness changes `state` from default→saving→success→failure and asserts the visible status/button state matches the selected control.

```javascript
test('unknown example identifiers cannot create executable definitions', () => {
  assert.equal(VibeExamples.has('form-save-state'), true);
  assert.equal(VibeExamples.has('user-supplied-script'), false);
});
```

- [ ] **Step 2: Confirm there is no example registry**

Run: `npm run test:js` and `python3 -m pytest tests/test_render_harness.py -q -k example`
Expected: FAIL before `web/examples.js` exists.

- [ ] **Step 3: Implement four renderer modes**

Implement `interactive`, `stepper`, `compare` and `static` adapters behind a fixed registry. The registry maps known IDs to code; YAML provides labels and safe state values only. Failure leaves the static first state and explanation visible.

- [ ] **Step 4: Add six representative interactive examples**

Implement exact IDs for `prompt-constraint-builder`, `context-window-budget`, `agent-tool-loop`, `component-reuse`, `form-save-state`, and `api-request-response`. Respect `prefers-reduced-motion` and keyboard operation.

- [ ] **Step 5: Verify CSP-safe output and commit**

Assert generated pages contain no `eval(`, `new Function`, inline user script or third-party iframe.
Run: `npm run test:js`
Run: `python3 -m pytest tests/test_static_site.py tests/test_render_harness.py -q -k example`
Expected: PASS.
Commit: `feat: add safe progressive term examples`

### Task 7: Add Per-term Exercises, Practice Queues, and Local Data v2

**Files:**
- Modify: `web/core.js`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `scripts/vibe_terms/indexes.py`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `content/ui.yaml`
- Modify: `tests/js/core.test.cjs`
- Modify: `tests/test_browser.py`
- Modify: `tests/test_render_harness.py`

**Interfaces:**
- Consumes: localized exercise records and v1 progress rows.
- Produces: `gradeExercise`, `buildPracticeQueue`, `migrateLocalStateV1`, IndexedDB `vibe-terms-local-v2` stores.

- [ ] **Step 1: Write failing grading, queue and migration tests**

```javascript
test('grades by stable option id and returns every explanation', () => {
  const exercise = {
    id: 'state-save-result',
    type: 'single-choice',
    answer: 'after-success',
    explanations: { 'after-success': 'Correct', 'before-response': 'The request may fail' },
  };
  const result = gradeExercise(exercise, ['after-success']);
  assert.equal(result.correct, true);
  assert.equal(result.explanations['before-response'], 'The request may fail');
});

test('v1 migration is idempotent', () => {
  const rows = [{ slug: 'api', rating: 'mastered', updatedAt: 100 }];
  assert.deepEqual(migrateLocalStateV1(migrateLocalStateV1(rows, 200), 200), migrateLocalStateV1(rows, 200));
});
```

- [ ] **Step 2: Confirm the new functions and practice route are absent**

Run: `npm run test:js` and `python3 -m pytest tests/test_browser.py -q -k practice`
Expected: FAIL.

- [ ] **Step 3: Implement local v2 stores and transactional migration**

Create `termProgress`, `exerciseAttempts`, `pathProgress`, `bookmarks`, and `recentViews`. Read v1 once, write v2 in a transaction, and only mark migration complete after success. Keep localStorage as the existing explicit fallback.

- [ ] **Step 4: Implement inline and standalone practice**

Inline questions provide immediate feedback without navigating away. `/{locale}/practice/` can scope by due review, domain, path, bookmarks or all. Queue order is: previous wrong/due, selected path, unseen. Answering never requires login.

- [ ] **Step 5: Add export, validated import and clear controls**

Export includes `schemaVersion: 2`. Import validates shape before a transaction and merges by newer `updatedAt`. Invalid data leaves all existing stores unchanged. Clear requires an in-page confirmation and deletes only Vibe Terms local stores/preferences.

- [ ] **Step 6: Verify persistence and commit**

Run: `npm run test:js`
Run: `RUN_HTTP_E2E=1 python3 -m pytest tests/test_browser.py -q -k "practice or persists or migration"`
Expected: PASS with browser reload and no account UI.
Commit: `feat: add anonymous local practice and progress`

### Task 8: Implement the First Real Project Path

**Files:**
- Delete: `content/paths/zero-to-vibe.prototype.yaml`
- Create: `content/paths/ship-a-product-site/meta.yaml`
- Create: `content/paths/ship-a-product-site/{en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml`
- Modify: `scripts/vibe_terms/content.py`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `scripts/vibe_terms/indexes.py`
- Modify: `web/app.js`
- Modify: `web/styles.css`
- Modify: `tests/test_content_schema.py`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_browser.py`

**Interfaces:**
- Consumes: term slugs, lifecycle stages and local `pathProgress`.
- Produces: path directory/detail/chapter routes and first complete 10-chapter course.

- [ ] **Step 1: Write failing path integrity tests**

```python
def test_paths_have_ordered_chapters_tasks_outputs_and_acceptance() -> None:
    catalog = load_catalog(ROOT / "content", minimum_terms=12)
    path = next(item for item in catalog.paths if item["slug"] == "ship-a-product-site")
    assert 8 <= len(path["chapters"]) <= 12
    assert [chapter["order"] for chapter in path["chapters"]] == list(range(1, len(path["chapters"]) + 1))
    for localized in path["localized"].values():
        for chapter in localized["chapters"]:
            assert chapter["task"]
            assert chapter["deliverable"]
            assert chapter["acceptance"]
```

- [ ] **Step 2: Confirm the prototype term list fails the course contract**

Run: `python3 -m pytest tests/test_content_schema.py -q -k path`
Expected: FAIL because the old file has no chapters, tasks or localized content.

- [ ] **Step 3: Author the ten exact chapters**

Use these stable chapter IDs and order: `product-brief`, `requirements`, `information-architecture`, `wireframe`, `html-structure`, `css-system`, `responsive-accessible-ui`, `interaction-and-state`, `testing`, `deploy-and-accept`. Each chapter specifies required/optional terms, one task, one deliverable and concrete checks.

- [ ] **Step 4: Render path pages and local progress**

Directory cards show final artifact and chapter count. Detail page shows 0–10 completion, continue link and complete chapter list. Chapter completion is a local checkbox; content remains readable when storage is unavailable.

- [ ] **Step 5: Verify the full path and commit**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py -q -k path`
Run: `RUN_HTTP_E2E=1 python3 -m pytest tests/test_browser.py -q -k path`
Expected: PASS across eight locales with reload persistence.
Commit: `feat: add the product-site learning path`

### Task 9: Expand the Corpus to 24 Terms — AI and Web Foundations

**Files:**
- Create: `content/terms/{token,llm,tool-calling,rag,hallucination,html,css,javascript,dom,component,state,accessibility}/`
- Modify: `tests/test_content_schema.py`

**Interfaces:**
- Consumes: Task 1 v2 term contract and Task 6 example registry.
- Produces: 12 new canonical terms, 96 reviewed localization files, 12 exercises and 12 examples.

- [ ] **Step 1: Raise the batch test threshold to 24 and list exact expected slugs**

Assert that all 12 slugs above exist, every locale is `reviewed`, every `source_content_version` equals `content_version`, and no normalized paragraph is duplicated across unrelated terms.

- [ ] **Step 2: Confirm the corpus test fails at 12**

Run: `python3 -m pytest tests/test_content_schema.py -q -k corpus`
Expected: FAIL with the 12 exact missing slugs.

- [ ] **Step 3: Author English canonical records in groups of four**

For each term, write boundary-aware definitions, a beginner phrase, real work scenarios, mistakes, example data, one exercise with all option explanations, Agent prompt and at least one authoritative primary source. Review one four-term group before starting the next.

- [ ] **Step 4: Add eight-language files and verify each four-term group**

Run after each group: `python3 -m pytest tests/test_content_schema.py -q -k "schema or translation"`
Expected: PASS for completed groups; final run reaches 24 terms.

- [ ] **Step 5: Render, inspect and commit the batch**

Run: `python3 -m pytest tests/test_static_site.py tests/test_render_harness.py -q -k "term or locale or search"`
Expected: PASS with new terms in knowledge pages and search.
Commit: `content: add AI and web foundation terms`

### Task 10: Expand the Corpus to 36 Terms — App, Backend, and Data

**Files:**
- Create: `content/terms/{native-app,cross-platform,app-package,device-api,app-store,rest-api,endpoint,request-response,http-status-code,webhook,relational-database,sql}/`
- Modify: `tests/test_content_schema.py`

**Interfaces:**
- Consumes: v2 content contract.
- Produces: 12 new terms covering the previously empty `app-platform` domain plus backend/data foundations.

- [ ] **Step 1: Raise the threshold to 36 with the exact slug set above**

- [ ] **Step 2: Confirm the missing-term failure**

Run: `python3 -m pytest tests/test_content_schema.py -q -k corpus`
Expected: FAIL listing those 12 slugs.

- [ ] **Step 3: Author English and eight-language content in three four-term review groups**

`app-store` explains distribution without implying this web project uses an app store. `http-status-code` distinguishes protocol status from user-facing error text. `sql` and `relational-database` cross-link without circular prerequisites.

- [ ] **Step 4: Verify the batch and commit**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py tests/test_render_harness.py -q -k "content or term or search"`
Expected: PASS with all eight domains non-empty.
Commit: `content: add app backend and data foundation terms`

### Task 11: Expand the Corpus to 48 Terms — Data, Security, and Git

**Files:**
- Create: `content/terms/{schema,migration,query,cache,authorization,session,cookie,environment-variable,secret,cors,repository,commit}/`
- Modify: `tests/test_content_schema.py`

**Interfaces:**
- Consumes: v2 content contract.
- Produces: 12 new terms with explicit security boundaries and valid relationship edges.

- [ ] **Step 1: Raise the threshold to 48 and assert the exact slug set**

- [ ] **Step 2: Confirm the missing-term failure**

Run: `python3 -m pytest tests/test_content_schema.py -q -k corpus`
Expected: FAIL listing those 12 slugs.

- [ ] **Step 3: Author and review the batch**

The `secret` and `environment-variable` entries must state that client-side static bundles cannot protect secrets. `authentication` vs `authorization`, `session` vs `cookie`, and `schema` vs `migration` each need explicit compare examples and reciprocal related links without duplicated definitions.

- [ ] **Step 4: Run content/security scans and commit**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py -q`
Run: `rg -n -i "api[_-]?key\s*[:=]|secret\s*[:=]|password\s*[:=]" content README.md docs AGENTS.md`
Expected: tests PASS; scan finds only explanatory placeholders, never real values.
Commit: `content: add data security and Git terms`

### Task 12: Expand the Corpus to 60 Terms — Workflow, Quality, and Product

**Files:**
- Create: `content/terms/{branch,pull-request,unit-test,end-to-end-test,debugging,requirement,user-story,information-architecture,wireframe,design-system,responsive-design,acceptance-criteria}/`
- Modify: `tests/test_content_schema.py`

**Interfaces:**
- Consumes: v2 content contract and existing `git`, `testing`, `deployment` terms.
- Produces: the final 60-term corpus and product-path vocabulary.

- [ ] **Step 1: Set `minimum_terms=60` for the core release and assert all 60 slugs**

Keep the threshold in configuration/test fixtures; do not hard-code 60 into the generic loader so future 180/500 plans can raise it cleanly.

- [ ] **Step 2: Confirm the final batch is missing**

Run: `python3 -m pytest tests/test_content_schema.py -q -k corpus`
Expected: FAIL listing the 12 exact new slugs.

- [ ] **Step 3: Author English and eight-language content in four-term review groups**

`requirement`, `user-story`, `acceptance-criteria` and `testing` must distinguish desired behavior from proof. `information-architecture`, `wireframe`, `design-system` and `responsive-design` must use product-design examples instead of framework-specific definitions.

- [ ] **Step 4: Run the 60-term content gate and commit**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py tests/test_render_harness.py -q`
Expected: PASS with 60 terms × 8 locale pages, search entries, example modules, exercises and valid relationships.
Commit: `content: complete the 60-term core corpus`

### Task 13: Complete Three Paths and the 20-example Coverage Gate

**Files:**
- Create: `content/paths/build-a-local-crud-tool/meta.yaml`
- Create: `content/paths/build-a-local-crud-tool/{en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml`
- Create: `content/paths/build-an-ai-chat-assistant/meta.yaml`
- Create: `content/paths/build-an-ai-chat-assistant/{en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml`
- Modify: `web/examples.js`
- Modify: `content/terms/*/meta.yaml`
- Modify: `content/terms/*/{en,zh-cn,zh-tw,ja,ko,de,ru,hi}.yaml`
- Modify: `tests/test_content_schema.py`
- Modify: `tests/test_render_harness.py`

**Interfaces:**
- Consumes: 60-term corpus, path renderer and example registry.
- Produces: 3 complete paths and exactly verified coverage of at least 20 interactive/stepper examples.

- [ ] **Step 1: Add failing release-gate tests**

```python
def test_core_release_has_three_paths_and_twenty_dynamic_examples() -> None:
    catalog = load_catalog(ROOT / "content", minimum_terms=60)
    assert {path["slug"] for path in catalog.paths} == {
        "ship-a-product-site",
        "build-a-local-crud-tool",
        "build-an-ai-chat-assistant",
    }
    dynamic = [term for term in catalog.terms if term["example"]["mode"] in {"interactive", "stepper"}]
    assert len(dynamic) >= 20
```

- [ ] **Step 2: Confirm only one path and six dynamic examples exist**

Run: `python3 -m pytest tests/test_content_schema.py -q -k core_release`
Expected: FAIL with path and example counts.

- [ ] **Step 3: Author the local CRUD path**

Use ten chapters: `brief`, `data-model`, `local-storage`, `list-view`, `create`, `edit`, `delete-and-undo`, `validation-and-errors`, `testing`, `export-and-accept`. It must remain a browser-local project and must not introduce a user database.

- [ ] **Step 4: Author the AI chat assistant path**

Use ten chapters: `brief`, `prompt-contract`, `message-ui`, `state-model`, `context-budget`, `request-response`, `streaming-states`, `tool-boundaries`, `failure-and-safety`, `test-and-accept`. The course may teach API concepts but must not put real keys in the static client; examples use local deterministic fixtures.

- [ ] **Step 5: Complete the exact 20-example set**

Ensure interactive/stepper coverage for: `prompt`, `context-window`, `ai-agent`, `tool-calling`, `rag`, `hallucination`, `html`, `css`, `dom`, `component`, `state`, `responsive-design`, `accessibility`, `api`, `request-response`, `http-status-code`, `database`, `authentication`, `git`, `testing`.

- [ ] **Step 6: Verify paths, examples and practice coverage**

Run: `python3 -m pytest tests/test_content_schema.py tests/test_static_site.py tests/test_render_harness.py -q -k "path or example or exercise"`
Run: `RUN_HTTP_E2E=1 python3 -m pytest tests/test_browser.py -q -k "path or practice"`
Expected: PASS for three paths, 20 dynamic examples and at least one exercise per term.
Commit: `feat: complete project paths and example coverage`

### Task 14: Finish Accessibility, SEO, GitHub Pages, and Deployment Readiness

**Files:**
- Create: `.github/workflows/deploy-pages.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `scripts/vibe_terms/urls.py`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_browser.py`
- Modify: `tests/test_packaging.py`
- Modify: `docs/deployment.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: host-independent `site/` and all release tests.
- Produces: verified Pages artifact/deployment job and documented root/subpath commands.

- [ ] **Step 1: Add failing SEO, no-script, base-path and workflow tests**

Tests must assert `hreflang` + `x-default`, `DefinedTerm`, path `ItemList`/`Course`, canonical URLs, manifest/sitemap base path, no broken internal link, no account-looking strings, and a Pages workflow using official configure/upload/deploy actions.

- [ ] **Step 2: Confirm the Pages deployment contract fails**

Run: `python3 -m pytest tests/test_static_site.py tests/test_packaging.py -q -k "seo or base_path or workflow or account"`
Expected: FAIL before the workflow and new structured data exist.

- [ ] **Step 3: Implement semantic metadata and accessibility fixes**

Add localized metadata and path structured data, complete focus states/live regions, reduced motion, text equivalents for graphs, and representative high-contrast checks. Never make color or animation the only explanation.

- [ ] **Step 4: Add the Pages workflow**

Trigger on pushes to `main` and manual dispatch. Grant `contents: read`, `pages: write`, `id-token: write`; use concurrency cancellation; build with `BASE_PATH=/vibe-terms` and the repository Pages URL; run the full verifier before `actions/upload-pages-artifact` and `actions/deploy-pages`.

- [ ] **Step 5: Verify local release artifacts**

Run: `python3 -m pip install -r requirements-dev.txt`
Run: `./scripts/verify_public_site.sh`
Run: `npm ci`
Run: `npm run build`
Run: `BASE_PATH=/vibe-terms SITE_URL=https://q2955161835-debug.github.io/vibe-terms python3 scripts/build_static_site.py`
Expected: all commands exit 0; generated project-path links and assets resolve.

- [ ] **Step 6: Commit without pushing or deploying yet**

Commit: `ci: prepare verified GitHub Pages deployment`
Do not push, enable Pages, or trigger deployment until the user separately authorizes that external action.

### Task 15: Update Project Records and Run Formal Independent Acceptance

**Files:**
- Modify: `AGENTS.md` only after explicit user authorization if architecture/commands changed
- Modify: `README.md`
- Modify: `content/README.md`
- Modify: `doc/验收/模块/验收-静态站点.md`
- Create: `doc/验收/跨模块/验收-查词到项目学习.md`
- Create: `doc/验收/任务/验收-60词本地静态扩展.md`
- Modify: `doc/进展记录/<local-date>.md`
- Move after completion: `docs/superpowers/plans/2026-08-16-vibe-terms-local-static-expansion.md` to `doc/归档/<acceptance-date>/`

**Interfaces:**
- Consumes: completed tasks, test evidence and deployed URL when deployment is authorized.
- Produces: reproducible acceptance record and a clean task branch ready for local merge.

- [ ] **Step 1: Update long-lived module and cross-module acceptance definitions**

Module checks cover content, search, knowledge, paths, term pages, practice, local storage, i18n/SEO and packaging. The cross-module file follows one user from global search to term example, inline exercise, related path chapter, local progress restoration and export.

- [ ] **Step 2: Run the complete local gate**

Run: `./scripts/verify_public_site.sh`
Run: `RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh`
Run: `npm ci && npm run build`
Expected: every command exits 0; test counts are recorded from actual output.

- [ ] **Step 3: Dispatch a fresh independent acceptance subagent**

The agent receives only this specification, task diff, acceptance files and run commands. It checks the requested scope and directly affected flows, not unrelated full-repository work. Any failed or conditional item blocks merge to `main` unless the user explicitly authorizes otherwise.

- [ ] **Step 4: If deployment is authorized, push and read back authoritative state**

Verify the GitHub branch/commit, Actions run, Pages deployment URL and live HTTP results for `/vibe-terms/`, `/vibe-terms/zh-cn/`, one term, knowledge overview, one path chapter, practice index and one asset. A green local build alone is not deployment proof.

- [ ] **Step 5: Record the final conclusion and archive the completed plan**

The task acceptance conclusion is exactly one of `通过`、`有条件通过`、`不通过`、`阻塞`、`未执行`. On `通过`, move this plan and the task acceptance record into the dated archive and update the progress record with file list, test evidence, deployment status and any external paths changed.

- [ ] **Step 6: Finish the branch according to repository rules**

On `通过`, locally merge the task branch into `main`, verify `main`, then delete the old task branch. Push is separate and requires the user's decision. If acceptance is not `通过`, keep the branch and report the exact blocker.

---

## Final Verification Matrix

| Area | Command or check | Required result |
| --- | --- | --- |
| Content | `python3 -m pytest tests/test_content_schema.py -q` | 60 terms, 8 locales, 3 paths, examples/exercises and valid relations |
| Static output | `python3 -m pytest tests/test_static_site.py tests/test_packaging.py -q` | routes, links, indexes, SEO and archives pass |
| JavaScript | `npm run test:js` | search, schedule, grading, queue and migration pass |
| Render harness | `python3 -m pytest tests/test_render_harness.py -q` | desktop/mobile rendering, examples and no overflow pass |
| HTTP E2E | `RUN_HTTP_E2E=1 python3 -m pytest tests/test_browser.py -q` | real navigation and IndexedDB persistence pass |
| Sites adapter | `npm ci && npm run build` | thin adapter packages the same static site |
| GitHub Pages build | `BASE_PATH=/vibe-terms SITE_URL=https://q2955161835-debug.github.io/vibe-terms python3 scripts/build_static_site.py` | no root-path leakage or broken resources |
| Privacy | generated-output scan | no login UI, user database, real secret or analytics SDK |
| Live deployment | browser/HTTP read-back after authorized push | Pages commit and representative routes match the accepted build |

## Plan Self-review Record

- Spec coverage: search position, taxonomy depth, rich term pages, examples, exercises, knowledge map, project paths, 60-term expansion, local-only persistence and GitHub Pages each map to explicit tasks.
- Scope: stops at the 60-term M2 release; 180/500 expansion is intentionally deferred to new plans.
- Type consistency: all Python tasks use `BuildConfig`, `Catalog`, `load_catalog`, `UrlBuilder` and `build_site`; all browser tasks preserve existing `VibeCore` exports and add the five named functions.
- Safety: execution is gated on receipt of the user's pending web files; no worktree, push, deployment or `AGENTS.md` edit is implied.
- Placeholder scan: there are no undecided feature requirements or abbreviated implementation bodies.

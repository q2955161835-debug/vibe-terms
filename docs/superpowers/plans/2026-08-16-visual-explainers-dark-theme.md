# 500 Visual Explainers and Dark Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 500 个术语增加按概念定制、仅维护英文与简体中文的可视化解读，并让现有站点及新图解完整支持浅色、暗色和跟随系统主题。

**Architecture:** 新增独立的 `content/explainers/<slug>.yaml` 内容层、严格验证器、14 种白名单视觉模式、静态 Python 渲染器和通用浏览器状态控制器。词条页先渲染专属图解，再完整保留已有四阶段示例；图解只在当前词条页内联，语言通过纯函数回退，主题通过共享语义变量统一控制。

**Tech Stack:** Python 3、PyYAML、静态 HTML、CSS、Vanilla JavaScript、Node test runner、pytest、Playwright、GitHub Pages、vinext Sites adapter、`@phosphor-icons/core@2.1.1` MIT 子集。

## Global Constraints

- 必须覆盖当前目录中的 500/500 个规范术语；禁止通用空图或缺失图解静默回退。
- 图解只维护 `en` 与 `zh-cn`；`zh-cn`、`zh-tw` 读取简体中文，`en`、`ja`、`ko`、`de`、`ru` 读取英文。
- 原有定义、四阶段文字说明、小练、项目路径、来源、相关词、搜索和本地进度只增不减。
- 关闭 JavaScript 后必须保留首状态画布、全部状态标题和结论记录。
- 禁止 `eval`、用户代码执行、第三方 iframe、远程运行时依赖和把 YAML 字符串作为 HTML 执行。
- 所有站内 URL 和资产 URL 继续通过 `UrlBuilder`，根路径和 `/vibe-terms` 必须同时工作。
- 组件只能消费主题语义变量；浅色、暗色和系统主题均需通过对比度与浏览器回归。
- 不创建 Git worktree；使用现有分支 `codex/feat-visual-explainers-dark-theme`。
- 每批只做快速自动化检查和 Git 提交；不做子任务独立验收，全部实现完成后统一独立验收一次。
- `site/`、`dist/`、截图、浏览器 profile 和临时审计产物不得提交。
- 未获得用户对 `AGENTS.md` 的明确授权前不得修改该文件；README、内容工作流和部署文档按实现同步更新。

---

## File Structure

| Path | Responsibility |
|---|---|
| `content/explainers/<slug>.yaml` | 单个术语的模式、状态、场景结构和 `en`/`zh-cn` 图解文案 |
| `scripts/vibe_terms/explainers.py` | 数据读取、模式白名单、交叉引用验证、locale 回退与批量加载 |
| `scripts/vibe_terms/explainer_renderers/base.py` | 转义、通用标题、状态控制、静态记录和节点原语 |
| `scripts/vibe_terms/explainer_renderers/flows.py` | sequence、pipeline、request-response、lifecycle、timeline |
| `scripts/vibe_terms/explainer_renderers/structures.py` | anatomy、hierarchy、data-mapping、boundary、layout |
| `scripts/vibe_terms/explainer_renderers/decisions.py` | compare、code-result、state-machine、evidence |
| `scripts/vibe_terms/explainer_renderers/__init__.py` | 模式注册表与 `render_visual_explainer()` 稳定入口 |
| `web/explainers.css` | 图解画布、状态、响应式和主题适配 |
| `web/explainers.js` | 状态选择、键盘导航、ARIA 和实时结论 |
| `web/styles.css` | 全站浅色/暗色/系统语义变量真源 |
| `web/clarity.css` | 只消费语义变量的现有清晰度布局层 |
| `scripts/audit_explainers.py` | 缺失文件、结构、双语 key、重复签名和领域统计 CLI |
| `scripts/sync_phosphor_icons.py` | 从锁定依赖复制允许使用的 Phosphor 图标子集 |
| `web/icons/` | 已筛选的 MIT 图标资源和许可记录 |
| `tests/test_explainers.py` | 内容解析、验证、回退和 500 覆盖测试 |
| `tests/test_explainer_renderers.py` | 14 种模式的静态渲染与安全测试 |
| `tests/test_theme_contract.py` | 语义变量、禁止浅色常量和主题对比测试 |
| `tests/js/explainers.test.cjs` | 浏览器状态控制器单元测试 |
| `tests/test_browser.py` | 真实主题、图解交互、locale 回退和移动端 E2E |
| `scripts/vibe_terms/render.py` | 词条页接入统一图解入口、复制共享资产 |

---

### Task 1: Establish the semantic dark-theme contract

**Files:**
- Create: `tests/test_theme_contract.py`
- Modify: `web/styles.css`
- Modify: `web/clarity.css`
- Modify: `tests/test_browser.py`

**Interfaces:**
- Consumes: `html[data-theme]` 与 `web/app.js` 中现有 `light -> dark -> system` 主题循环。
- Produces: `--canvas`、`--panel`、`--text-primary` 等语义变量，以及 `_contrast(foreground: str, background: str) -> float` 浏览器测试辅助函数。

- [ ] **Step 1: Write a failing static theme-contract test**

```python
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
THEME_TOKENS = {
    "--canvas", "--canvas-subtle", "--panel", "--panel-raised",
    "--panel-muted", "--text-primary", "--text-secondary", "--text-faint",
    "--border", "--border-strong", "--accent", "--accent-surface",
    "--accent-contrast", "--focus-ring",
}


def test_styles_define_every_semantic_token_for_light_dark_and_system() -> None:
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    for selector in (':root[data-theme="light"]', ':root[data-theme="dark"]'):
        block = css.split(selector, 1)[1].split("}", 1)[0]
        assert THEME_TOKENS <= set(re.findall(r"--[a-z-]+(?=\s*:)", block))
    assert '@media (prefers-color-scheme: dark)' in css
    assert ':root[data-theme="system"]' in css


def test_clarity_components_do_not_force_light_surfaces() -> None:
    css = (ROOT / "web" / "clarity.css").read_text(encoding="utf-8")
    for forbidden in ("background: #fff", "background: #ffffff", "color: #11151c"):
        assert forbidden not in css.lower()
```

- [ ] **Step 2: Run the static test and confirm the current light constants fail**

Run: `python -m pytest tests/test_theme_contract.py -q`

Expected: FAIL because `clarity.css` still contains forced white panels and `styles.css` does not define the full semantic contract.

- [ ] **Step 3: Define complete light and dark token blocks**

Use this exact public contract in `web/styles.css`; values may be tuned only while preserving the token names:

```css
:root[data-theme="light"] {
  --canvas: #ffffff;
  --canvas-subtle: #f7f8fa;
  --panel: #fbfbfc;
  --panel-raised: #ffffff;
  --panel-muted: #f1f3f6;
  --text-primary: #12151c;
  --text-secondary: #515966;
  --text-faint: #707887;
  --border: #e2e5eb;
  --border-strong: #c8ced8;
  --accent: #3458df;
  --accent-surface: #eef1ff;
  --accent-contrast: #ffffff;
  --focus-ring: #6f8cff;
}

:root[data-theme="dark"] {
  --canvas: #0d1117;
  --canvas-subtle: #111721;
  --panel: #151c27;
  --panel-raised: #1a2330;
  --panel-muted: #202b39;
  --text-primary: #f5f7fa;
  --text-secondary: #c0c8d4;
  --text-faint: #96a2b2;
  --border: #2b3747;
  --border-strong: #435268;
  --accent: #91a7ff;
  --accent-surface: #23315f;
  --accent-contrast: #0d1117;
  --focus-ring: #a9b8ff;
}
```

Add matching light values inside `@media (prefers-color-scheme: light)` and matching dark values inside `@media (prefers-color-scheme: dark)` for `:root[data-theme="system"]`. Map legacy variables such as `--bg`, `--surface`, `--text`, `--muted` and `--line` to the semantic values during migration.

- [ ] **Step 4: Replace theme-sensitive constants in `clarity.css`**

Replace component surfaces and text with variables, including topbar, brand, search, domain tabs, term cards, term detail, four-stage examples, forms, prompts and mobile menus:

```css
.topbar { background: color-mix(in srgb, var(--canvas) 96%, transparent); }
.term-card,
.term-reference-grid > section { background: var(--panel-raised); border-color: var(--border); }
.term-card strong,
.section-title h2 { color: var(--text-primary); }
.term-card p,
.section-title > p { color: var(--text-secondary); }
```

- [ ] **Step 5: Add computed-color browser assertions**

```python
def _rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.removeprefix("rgb(").removesuffix(")").split(", "))


def _luminance(rgb: tuple[int, int, int]) -> float:
    values = [channel / 255 for channel in rgb]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    high, low = sorted((_luminance(_rgb(foreground)), _luminance(_rgb(background))), reverse=True)
    return (high + 0.05) / (low + 0.05)
```

In `test_theme_cycle_persists`, collect computed foreground/background values for `.topbar`, `.term-card`, `.term-card-example`, `pre`, buttons and inputs in dark mode. Assert text contrast `>= 4.5` and component border/focus contrast `>= 3.0` for sampled pairs.

- [ ] **Step 6: Run targeted theme tests**

Run: `python -m pytest tests/test_theme_contract.py tests/test_browser.py::test_theme_cycle_persists -q`

Expected: PASS with the page returning to its original theme after the test.

- [ ] **Step 7: Commit the dark-theme foundation**

```bash
git add web/styles.css web/clarity.css tests/test_theme_contract.py tests/test_browser.py
git commit -m "fix: establish accessible dark theme contract"
```

---

### Task 2: Build the explainer parser, validation, and locale fallback

**Files:**
- Create: `scripts/vibe_terms/explainers.py`
- Create: `scripts/audit_explainers.py`
- Create: `tests/test_explainers.py`
- Create: `tests/fixtures/explainers/css.yaml`

**Interfaces:**
- Consumes: `content/explainers/<slug>.yaml`, canonical term slug sets and optional domain subsets.
- Produces: `PATTERNS`, `resolve_explainer_locale(locale: str) -> str`, `load_explainer(path: Path, expected_slug: str) -> dict[str, Any]`, `load_explainers(content_root: Path, expected_slugs: set[str]) -> dict[str, dict[str, Any]]`.

- [ ] **Step 1: Write failing parser and fallback tests**

```python
import pytest
from scripts.vibe_terms.explainers import load_explainer, resolve_explainer_locale


@pytest.mark.parametrize(
    ("page_locale", "copy_locale"),
    [("en", "en"), ("zh-cn", "zh-cn"), ("zh-tw", "zh-cn"),
     ("ja", "en"), ("ko", "en"), ("de", "en"), ("ru", "en")],
)
def test_visual_copy_locale_is_explicit(page_locale: str, copy_locale: str) -> None:
    assert resolve_explainer_locale(page_locale) == copy_locale


def test_explainer_rejects_missing_focus_targets(tmp_path) -> None:
    path = tmp_path / "css.yaml"
    path.write_text("""
schema_version: 1
term: css
pattern: code-result
complexity: 2
copy:
  en: {heading: CSS result, intro: Follow the rule, states: {base: {label: Base, conclusion: Result}}, labels: {source: Source}}
  zh-cn: {heading: CSS 结果, intro: 观察规则, states: {base: {label: 基础, conclusion: 结果}}, labels: {source: 源码}}
states: [{id: base, focus: [missing], values: {}}]
scene: {nodes: [{id: source, role: code, label_key: source, value: rule}], relations: []}
""", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown focus target missing"):
        load_explainer(path, "css")
```

- [ ] **Step 2: Run tests and confirm the module is missing**

Run: `python -m pytest tests/test_explainers.py -q`

Expected: FAIL with `ModuleNotFoundError: scripts.vibe_terms.explainers`.

- [ ] **Step 3: Implement the stable parser API**

```python
PATTERNS = frozenset({
    "anatomy", "compare", "sequence", "state-machine", "request-response",
    "pipeline", "hierarchy", "code-result", "data-mapping", "lifecycle",
    "boundary", "layout", "timeline", "evidence",
})

COPY_LOCALE = {
    "en": "en", "zh-cn": "zh-cn", "zh-tw": "zh-cn",
    "ja": "en", "ko": "en", "de": "en", "ru": "en",
}


def resolve_explainer_locale(locale: str) -> str:
    try:
        return COPY_LOCALE[locale]
    except KeyError as error:
        raise ValueError(f"unsupported page locale: {locale}") from error
```

Implement strict checks for schema version, slug, pattern, complexity `1..4`, exact copy locales, aligned state/label keys, unique IDs, focus targets, relation endpoints, `value_from` keys and escaped scalar types. Return normalized dictionaries without inserting generic copy.

- [ ] **Step 4: Add a complete CSS fixture and rejection matrix**

Use the schema example from the approved design for `tests/fixtures/explainers/css.yaml`. Parametrize mutations for unknown pattern, missing locale, mismatched state keys, duplicate node IDs, unknown relation endpoints and `complexity: 5`; each mutation must assert its exact error substring.

- [ ] **Step 5: Add the audit CLI contract**

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="*", default=[])
    parser.add_argument("--list-missing", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args()
```

The CLI loads the current catalog only to select canonical slugs and domains, then validates the requested explainer subset. `--list-missing` prints one slug per line; `--require-complete` exits non-zero for a missing or extra file. Output includes counts by domain, pattern and complexity.

- [ ] **Step 6: Run parser tests and the fixture audit**

Run: `python -m pytest tests/test_explainers.py -q`

Run: `python -X utf8 scripts/audit_explainers.py --domains frontend-engineering --list-missing`

Expected: tests PASS; CLI prints the exact missing slugs for the requested domain without modifying files.

- [ ] **Step 7: Commit the content contract**

```bash
git add scripts/vibe_terms/explainers.py scripts/audit_explainers.py tests/test_explainers.py tests/fixtures/explainers/css.yaml
git commit -m "feat: define visual explainer content contract"
```

---

### Task 3: Implement the 14-pattern static renderer registry

**Files:**
- Create: `scripts/vibe_terms/explainer_renderers/__init__.py`
- Create: `scripts/vibe_terms/explainer_renderers/base.py`
- Create: `scripts/vibe_terms/explainer_renderers/flows.py`
- Create: `scripts/vibe_terms/explainer_renderers/structures.py`
- Create: `scripts/vibe_terms/explainer_renderers/decisions.py`
- Create: `tests/test_explainer_renderers.py`

**Interfaces:**
- Consumes: one validated explainer dictionary and page locale.
- Produces: `render_visual_explainer(explainer: dict[str, Any], page_locale: str) -> str` with escaped static HTML and all-state transcript.

- [ ] **Step 1: Write a failing registry coverage test**

```python
from scripts.vibe_terms.explainers import PATTERNS
from scripts.vibe_terms.explainer_renderers import RENDERERS, render_visual_explainer


def test_every_allowed_pattern_has_exactly_one_renderer() -> None:
    assert set(RENDERERS) == set(PATTERNS)


def test_renderer_escapes_code_and_keeps_every_state_in_transcript(css_explainer) -> None:
    broken = deepcopy(css_explainer)
    broken["scene"]["nodes"][0]["value"] = "</code><script>alert(1)</script>"
    html = render_visual_explainer(broken, "zh-tw")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert 'data-explainer-locale="zh-cn"' in html
    assert html.count('class="visual-transcript-item"') == len(broken["states"])
```

- [ ] **Step 2: Run and confirm the renderer package is missing**

Run: `python -m pytest tests/test_explainer_renderers.py -q`

Expected: FAIL importing `scripts.vibe_terms.explainer_renderers`.

- [ ] **Step 3: Implement shared primitives in `base.py`**

Provide escaped helpers with these signatures:

```python
def render_node(node: dict[str, Any], copy: dict[str, Any], state: dict[str, Any]) -> str:
    label = _esc(copy["labels"][node["label_key"]])
    value = state["values"].get(node.get("value_from"), node.get("value", ""))
    active = " is-active" if node["id"] in state["focus"] else ""
    return (
        f'<article class="visual-node visual-node--{_esc(node["role"])}{active}" '
        f'data-explainer-node="{_esc(node["id"])}"><strong>{label}</strong>'
        f'<code>{_esc(value)}</code></article>'
    )


def render_state_controls(states: list[dict[str, Any]], copy: dict[str, Any]) -> str:
    if len(states) < 2:
        return ""
    buttons = "".join(
        f'<button type="button" data-explainer-state-control="{_esc(state["id"])}" '
        f'aria-pressed="{str(index == 0).lower()}">{_esc(copy["states"][state["id"]]["label"])}</button>'
        for index, state in enumerate(states)
    )
    return f'<div class="visual-state-controls" role="group">{buttons}</div>'


def render_transcript(states: list[dict[str, Any]], copy: dict[str, Any]) -> str:
    items = "".join(
        f'<li class="visual-transcript-item"><strong>{_esc(copy["states"][state["id"]]["label"])}</strong>'
        f'<p>{_esc(copy["states"][state["id"]]["conclusion"])}</p></li>'
        for state in states
    )
    return f'<ol class="visual-transcript">{items}</ol>'


def render_shell(explainer: dict[str, Any], page_locale: str, canvas: str) -> str:
    copy_locale = resolve_explainer_locale(page_locale)
    copy = explainer["copy"][copy_locale]
    states = explainer["states"]
    first = states[0]["id"]
    return (
        f'<section data-visual-explainer data-explainer-pattern="{_esc(explainer["pattern"])}" '
        f'data-explainer-locale="{_esc(copy_locale)}"><h2>{_esc(copy["heading"])}</h2>'
        f'<p>{_esc(copy["intro"])}</p>{render_state_controls(states, copy)}{canvas}'
        f'<p data-explainer-conclusion aria-live="polite">{_esc(copy["states"][first]["conclusion"])}</p>'
        f'{render_transcript(states, copy)}</section>'
    )
```

`render_shell` must add `data-visual-explainer`, `data-explainer-pattern`, `data-explainer-locale`, a named button group only when state count is greater than one, an `aria-live="polite"` conclusion and an ordered transcript.

- [ ] **Step 4: Implement the flow renderers**

In `flows.py`, implement `render_sequence`, `render_pipeline`, `render_request_response`, `render_lifecycle` and `render_timeline`. They share node primitives but produce distinct semantic class names and region ordering. Request/response must render two named endpoints plus a contract panel; timeline must preserve chronological order even when a state highlights a branch.

- [ ] **Step 5: Implement the structure renderers**

In `structures.py`, implement `render_anatomy`, `render_hierarchy`, `render_data_mapping`, `render_boundary` and `render_layout`. Hierarchy uses nested lists, data mapping uses source/target columns, boundary separates trust zones, and layout exposes dimension labels as text rather than decorative glyphs.

- [ ] **Step 6: Implement the decision renderers and registry**

In `decisions.py`, implement `render_compare`, `render_code_result`, `render_state_machine` and `render_evidence`. Register all functions in `__init__.py`:

```python
RENDERERS = {
    "anatomy": render_anatomy,
    "compare": render_compare,
    "sequence": render_sequence,
    "state-machine": render_state_machine,
    "request-response": render_request_response,
    "pipeline": render_pipeline,
    "hierarchy": render_hierarchy,
    "code-result": render_code_result,
    "data-mapping": render_data_mapping,
    "lifecycle": render_lifecycle,
    "boundary": render_boundary,
    "layout": render_layout,
    "timeline": render_timeline,
    "evidence": render_evidence,
}
```

- [ ] **Step 7: Test one full fixture per pattern**

Build in-memory fixtures with unique node roles and 1–4 states. Assert pattern-specific wrappers, unique node IDs, no controls for one state, controls for multiple states, transcript completeness, English fallback for `de`, and Simplified Chinese fallback for `zh-tw`.

Run: `python -m pytest tests/test_explainer_renderers.py -q`

Expected: all 14 pattern cases PASS.

- [ ] **Step 8: Commit the renderer registry**

```bash
git add scripts/vibe_terms/explainer_renderers tests/test_explainer_renderers.py
git commit -m "feat: render fourteen visual explainer patterns"
```

---

### Task 4: Add explainer interaction, responsive styles, and licensed icons

**Files:**
- Create: `web/explainers.js`
- Create: `web/explainers.css`
- Create: `tests/js/explainers.test.cjs`
- Create: `scripts/sync_phosphor_icons.py`
- Create: `web/icons/LICENSE.phosphor.txt`
- Create: `web/icons/*.svg`
- Modify: `package.json`
- Modify: `package-lock.json`

**Interfaces:**
- Consumes: renderer attributes `data-visual-explainer`, `data-explainer-state-control`, `data-explainer-state`, `data-explainer-node`, `data-explainer-conclusion`.
- Produces: `globalThis.VibeExplainers.mount(root)`, keyboard-safe state switching and responsive themed visuals.

- [ ] **Step 1: Add failing JS behavior tests**

```javascript
const { mount } = require('../../web/explainers.js');

test('mount activates one state and preserves the transcript', () => {
  const root = makeExplainerFixture(['base', 'override', 'fixed']);
  assert.equal(mount(root), true);
  root.querySelector('[data-explainer-state-control="override"]').click();
  assert.equal(root.querySelector('[aria-pressed="true"]').dataset.explainerStateControl, 'override');
  assert.equal(root.querySelector('[data-explainer-state="override"]').getAttribute('aria-current'), 'step');
  assert.equal(root.querySelectorAll('.visual-transcript-item').length, 3);
});

test('arrow keys move between state buttons without wrapping page focus', () => {
  const root = makeExplainerFixture(['one', 'two', 'three']);
  mount(root);
  root.querySelector('[data-explainer-state-control="one"]').dispatchEvent(key('ArrowRight'));
  assert.equal(document.activeElement.dataset.explainerStateControl, 'two');
});
```

- [ ] **Step 2: Run and confirm the runtime is missing**

Run: `node --test tests/js/explainers.test.cjs`

Expected: FAIL because `web/explainers.js` does not exist.

- [ ] **Step 3: Implement the generic runtime**

Use the existing UMD shape from `web/examples.js`. Export `mount` and `mountAll`. The activation function must update `aria-pressed`, `aria-current`, `is-active`, visible state values and conclusion text; it must never insert HTML from content.

- [ ] **Step 4: Add responsive pattern styles**

Define shared canvas tokens and pattern grids in `web/explainers.css`. Desktop patterns may use 2–4 columns; under `720px`, panels stack or use an internal overflow container while `body` remains overflow-free. State buttons may scroll horizontally inside the module. Add:

```css
@media (prefers-reduced-motion: reduce) {
  [data-visual-explainer] * { scroll-behavior: auto; transition-duration: 0.01ms !important; }
}
```

All colors must use the Task 1 semantic theme contract.

- [ ] **Step 5: Add the Phosphor icon subset reproducibly**

Run `npm install --save-dev @phosphor-icons/core@2.1.1` and commit the resulting lockfile. Implement `scripts/sync_phosphor_icons.py` with an explicit allowlist:

```python
ICON_NAMES = (
    "arrow-right", "browser", "brackets-curly", "check-circle", "code",
    "database", "file", "folder", "git-branch", "lock", "magnifying-glass",
    "server", "shield-check", "terminal", "warning-circle",
)
```

The script copies only those vendor SVGs and the upstream MIT license into `web/icons/`. Do not hand-edit SVG path data.

Source paths are `node_modules/@phosphor-icons/core/assets/regular/<name>.svg`; copy `node_modules/@phosphor-icons/core/LICENSE` verbatim to `web/icons/LICENSE.phosphor.txt`.

Run: `python scripts/sync_phosphor_icons.py --check`

Expected: PASS and exactly the allowlisted files plus the license exist.

- [ ] **Step 6: Run JS, CSS contract, and icon checks**

Run: `node --test tests/js/explainers.test.cjs`

Run: `python -m pytest tests/test_theme_contract.py -q`

Run: `python scripts/sync_phosphor_icons.py --check`

Expected: all PASS.

- [ ] **Step 7: Commit the browser layer**

```bash
git add web/explainers.js web/explainers.css web/icons scripts/sync_phosphor_icons.py tests/js/explainers.test.cjs package.json package-lock.json
git commit -m "feat: add accessible visual explainer runtime"
```

---

### Task 5: Author and visually calibrate the 14 representative explainers

**Files:**
- Create: `content/explainers/css.yaml`
- Create: `content/explainers/component.yaml`
- Create: `content/explainers/mock.yaml`
- Create: `content/explainers/request.yaml`
- Create: `content/explainers/state.yaml`
- Create: `content/explainers/api.yaml`
- Create: `content/explainers/retrieval-augmented-generation.yaml`
- Create: `content/explainers/dom.yaml`
- Create: `content/explainers/orm.yaml`
- Create: `content/explainers/access-token.yaml`
- Create: `content/explainers/authentication.yaml`
- Create: `content/explainers/box-model.yaml`
- Create: `content/explainers/git.yaml`
- Create: `content/explainers/testing.yaml`
- Create: `tests/fixtures/explainer-gallery.html`
- Modify: `tests/test_explainer_renderers.py`

**Interfaces:**
- Consumes: strict schema and 14 renderers from Tasks 2–3.
- Produces: one gold-standard production explainer per pattern and a deterministic local gallery fixture.

- [ ] **Step 1: Write a failing representative-coverage test**

```python
REPRESENTATIVES = {
    "anatomy": "component", "compare": "mock", "sequence": "request",
    "state-machine": "state", "request-response": "api",
    "pipeline": "retrieval-augmented-generation", "hierarchy": "dom",
    "code-result": "css", "data-mapping": "orm", "lifecycle": "access-token",
    "boundary": "authentication", "layout": "box-model", "timeline": "git",
    "evidence": "testing",
}


def test_gold_explainers_cover_each_pattern_once() -> None:
    explainers = load_explainers(CONTENT, set(REPRESENTATIVES.values()))
    assert {item["pattern"] for item in explainers.values()} == set(REPRESENTATIVES)
```

- [ ] **Step 2: Run and confirm all production files are missing**

Run: `python -m pytest tests/test_explainer_renderers.py -q -k gold`

Expected: FAIL listing the 14 missing slugs.

- [ ] **Step 3: Author the 14 files from canonical English meaning**

For each file, write term-specific `en` and `zh-cn` headings, intros, state labels and conclusions. Use the CSS reference principle for `css.yaml`: three states named base/override/fixed, concrete rule text, computed value and button result. Do not copy the reference site's sentences or exact sample names.

Each of the other files must model its own objects: component parts, mock-vs-real boundary, request sequence, allowed state transitions, API contract, retrieval stages, DOM ancestry, ORM field mapping, token lifecycle, authentication trust boundary, box dimensions, Git branch history and test evidence.

- [ ] **Step 4: Generate the deterministic gallery fixture**

Render one section per representative into `tests/fixtures/explainer-gallery.html` using only the production renderer and assets. The fixture is test-only and contains both `en` and `zh-cn` pages linked from a local index.

- [ ] **Step 5: Run parser and renderer tests**

Run: `python -m pytest tests/test_explainers.py tests/test_explainer_renderers.py -q`

Run: `python -X utf8 scripts/audit_explainers.py --domains frontend-engineering ai-vibe backend-apis data-databases security-privacy git-collaboration testing-debugging --list-missing`

Expected: the 14 authored files pass; the audit still reports uncreated slugs outside the representative set.

- [ ] **Step 6: Perform the first local visual comparison**

Open the gallery in the Browser plugin at 1280×720 and 390×844. Check light/dark, multi-state buttons, code wrapping, focus, internal overflow and console errors. Compare the CSS section against `https://vibe-hub.org/css` for information hierarchy and state clarity only. Record concrete mismatches in the implementation notes; fix P0–P2 renderer issues before continuing content production.

- [ ] **Step 7: Commit the gold content set**

```bash
git add content/explainers tests/fixtures/explainer-gallery.html tests/test_explainer_renderers.py
git commit -m "content: add fourteen gold visual explainers"
```

---

### Task 6: Add full-corpus audit gates before bulk authoring

**Files:**
- Modify: `scripts/audit_explainers.py`
- Modify: `scripts/audit_full_content.py`
- Modify: `tests/test_explainers.py`

**Interfaces:**
- Consumes: partial or complete `content/explainers/` plus canonical term/domain data.
- Produces: deterministic duplicate-signature detection, two-language alignment report and final 500-file gate.

- [ ] **Step 1: Write failing duplicate and generic-copy tests**

```python
def test_complete_corpus_rejects_duplicate_scene_signatures(tmp_path) -> None:
    write_valid_explainer(tmp_path, "css")
    write_valid_explainer(tmp_path, "html", copy_from="css")
    with pytest.raises(ValueError, match="duplicate explainer signature: css, html"):
        audit_explainer_set(tmp_path, {"css", "html"})


def test_every_explainer_uses_term_specific_heading(complete_explainers) -> None:
    for slug, item in complete_explainers.items():
        canonical = canonical_term(slug)
        assert item["copy"]["en"]["heading"].casefold() != canonical.casefold()
        assert item["copy"]["zh-cn"]["heading"] != item["copy"]["zh-cn"]["intro"]
```

- [ ] **Step 2: Run and confirm the audit lacks these checks**

Run: `python -m pytest tests/test_explainers.py -q -k "duplicate or specific"`

Expected: FAIL because `audit_explainer_set` and signature checks are absent.

- [ ] **Step 3: Implement normalized signatures and copy checks**

Build the signature from pattern, state IDs, node roles, relation topology and non-localized structural values. Exclude headings and translated labels so copy-only changes cannot hide a duplicated scene. Reject exact duplicate signatures; report near-duplicate state/role signatures as warnings grouped by domain.

- [ ] **Step 4: Integrate explainer audit into full content audit**

`scripts/audit_full_content.py` must call the complete audit after its existing term/locale checks and print:

```text
Visual explainers passed: 500 files, 14 patterns, en/zh-cn aligned, 0 duplicate signatures.
```

During partial authoring, domain commands continue using `scripts/audit_explainers.py`; the full audit remains red until all 500 files exist.

- [ ] **Step 5: Run targeted audit tests**

Run: `python -m pytest tests/test_explainers.py -q`

Expected: PASS for fixtures; `python scripts/audit_full_content.py` still fails with an exact missing-file count until Tasks 7–12 complete.

- [ ] **Step 6: Commit the corpus quality gate**

```bash
git add scripts/audit_explainers.py scripts/audit_full_content.py tests/test_explainers.py
git commit -m "test: enforce custom visual explainer corpus"
```

---

### Task 7: Author UI/UX explainers (115 terms)

**Files:**
- Create/Modify: `content/explainers/*.yaml` for every term whose `primary_domain` is `ui-ux`

**Interfaces:**
- Consumes: 14 gold patterns and the canonical English definition for each UI/UX term.
- Produces: exactly 115 valid `ui-ux` explainers, including the already authored representatives in that domain.

- [ ] **Step 1: Capture the exact domain worklist**

Run: `python -X utf8 scripts/audit_explainers.py --domains ui-ux --list-missing > try/ui-ux-explainer-worklist.txt`

Expected: one missing canonical slug per line; the file stays in `try/` and is not committed.

- [ ] **Step 2: Author anatomy, layout, compare and state scenes**

For every listed slug, choose the pattern based on the term's observable behavior. UI controls model visible states and accessibility; layout terms model containers and dimensions; design styles compare concrete visual rules; research terms model evidence or sequence. Each file contains only `en` and `zh-cn` copy and unique scene values.

- [ ] **Step 3: Validate the complete UI/UX domain**

Run: `python -X utf8 scripts/audit_explainers.py --domains ui-ux --require-complete`

Expected: `ui-ux: 115/115`, no duplicate signature and aligned bilingual keys.

- [ ] **Step 4: Sample one term per used pattern through the renderer**

Run: `python -m pytest tests/test_explainer_renderers.py tests/test_explainers.py -q`

Expected: PASS; no shared renderer regression introduced by production data.

- [ ] **Step 5: Commit the UI/UX corpus**

```bash
git add content/explainers
git commit -m "content: add UI UX visual explainers"
```

---

### Task 8: Author frontend and web-network explainers (85 terms)

**Files:**
- Create/Modify: `content/explainers/*.yaml` for `frontend-engineering` and `web-network`

**Interfaces:**
- Consumes: canonical term metadata and all registered patterns.
- Produces: exactly 55 frontend and 30 web/network explainers.

- [ ] **Step 1: List the exact missing slugs**

Run: `python -X utf8 scripts/audit_explainers.py --domains frontend-engineering web-network --list-missing > try/frontend-web-explainer-worklist.txt`

- [ ] **Step 2: Author browser, code-result, hierarchy and request scenes**

Use code-result for CSS/HTML/configuration where source visibly changes output; hierarchy for DOM and document structure; request-response for HTTP/WebSocket/fetch; layout/state patterns for responsive and browser behavior. Preserve protocols, selectors, tags, ports, methods and status values as structural data rather than translated prose.

- [ ] **Step 3: Validate both domains**

Run: `python -X utf8 scripts/audit_explainers.py --domains frontend-engineering web-network --require-complete`

Expected: `frontend-engineering: 55/55` and `web-network: 30/30`.

- [ ] **Step 4: Run parser and renderer regression**

Run: `python -m pytest tests/test_explainers.py tests/test_explainer_renderers.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the frontend/network corpus**

```bash
git add content/explainers
git commit -m "content: add frontend and network visual explainers"
```

---

### Task 9: Author AI/Vibe and product-requirement explainers (90 terms)

**Files:**
- Create/Modify: `content/explainers/*.yaml` for `ai-vibe` and `product-requirements`

**Interfaces:**
- Consumes: English canonical meanings, current project examples and pattern registry.
- Produces: exactly 60 AI/Vibe and 30 product/requirements explainers.

- [ ] **Step 1: List the exact missing slugs**

Run: `python -X utf8 scripts/audit_explainers.py --domains ai-vibe product-requirements --list-missing > try/ai-product-explainer-worklist.txt`

- [ ] **Step 2: Author pipelines, boundaries, lifecycles and evidence scenes**

AI concepts must distinguish model input, context, retrieval, tool boundary, model output and verification. Product concepts must visualize decision evidence, prioritization, user flow or lifecycle rather than depicting generic documents. Keep Token, Grounding, Guardrail, Agent, ReAct and prompt roles semantically distinct.

- [ ] **Step 3: Validate both domains**

Run: `python -X utf8 scripts/audit_explainers.py --domains ai-vibe product-requirements --require-complete`

Expected: `ai-vibe: 60/60` and `product-requirements: 30/30`.

- [ ] **Step 4: Run content regression**

Run: `python -m pytest tests/test_explainers.py tests/test_full_corpus.py -q`

Expected: PASS for authored content and existing term translations.

- [ ] **Step 5: Commit the AI/product corpus**

```bash
git add content/explainers
git commit -m "content: add AI and product visual explainers"
```

---

### Task 10: Author backend, data, and security explainers (90 terms)

**Files:**
- Create/Modify: `content/explainers/*.yaml` for `backend-apis`, `data-databases`, `security-privacy`

**Interfaces:**
- Consumes: request-response, data-mapping, lifecycle, boundary and state-machine patterns.
- Produces: exactly 35 backend, 30 data and 25 security explainers.

- [ ] **Step 1: List the exact missing slugs**

Run: `python -X utf8 scripts/audit_explainers.py --domains backend-apis data-databases security-privacy --list-missing > try/backend-data-security-explainer-worklist.txt`

- [ ] **Step 2: Author contracts, mappings, transactions and trust boundaries**

Backend scenes must show caller, contract, handler and result; data scenes must show record/field/key/transaction relationships; security scenes must identify protected asset, trust boundary, validation or permission decision and observable result. Never render real secrets, tokens, credentials or exploit payloads.

- [ ] **Step 3: Validate all three domains**

Run: `python -X utf8 scripts/audit_explainers.py --domains backend-apis data-databases security-privacy --require-complete`

Expected: `backend-apis: 35/35`, `data-databases: 30/30`, `security-privacy: 25/25`.

- [ ] **Step 4: Run parser, renderer and security-safe escaping tests**

Run: `python -m pytest tests/test_explainers.py tests/test_explainer_renderers.py -q -k "security or escape or mapping or request"`

Expected: PASS.

- [ ] **Step 5: Commit the backend/data/security corpus**

```bash
git add content/explainers
git commit -m "content: add backend data and security visual explainers"
```

---

### Task 11: Author computing, deployment, and Git explainers (85 terms)

**Files:**
- Create/Modify: `content/explainers/*.yaml` for `computing-env`, `deployment-operations`, `git-collaboration`

**Interfaces:**
- Consumes: anatomy, sequence, pipeline, lifecycle and timeline patterns.
- Produces: exactly 35 computing, 25 deployment and 25 Git explainers.

- [ ] **Step 1: List the exact missing slugs**

Run: `python -X utf8 scripts/audit_explainers.py --domains computing-env deployment-operations git-collaboration --list-missing > try/computing-deploy-git-explainer-worklist.txt`

- [ ] **Step 2: Author environment, rollout and history scenes**

Computing scenes must distinguish operating system, process, shell, terminal, file system and working directory. Deployment scenes must show artifact, environment, rollout and rollback evidence. Git scenes must show commit/history/branch/working-tree relationships without conflating pull, fetch, merge, rebase, revert and reset.

- [ ] **Step 3: Validate all three domains**

Run: `python -X utf8 scripts/audit_explainers.py --domains computing-env deployment-operations git-collaboration --require-complete`

Expected: `computing-env: 35/35`, `deployment-operations: 25/25`, `git-collaboration: 25/25`.

- [ ] **Step 4: Run domain and timeline regression**

Run: `python -m pytest tests/test_explainers.py tests/test_explainer_renderers.py -q -k "timeline or lifecycle or complete"`

Expected: PASS.

- [ ] **Step 5: Commit the environment/deployment/Git corpus**

```bash
git add content/explainers
git commit -m "content: add environment deployment and Git explainers"
```

---

### Task 12: Author testing/debugging explainers and close 500 coverage

**Files:**
- Create/Modify: `content/explainers/*.yaml` for `testing-debugging`
- Modify: `tests/test_explainers.py`

**Interfaces:**
- Consumes: evidence, sequence, compare and timeline patterns.
- Produces: exactly 35 testing/debugging explainers and a complete 500-file corpus.

- [ ] **Step 1: List the exact missing slugs**

Run: `python -X utf8 scripts/audit_explainers.py --domains testing-debugging --list-missing > try/testing-explainer-worklist.txt`

- [ ] **Step 2: Author evidence-focused scenes**

Differentiate test case, fixture, double, unit/integration/E2E, regression, smoke, snapshot, flaky test, coverage, log, stack trace, reproduction and root cause. Each scene must name the behavior, evidence source and pass/fail or diagnosis boundary.

- [ ] **Step 3: Run the domain gate**

Run: `python -X utf8 scripts/audit_explainers.py --domains testing-debugging --require-complete`

Expected: `testing-debugging: 35/35`.

- [ ] **Step 4: Run the complete 500-file gate**

Run: `python -X utf8 scripts/audit_explainers.py --require-complete`

Run: `python -X utf8 scripts/audit_full_content.py`

Expected: 500 files, 14 registered patterns represented, exact `en`/`zh-cn` alignment, zero duplicate signatures, existing 500-term content audit PASS.

- [ ] **Step 5: Commit the final corpus batch**

```bash
git add content/explainers tests/test_explainers.py
git commit -m "content: complete 500 visual explainers"
```

---

### Task 13: Integrate explainers into the catalog and term pages

**Files:**
- Modify: `scripts/vibe_terms/content.py`
- Modify: `scripts/vibe_terms/render.py`
- Modify: `scripts/vibe_terms/__init__.py`
- Modify: `tests/test_content_schema.py`
- Modify: `tests/test_static_site.py`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Consumes: complete 500-file corpus and `render_visual_explainer()`.
- Produces: `term["visual_explainer"]`, built `assets/explainers.css`, `assets/explainers.js`, copied icons and term-page `data-section="visual-explainer"`.

- [ ] **Step 1: Write failing catalog and generated-page tests**

```python
def test_every_term_carries_one_valid_visual_explainer(catalog: Catalog) -> None:
    assert len(catalog.terms) == 500
    for term in catalog.terms:
        assert term["visual_explainer"]["term"] == term["slug"]


def test_term_page_keeps_visual_and_existing_learning_sections(generated_site: Path) -> None:
    html = (generated_site / "zh-cn" / "terms" / "css" / "index.html").read_text(encoding="utf-8")
    assert 'data-section="visual-explainer"' in html
    assert 'data-explainer-pattern="code-result"' in html
    assert 'data-explainer-locale="zh-cn"' in html
    assert 'data-section="example"' in html
    assert 'data-section="exercise"' in html
```

- [ ] **Step 2: Run and confirm integration is absent**

Run: `python -m pytest tests/test_content_schema.py::test_every_term_carries_one_valid_visual_explainer tests/test_static_site.py::test_term_page_keeps_visual_and_existing_learning_sections -q`

Expected: FAIL because catalog terms do not yet carry explainers.

- [ ] **Step 3: Attach validated explainers during catalog loading**

At the beginning of `load_catalog`, collect the canonical slug set and call `load_explainers(content_root, slugs)`. Add the matching dictionary as `visual_explainer` when each term is normalized. Extend `validate_catalog` to assert one matching explainer per term without re-reading files.

- [ ] **Step 4: Render the new section before the existing example**

Import `render_visual_explainer` in `render.py`. In `build_term_pages`, place:

```python
visual_html = render_visual_explainer(term["visual_explainer"], locale)
```

immediately after the definition summary and before `self.example_html(locale, term, localized)`. Wrap it in `data-section="visual-explainer"`; do not remove or reorder the existing exercise and reference sections.

- [ ] **Step 5: Copy and load shared browser assets**

Add `explainers.css`, `explainers.js` and `icons/` to `SiteRenderer.prepare()`. Add the CSS after `clarity.css` and the script before `app.js`. Mount all explainer roots on `DOMContentLoaded` without changing `examples.js`.

- [ ] **Step 6: Verify locale fallback in generated pages**

Add assertions that CSS renders Chinese copy for `zh-cn` and `zh-tw`, English copy for `en`, `ja`, `ko`, `de`, `ru`, while page navigation remains in its original locale.

- [ ] **Step 7: Run static, content, and packaging tests**

Run: `python -m pytest tests/test_content_schema.py tests/test_static_site.py tests/test_packaging.py -q`

Expected: PASS with 500 terms and all required assets in the archive.

- [ ] **Step 8: Commit integration**

```bash
git add scripts/vibe_terms/content.py scripts/vibe_terms/render.py scripts/vibe_terms/__init__.py tests/test_content_schema.py tests/test_static_site.py tests/test_packaging.py
git commit -m "feat: integrate visual explainers into term pages"
```

---

### Task 14: Add real-browser explainer, fallback, theme, and responsive gates

**Files:**
- Modify: `tests/test_browser.py`
- Modify: `tests/test_render_harness.py`
- Modify: `tests/js/explainers.test.cjs`
- Modify: `scripts/verify_public_site.sh`

**Interfaces:**
- Consumes: generated pages, theme runtime and visual explainer runtime.
- Produces: reproducible root/BASE_PATH HTTP behavior and desktop/mobile interaction evidence.

- [ ] **Step 1: Write the failing cross-locale browser scenario**

```python
def test_visual_explainer_locale_fallback_and_state_change(site_url: str) -> None:
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(f"{site_url}/zh-tw/terms/css/")
        root = page.locator("[data-visual-explainer]")
        assert root.get_attribute("data-explainer-locale") == "zh-cn"
        root.locator('[data-explainer-state-control="override"]').click()
        assert root.locator('[aria-pressed="true"]').get_attribute("data-explainer-state-control") == "override"
        page.goto(f"{site_url}/de/terms/css/")
        assert page.locator("[data-visual-explainer]").get_attribute("data-explainer-locale") == "en"
        browser.close()
```

- [ ] **Step 2: Run and confirm browser behavior is not wired**

Run: `RUN_HTTP_E2E=1 python -m pytest tests/test_browser.py -q -k visual_explainer`

Expected: FAIL before Task 13 assets/runtime are mounted in the HTTP build.

- [ ] **Step 3: Add desktop/mobile and theme assertions**

Parametrize representative slugs for all 14 patterns. At 1280×720 and 390×844 assert:

```python
assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
assert root.is_visible()
assert page.locator("[data-explainer-conclusion]").is_visible()
assert not page.locator("nextjs-portal, vite-error-overlay").count()
```

Switch light/dark/system, sample computed text/background contrast and assert no relevant console error or warning.

- [ ] **Step 4: Add keyboard and reduced-motion checks**

Focus the first state button, press ArrowRight and End, verify focus and `aria-pressed`. Emulate reduced motion in the local harness and assert computed transition duration is effectively zero.

- [ ] **Step 5: Verify root and `/vibe-terms` builds**

Run: `RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh`

Run: `BASE_PATH=/vibe-terms RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh`

Expected: both builds PASS; the second uses `/vibe-terms/assets/explainers.css`, `/vibe-terms/assets/explainers.js` and prefixed icons.

- [ ] **Step 6: Commit browser gates**

```bash
git add tests/test_browser.py tests/test_render_harness.py tests/js/explainers.test.cjs scripts/verify_public_site.sh
git commit -m "test: cover visual explainers across themes and locales"
```

---

### Task 15: Documentation, design QA, unified acceptance, and release

**Files:**
- Modify: `README.md`
- Modify: `docs/content-workflow.md`
- Modify: `docs/deployment.md`
- Modify: `design-qa.md`
- Modify: `doc/验收/模块/验收-静态站点.md`
- Modify: `doc/验收/跨模块/验收-查词到项目学习.md`
- Create: `doc/验收/任务/验收-500词可视化解读与暗色主题.md`
- Modify: `doc/进展记录/2026-08-16.md`
- Move after PASS: `docs/superpowers/specs/2026-08-16-visual-explainers-dark-theme-design.md` to `doc/归档/2026-08-16/`
- Move after PASS: `docs/superpowers/plans/2026-08-16-visual-explainers-dark-theme.md` to `doc/归档/2026-08-16/`
- Modify only with explicit user authorization: `AGENTS.md`

**Interfaces:**
- Consumes: the complete implementation and every automated/browser gate.
- Produces: final QA evidence, one independent formal acceptance conclusion, clean `main`, GitHub Pages deployment and live readback.

- [ ] **Step 1: Update authoring and deployment documentation**

Document the exact explainer schema, locale fallback table, domain audit commands, icon sync command, no-JavaScript contract and theme QA commands. README describes 500 visual explainers without claiming seven translated explainer sets.

- [ ] **Step 2: Run the complete local verification matrix**

Run:

```bash
python -X utf8 scripts/audit_full_content.py
python -X utf8 scripts/audit_explainers.py --require-complete
RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh
BASE_PATH=/vibe-terms RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh
npm ci
npm run build
git diff --check
```

Expected: 500 terms, 500 explainers, 14 patterns, seven page locales, three paths, root/subpath HTTP success, Sites build success and no diff whitespace errors.

- [ ] **Step 3: Run blocking browser design QA**

Use the Browser plugin on the local static site. The flow under test is: term page loads -> theme and explainer state change -> visible panel, conclusion and original learning content remain correct. Capture same-state desktop/mobile light/dark screenshots for representative patterns. Compare CSS against the provided reference for information hierarchy and state clarity. Update `design-qa.md`; fix P0/P1/P2 and repeat until it says exactly `final result: passed`.

- [ ] **Step 4: Dispatch one independent unified acceptance agent**

The acceptance agent receives requirements and commands but no implementation context. It samples all 14 patterns, both explainer copy languages, Chinese/English fallback routes, dark/light, 1280×720 and 390×844, search -> term -> explainer -> exercise -> project path, local persistence, root/BASE_PATH, package output and core pre-existing flows. It does not repeat 500 manual browser checks; it must verify the 500-file automated gate and use a reproducible random sample for content/browser quality.

- [ ] **Step 5: Resolve every blocking acceptance finding**

For each L2/L3 blocker, add a red test, apply the minimal in-scope fix, rerun the targeted gate and ask the same independent acceptance agent to recheck. Final conclusion must be `通过`; `有条件通过`、`不通过` or `阻塞` cannot merge or publish.

- [ ] **Step 6: Archive completed design/plan and record progress**

Move the two completed Superpowers documents into `doc/归档/2026-08-16/`, archive the task acceptance record after PASS, and update the progress record once with exact local time, files, tests, errors, rollback and external-state boundaries.

- [ ] **Step 7: Commit final documentation**

```bash
git add README.md docs doc design-qa.md
git commit -m "docs: record visual explainer delivery"
```

If the user has explicitly authorized `AGENTS.md`, add its current source-of-truth and test-command changes to this commit; otherwise leave it untouched and report the documentation constraint.

- [ ] **Step 8: Merge, delete the task branch, and push**

```bash
git checkout main
git merge --no-ff codex/feat-visual-explainers-dark-theme -m "merge: add 500 visual explainers and dark theme"
git branch -d codex/feat-visual-explainers-dark-theme
git push origin main
```

- [ ] **Step 9: Wait for authoritative GitHub readback**

Wait for both `Verify public site` and `Deploy GitHub Pages` runs tied to the pushed `main` SHA. Read back:

- `/vibe-terms/zh-cn/terms/css/` uses Simplified Chinese explainer copy;
- `/vibe-terms/zh-tw/terms/css/` also uses Simplified Chinese explainer copy;
- `/vibe-terms/de/terms/css/` uses English explainer copy;
- dark theme renders readable header, card, diagram, code and exercise regions;
- the CSS state control changes the computed result;
- one simple single-state term and one complex multi-state term render correctly;
- original search, knowledge map, project paths and exercises remain HTTP 200 and usable.

Expected: remote SHA equals local `main`, both workflows conclude `success`, and all live checks pass without console errors.

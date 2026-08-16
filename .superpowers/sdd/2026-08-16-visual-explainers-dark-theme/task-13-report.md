# Task 13 report: catalog, term-page, and discovery integration

## Status

Implemented as `4d9ca3b6f518bce14b87c1288436ee4d487db2be` (`feat: integrate visual explainers into term pages`), followed by `53add25885a1d6bdd8acf6af80c03d3b2d00c609` to generate every localized license alternate required by the shared hreflang head.

## RED / GREEN evidence

- **RED:** before production changes, loading the real 500-term catalog and asserting
  `len(term["visual_explainer"] for term in catalog.terms) == 14` failed with
  `AssertionError: 0`.
- **GREEN:** the same real-catalog contract passed with exactly 14 attached explainers
  and 486 terms without that optional field. The generated `css` pages place the
  visual section after `definition` and before the pre-existing `example` section;
  the original exercise, path, and source sections remain present.

## Scope and content boundary

- `load_catalog()` enumerates only present `content/explainers/*.yaml` files, rejects
  a non-canonical slug, validates every file through `load_explainer()`, and attaches
  it only to its matching term.
- Exactly 14 authored terms render `data-section="visual-explainer"`; no empty or
  generic explainer is emitted for the remaining 486 terms.
- Explainer copy uses `zh-cn` for `zh-cn` and `zh-tw`, and `en` for `en`, `ja`, `ko`,
  `de`, and `ru`; document locale and navigation remain the requested locale.

## SEO/GEO output

- Root `/` is now an answer-first bilingual English/Chinese landing page with the
  seven language entrances, global search, verified 500/12/42/3 facts, 14 visual
  entry points, knowledge-map and project-path calls to action, question-format
  sections, FAQ, and licensing/source disclosure.
- Root metadata uses `UrlBuilder` for canonical, hreflang, Open Graph, and X/Twitter
  URLs. The JSON-LD `@graph` contains `WebSite`, `DefinedTermSet`, and `FAQPage`.
- `robots.txt`, `sitemap.xml`, and `llms.txt` are generated. `llms.txt` links all 14
  representative terms, the knowledge map, project paths, and the generated license
  page.
- The discoverability text and tests identify the format basis as
  AnswerDotAI/llms-txt (Apache-2.0) and the JSON-LD vocabulary as Schema.org. No
  remote runtime or third-party marketing copy was added.

## Tests and checks

- `python -m py_compile scripts/vibe_terms/content.py scripts/vibe_terms/render.py scripts/vibe_terms/__init__.py scripts/vibe_terms/explainer_renderers/*.py` — PASS.
- Real-catalog 14/486 contract — PASS.
- `python scripts/build_static_site.py` — PASS: 7 locales, 12 domains, 42 topics,
  3 paths, 500 terms, 4244 routes.
- Default generated-artifact read-back — PASS: visual order, locale fallback, root
  metadata/JSON-LD, llms, copied CSS/JS/icons, robots, and sitemap.
- `SITE_URL=https://q2955161835-debug.github.io/vibe-terms BASE_PATH=/vibe-terms python scripts/build_static_site.py` plus read-back — PASS: root canonical/hreflang,
  explainer assets, robots sitemap and llms paths have one correct `/vibe-terms` prefix.
- `git diff --check` and staged `git diff --cached --check` — PASS.
- The requested pytest command was invoked, but the desktop command runner stopped
  the captured process at its 30-second limit before pytest produced a final summary.
  The focused real-output checks above were run instead; the controller should run
  the full `tests/test_content_schema.py tests/test_static_site.py tests/test_packaging.py -q`
  gate during the final acceptance window.

## Concerns

- The newly exported renderer exposed an existing package-context incompatibility in
  the explainer renderer imports when `scripts/build_static_site.py` imports
  `vibe_terms` directly. The integration commit changes those internal imports to
  package-relative form; static generation now passes.
- `npm run build` was started but its child `vinext build` exceeded the desktop
  command runner's 30-second capture limit and was terminated to avoid leaving a
  background process. It is not claimed as passed here.

## SHA

`4d9ca3b6f518bce14b87c1288436ee4d487db2be` (integration)

`53add25885a1d6bdd8acf6af80c03d3b2d00c609` (localized license alternates)

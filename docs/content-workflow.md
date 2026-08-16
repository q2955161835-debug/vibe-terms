# Terminology content workflow

## Canonical source

English is the canonical editorial source. Every term has:

- `content/terms/<slug>/meta.yaml` for language-independent metadata;
- `en.yaml` for the canonical editorial content;
- one file for each supported locale.

## Adding a term

1. Choose a canonical English name and stable slug.
2. Add aliases for abbreviations, historical names, and library-specific names.
3. Select one primary domain and one lifecycle stage.
4. Add the slug once to the learning path.
5. Write the English definition and teaching fields.
6. Add all seven translated locale files as `draft`.
7. Run `python3 scripts/audit_full_content.py`.
8. Run `./scripts/verify_public_site.sh`.
9. Submit the change through a GitHub pull request.

## Translation status

- `draft`: machine-assisted or unreviewed translation; generated page must remain `noindex`.
- `reviewed`: reviewed for language/technical accuracy but not necessarily approved for publication by the project maintainer.
- `published`: approved for the public index and sitemap.

A translation status is per locale and per term. One unfinished language must not block publication of another reviewed language.

## Reference-site compatibility

`content/baselines/vibe-hub.yaml` is a compatibility map, not a copy of VibeHub editorial prose.

When a source label is framework-specific, preserve it as an alias while mapping it to a more general canonical term, for example:

- `InputNumber` → `Number Input`
- `Rate` → `Rating Control`
- `Cascader` → `Cascading Select`
- `Descriptions` → `Description List`
- `Popconfirm` → `Inline Confirmation`
- `BackTop` → `Back-to-top Button`

Do not copy third-party explanatory text. Vibe Terms definitions and examples must remain original.

## Visual explainer subset

Visual explainers are an optional, hand-authored layer under
`content/explainers/<canonical-slug>.yaml`. The shipped subset contains exactly
14 representative terms and covers the registered patterns `anatomy`,
`compare`, `sequence`, `state-machine`, `request-response`, `pipeline`,
`hierarchy`, `code-result`, `data-mapping`, `lifecycle`, `boundary`, `layout`,
`timeline`, and `evidence` once each. Do not add an empty or generic explainer
to the other 486 terms.

Each file uses schema version 1 and must contain only these root fields:

- `term`: the canonical slug matching the filename;
- `pattern`: one registered visual grammar;
- `complexity`: an integer from 1 through 4, chosen for the concept rather than
  normalized across the corpus;
- `copy`: exactly `en` and `zh-cn`, with aligned headings, introductions, state
  labels/conclusions, and node labels;
- `states`: stable IDs, focus-node IDs, and scalar dynamic values;
- `scene`: unique nodes and explicit `from`/`to` relations.

Copy fallback is deliberate: `en` uses English; `zh-cn` and `zh-tw` use
Simplified Chinese; `ja`, `ko`, `de`, and `ru` use English. The renderer emits a
complete static first state and transcript, so the concept and every state
conclusion remain available without JavaScript. JavaScript only enhances state
focus and dynamic values; it must not remove the original four-stage example,
exercise, project-path, or source sections.

Validate content, rendering, runtime, and the vendored Phosphor subset with:

```bash
python3 -m pytest tests/test_explainers.py tests/test_explainer_renderers.py -q
node --test tests/js/explainers.test.cjs
python3 scripts/sync_phosphor_icons.py --check
```

The 15 regular SVG icons are byte-for-byte synchronized from the pinned
`@phosphor-icons/core` dependency; `web/icons/LICENSE.phosphor.txt` preserves
its MIT license. Run the sync command without `--check` only after installing
the locked npm dependencies and intentionally changing the allowlist.

## Discovery artifacts

The generated root page is an answer-first bilingual index of the complete
500-term platform and the 14 visual explainers. It emits canonical and
`hreflang` links, Open Graph/X metadata, a site-wide social image, Schema.org
`WebSite`/`DefinedTermSet`/`FAQPage` JSON-LD, `robots.txt`, `sitemap.xml`, and an
AnswerDotAI-style `llms.txt`. These are static discovery aids, not claims of
search-engine placement. Keep all generated URLs behind `UrlBuilder` so root
hosting and `BASE_PATH=/vibe-terms` remain equivalent.

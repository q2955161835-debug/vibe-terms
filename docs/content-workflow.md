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

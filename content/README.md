# Content authoring

English files are the canonical meaning source. Every term directory contains
`meta.yaml` and one YAML file for each supported locale.

The current corpus contract is 500 canonical terms, 12 first-level domains,
42 second-level topics, and the fixed eight locales. `taxonomy/topics.yaml`
assigns every term to exactly one topic. `paths/` contains three chaptered
project courses; `paths/zero-to-vibe.yaml` remains the canonical 500-term
learning order, while `zero-to-vibe.prototype.yaml` is retained only as
historical compatibility evidence.

When the English meaning changes:

1. increment `content_version` in `meta.yaml`;
2. update the English file;
3. update each translation's `source_content_version` after review;
4. leave unreviewed translations marked `draft`.

Draft localizations are valid source material, but the generator must label
them and emit `noindex`. A complete file set does not imply human review.

General concepts use canonical cross-framework names. Framework-specific labels
belong in `aliases` unless the framework itself is the subject.

Original content in this directory is licensed under CC BY-SA 4.0. See
`../LICENSE-CONTENT`.

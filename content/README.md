# Content authoring

English files are the canonical meaning source. Every term directory contains
`meta.yaml` and one YAML file for each supported locale.

When the English meaning changes:

1. increment `content_version` in `meta.yaml`;
2. update the English file;
3. update each translation's `source_content_version` after review;
4. leave unreviewed translations marked `draft`.

General concepts use canonical cross-framework names. Framework-specific labels
belong in `aliases` unless the framework itself is the subject.

Original content in this directory is licensed under CC BY-SA 4.0. See
`../LICENSE-CONTENT`.

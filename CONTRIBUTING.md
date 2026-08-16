# Contributing to Vibe Terms

Thank you for helping make Vibe Coding terminology understandable to beginners.
All code and content contributions use GitHub issues and pull requests.

## Before opening a pull request

1. Create or update an issue when the change affects taxonomy, content schema, or user-facing behavior.
2. Keep English as the canonical source for technical meaning.
3. Preserve the seven supported locale files for every term: `en`, `zh-cn`, `zh-tw`, `ja`, `ko`, `de`, and `ru`.
4. Do not publish machine-generated translations without human review.
5. Keep examples beginner-friendly and avoid tying a general term to one framework unless the framework is the subject.

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m playwright install chromium
```

## Build and verify

```bash
./scripts/verify_public_site.sh
```

The generated site is written to `site/` and is not committed.

## Content layout

Each term lives in `content/terms/<slug>/` with one `meta.yaml` file and one localized YAML file per supported locale. Update the learning path when adding a prototype term, and keep `source_content_version` aligned with the metadata version.

## Licensing

By contributing code, you agree that it may be distributed under Apache-2.0. By contributing terminology, translations, taxonomy, examples, or learning content, you agree that it may be distributed under CC BY-SA 4.0.

#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
TERMS = CONTENT / "terms"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")
EXPECTED_TERMS = 500
REQUIRED_FIELDS = (
    "title",
    "short_definition",
    "analogy",
    "why_it_matters",
    "ai_prompt_example",
    "common_mistake",
    "status",
    "source_content_version",
)
ALLOWED_STATUS = {"draft", "reviewed", "published"}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def main() -> int:
    errors: list[str] = []
    term_dirs = sorted(path for path in TERMS.iterdir() if path.is_dir())
    if len(term_dirs) != EXPECTED_TERMS:
        errors.append(f"expected {EXPECTED_TERMS} canonical term directories, found {len(term_dirs)}")

    domains = load(CONTENT / "taxonomy" / "domains.yaml")["domains"]
    stages = load(CONTENT / "taxonomy" / "lifecycle.yaml")["stages"]
    domain_ids = {item["id"] for item in domains}
    stage_ids = {item["id"] for item in stages}

    metas = []
    for directory in term_dirs:
        meta_path = directory / "meta.yaml"
        if not meta_path.is_file():
            errors.append(f"{directory.name}: missing meta.yaml")
            continue
        meta = load(meta_path)
        metas.append(meta)
        if meta.get("slug") != directory.name:
            errors.append(f"{directory.name}: directory/slug mismatch")
        if meta.get("primary_domain") not in domain_ids:
            errors.append(f"{directory.name}: unknown domain {meta.get('primary_domain')!r}")
        if meta.get("lifecycle_stage") not in stage_ids:
            errors.append(f"{directory.name}: unknown lifecycle stage {meta.get('lifecycle_stage')!r}")
        if not isinstance(meta.get("content_version"), int) or meta["content_version"] < 1:
            errors.append(f"{directory.name}: invalid content_version")
        for locale in LOCALES:
            path = directory / f"{locale}.yaml"
            if not path.is_file():
                errors.append(f"{directory.name}: missing {locale}.yaml")
                continue
            localized = load(path)
            missing = [field for field in REQUIRED_FIELDS if not localized.get(field) and localized.get(field) != 0]
            if missing:
                errors.append(f"{directory.name}/{locale}: missing fields {missing}")
            if localized.get("status") not in ALLOWED_STATUS:
                errors.append(f"{directory.name}/{locale}: invalid status {localized.get('status')!r}")
            if localized.get("source_content_version") != meta.get("content_version"):
                errors.append(f"{directory.name}/{locale}: stale source_content_version")

    slugs = [meta.get("slug") for meta in metas]
    names = [meta.get("canonical_name") for meta in metas]
    if len(slugs) != len(set(slugs)):
        errors.append(f"duplicate slugs: {[k for k,v in Counter(slugs).items() if v > 1]}")
    if len(names) != len(set(names)):
        errors.append(f"duplicate canonical names: {[k for k,v in Counter(names).items() if v > 1]}")

    canonical_names = set(names)
    for meta in metas:
        for related in meta.get("related_terms", []):
            if related not in canonical_names:
                errors.append(f"{meta.get('slug')}: unknown related term {related!r}")

    path_file = CONTENT / "paths" / "zero-to-vibe.yaml"
    learning = load(path_file)
    ordered = learning["terms"]
    if len(ordered) != EXPECTED_TERMS or len(set(ordered)) != EXPECTED_TERMS:
        errors.append("zero-to-vibe.yaml must contain 500 unique slugs")
    if set(ordered) != set(slugs):
        errors.append("learning path and canonical term set differ")

    baseline_path = CONTENT / "baselines" / "vibe-hub.yaml"
    if not baseline_path.is_file():
        errors.append("missing content/baselines/vibe-hub.yaml")
    else:
        baseline = load(baseline_path)
        source_terms = set()
        slug_set = set(slugs)
        for mapping in baseline.get("mappings", []):
            source = mapping.get("source_term")
            target = mapping.get("slug")
            if source in source_terms:
                errors.append(f"duplicate VibeHub source mapping: {source!r}")
            source_terms.add(source)
            if target not in slug_set:
                errors.append(f"VibeHub mapping target does not exist: {source!r} -> {target!r}")
        if len(source_terms) < 250:
            errors.append(f"expected at least 250 captured VibeHub mappings, found {len(source_terms)}")

    for error in errors:
        fail(error)
    if errors:
        print(f"Content audit failed with {len(errors)} problem(s).", file=sys.stderr)
        return 1

    print(
        f"Content audit passed: {len(term_dirs)} canonical terms, "
        f"{len(term_dirs) * len(LOCALES)} locale files, "
        f"{len(domains)} domains, {len(learning['terms'])} learning-path entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

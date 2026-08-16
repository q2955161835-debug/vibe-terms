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
TRANSLATED_LOCALES = LOCALES[1:]
PLACEHOLDER_MARKERS = {
    "zh-cn": ("当前为待人工审校的草稿", "英文标准定义"),
    "zh-tw": ("目前為待人工審校的草稿", "英文標準定義"),
    "ja": ("現在の日本語本文はレビュー前の草稿", "英語の基準定義"),
    "ko": ("현재 한국어 본문은 검토 전 초안", "영어 기준 정의"),
    "de": ("noch nicht redigierter Entwurf", "Englische Referenzdefinition"),
    "ru": ("черновиком до редакторской проверки", "Эталонное определение на английском"),
    "hi": ("मानव समीक्षा से पहले का मसौदा", "अंग्रेज़ी मानक परिभाषा"),
}


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
    translation_placeholders: Counter[str] = Counter()

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
            if locale in TRANSLATED_LOCALES:
                visible = "\n".join(
                    str(localized.get(field, ""))
                    for field in (
                        "title",
                        "short_definition",
                        "analogy",
                        "mechanism",
                        "why_it_matters",
                        "project_example",
                        "ai_prompt_example",
                        "common_mistake",
                    )
                )
                repeated = (
                    bool(localized.get("mechanism"))
                    and str(localized["short_definition"]).strip()
                    == str(localized["mechanism"]).strip()
                ) or (
                    bool(localized.get("project_example"))
                    and str(localized["why_it_matters"]).strip()
                    == str(localized["project_example"]).strip()
                )
                if repeated or any(
                    marker in visible for marker in PLACEHOLDER_MARKERS[locale]
                ):
                    translation_placeholders[locale] += 1

    for locale, count in sorted(translation_placeholders.items()):
        errors.append(f"{locale}: {count} generated translation placeholder(s)")

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

    untranslated_paths: list[str] = []
    for project_path in sorted(
        path for path in (CONTENT / "paths").iterdir() if path.is_dir()
    ):
        for locale in TRANSLATED_LOCALES:
            localized_path = project_path / f"{locale}.yaml"
            if not localized_path.is_file():
                continue
            localized_text = localized_path.read_text(encoding="utf-8")
            if "Draft —" in localized_text or "not human reviewed" in localized_text:
                untranslated_paths.append(f"{project_path.name}/{locale}")
    if untranslated_paths:
        errors.append(
            "untranslated project path placeholder(s): "
            + ", ".join(untranslated_paths)
        )

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

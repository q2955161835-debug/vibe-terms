#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
GLOSSARY = CONTENT / "glossaries" / "terminology.yaml"
LOCALES = ("zh-cn", "zh-tw", "ja", "ko", "de", "ru")


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a YAML mapping: {path}")
    return value


def synchronized_glossary() -> dict:
    glossary = load(GLOSSARY)
    entries = glossary.get("terms")
    if not isinstance(entries, list):
        raise ValueError("terminology.yaml must contain a terms list")

    term_dirs = {
        path.name: path
        for path in (CONTENT / "terms").iterdir()
        if path.is_dir() and (path / "meta.yaml").is_file()
    }
    glossary_slugs = {str(entry.get("slug")) for entry in entries}
    if glossary_slugs != set(term_dirs):
        raise ValueError("glossary and canonical term slugs differ")

    for entry in entries:
        slug = str(entry["slug"])
        directory = term_dirs[slug]
        entry["canonical"] = str(load(directory / "meta.yaml")["canonical_name"])
        statuses: dict[str, str] = {}
        for locale in LOCALES:
            localized = load(directory / f"{locale}.yaml")
            entry[locale] = str(localized["title"])
            statuses[locale] = str(localized["status"])
        entry["status"] = statuses
    return glossary


def render(value: dict) -> str:
    return yaml.safe_dump(
        value,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keep the editorial glossary aligned with locale term titles."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite content/glossaries/terminology.yaml",
    )
    args = parser.parse_args()

    expected = render(synchronized_glossary())
    current = GLOSSARY.read_text(encoding="utf-8")
    if current == expected:
        print("Glossary titles and statuses are synchronized.")
        return 0
    if not args.write:
        print("Glossary is stale; run scripts/sync_glossary_titles.py --write.")
        return 1
    GLOSSARY.write_text(expected, encoding="utf-8")
    print("Updated content/glossaries/terminology.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

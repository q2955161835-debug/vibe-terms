#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.vibe_terms.content import load_catalog
from scripts.vibe_terms.explainers import load_explainer


CONTENT = ROOT / "content"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", nargs="*", default=[])
    parser.add_argument("--list-missing", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args()


def _selected_terms(domains: list[str]) -> tuple[dict[str, str], list[str]]:
    catalog = load_catalog(CONTENT, minimum_terms=500)
    all_domains = {str(domain["id"]) for domain in catalog.domains}
    requested = domains or sorted(all_domains)
    unknown = sorted(set(requested) - all_domains)
    if unknown:
        raise ValueError(f"unknown domains: {', '.join(unknown)}")
    selected = {
        str(term["slug"]): str(term["primary_domain"])
        for term in catalog.terms
        if term["primary_domain"] in requested
    }
    return selected, requested


def _print_counts(
    requested: list[str],
    selected: dict[str, str],
    loaded: dict[str, dict[str, object]],
) -> None:
    domain_counts = Counter(selected.values())
    present_domains = Counter(selected[slug] for slug in loaded)
    print("domains:", file=sys.stderr)
    for domain in requested:
        print(f"{domain}: {present_domains[domain]}/{domain_counts[domain]}", file=sys.stderr)

    patterns = Counter(str(item["pattern"]) for item in loaded.values())
    print(
        "patterns: "
        + (", ".join(f"{key}={patterns[key]}" for key in sorted(patterns)) if patterns else "none"),
        file=sys.stderr,
    )
    complexities = Counter(int(item["complexity"]) for item in loaded.values())
    print(
        "complexities: "
        + (
            ", ".join(f"{key}={complexities[key]}" for key in sorted(complexities))
            if complexities
            else "none"
        ),
        file=sys.stderr,
    )


def main() -> int:
    args = parse_args()
    try:
        selected, requested = _selected_terms(args.domains)
        explainer_root = CONTENT / "explainers"
        discovered = (
            {path.stem: path for path in explainer_root.glob("*.yaml")}
            if explainer_root.is_dir()
            else {}
        )
        missing = sorted(set(selected) - set(discovered))
        all_slugs, _ = _selected_terms([])
        extras = sorted(set(discovered) - set(all_slugs))
        loaded = {
            slug: load_explainer(discovered[slug], slug)
            for slug in sorted(set(selected) & set(discovered))
        }
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.list_missing:
        print("\n".join(missing))
    _print_counts(requested, selected, loaded)
    if extras:
        print(f"extra explainer files: {', '.join(extras)}", file=sys.stderr)
    if args.require_complete and (missing or extras):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

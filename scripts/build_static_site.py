from __future__ import annotations

import os
from pathlib import Path

from vibe_terms import BuildConfig, build_site, load_catalog


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    minimum_terms = int(os.environ.get("MINIMUM_TERMS", "500"))
    config = BuildConfig(
        content_root=ROOT / "content",
        output_root=ROOT / "site",
        site_url=os.environ.get("SITE_URL", "").strip(),
        base_path=os.environ.get("BASE_PATH", "").strip(),
        minimum_terms=minimum_terms,
    )
    catalog = load_catalog(config.content_root, config.minimum_terms)
    routes = build_site(config, catalog)
    print(
        f"built {len(catalog.locales)} locales, {len(catalog.domains)} domains, "
        f"{len(catalog.topics)} topics, {len(catalog.paths)} paths, "
        f"{len(catalog.terms)} terms, and {len(routes)} routes"
    )


if __name__ == "__main__":
    main()

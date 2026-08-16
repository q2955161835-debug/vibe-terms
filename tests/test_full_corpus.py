from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_full_corpus_contract():
    terms = sorted(path for path in (CONTENT / "terms").iterdir() if path.is_dir())
    assert len(terms) == 500

    metas = [load(path / "meta.yaml") for path in terms]
    slugs = [meta["slug"] for meta in metas]
    canonical = [meta["canonical_name"] for meta in metas]
    assert len(set(slugs)) == 500
    assert len(set(canonical)) == 500

    for directory, meta in zip(terms, metas):
        assert directory.name == meta["slug"]
        for locale in LOCALES:
            localized = load(directory / f"{locale}.yaml")
            assert localized["source_content_version"] == meta["content_version"]
            assert localized["status"] in {"draft", "reviewed", "published"}

    path = load(CONTENT / "paths" / "zero-to-vibe.yaml")["terms"]
    assert len(path) == 500
    assert len(set(path)) == 500
    assert set(path) == set(slugs)


def test_vibehub_baseline_resolves_to_canonical_terms():
    slugs = {
        load(path / "meta.yaml")["slug"]
        for path in (CONTENT / "terms").iterdir()
        if path.is_dir()
    }
    baseline = load(CONTENT / "baselines" / "vibe-hub.yaml")
    mappings = baseline["mappings"]
    assert len(mappings) >= 250
    assert len({item["source_term"] for item in mappings}) == len(mappings)
    assert all(item["slug"] in slugs for item in mappings)

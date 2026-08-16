from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru", "hi")


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def term_domains() -> dict[str, str]:
    return {
        meta["slug"]: meta["primary_domain"]
        for directory in (CONTENT / "terms").iterdir()
        if directory.is_dir()
        for meta in [load(directory / "meta.yaml")]
    }


def test_topics_cover_each_canonical_term_once_in_its_primary_domain() -> None:
    topics = load(CONTENT / "taxonomy" / "topics.yaml")["topics"]
    canonical_domains = term_domains()
    assigned = [slug for topic in topics for slug in topic["terms"]]

    assert len(canonical_domains) == 500
    assert set(assigned) == set(canonical_domains)
    duplicates = [slug for slug, count in Counter(assigned).items() if count > 1]
    assert duplicates == []
    assert all(
        canonical_domains[slug] == topic["domain"]
        for topic in topics
        for slug in topic["terms"]
    )


def test_topics_reference_real_domains_and_have_three_per_domain() -> None:
    topics = load(CONTENT / "taxonomy" / "topics.yaml")["topics"]
    domains = load(CONTENT / "taxonomy" / "domains.yaml")["domains"]
    domain_ids = {domain["id"] for domain in domains}

    assert len({topic["id"] for topic in topics}) == len(topics)
    assert {topic["domain"] for topic in topics} == domain_ids
    counts = Counter(topic["domain"] for topic in topics)
    assert all(counts[domain_id] >= 3 for domain_id in domain_ids)


def test_topics_have_complete_localized_names_and_descriptions() -> None:
    topics = load(CONTENT / "taxonomy" / "topics.yaml")["topics"]

    for topic in topics:
        assert set(topic) == {"id", "domain", "names", "descriptions", "terms"}
        assert set(topic["names"]) == set(LOCALES)
        assert set(topic["descriptions"]) == set(LOCALES)
        assert all(
            isinstance(topic["names"][locale], str)
            and topic["names"][locale].strip()
            and isinstance(topic["descriptions"][locale], str)
            and topic["descriptions"][locale].strip()
            for locale in LOCALES
        )
        assert isinstance(topic["terms"], list) and topic["terms"]
        assert len(topic["terms"]) == len(set(topic["terms"]))

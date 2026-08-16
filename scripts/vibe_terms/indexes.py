from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from .models import Catalog
from .urls import UrlBuilder


def _domain_name(catalog: Catalog, domain_id: str, locale: str) -> str:
    return next(
        str(domain.get(locale) or domain.get("en") or domain_id)
        for domain in catalog.domains
        if domain["id"] == domain_id
    )


def _path_memberships(catalog: Catalog) -> dict[str, list[dict[str, str]]]:
    memberships: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in catalog.paths:
        for chapter in path.get("chapters", []):
            for slug in chapter.get("term_slugs", []):
                memberships[slug].append(
                    {"path": path["slug"], "chapter": chapter["id"]}
                )
    return memberships


def build_terms_index(
    catalog: Catalog, locale: str, urls: UrlBuilder
) -> list[dict[str, Any]]:
    memberships = _path_memberships(catalog)
    terms: list[dict[str, Any]] = []
    for learning_order, term in enumerate(catalog.terms, start=1):
        localized = term["localized"][locale]
        terms.append(
            {
                "slug": term["slug"],
                "canonical_name": term["canonical_name"],
                "aliases": list(term.get("aliases", [])),
                "primary_domain": term["primary_domain"],
                "domain_title": _domain_name(
                    catalog, term["primary_domain"], locale
                ),
                "topics": list(term.get("topics", [])),
                "lifecycle_stage": term["lifecycle_stages"][0],
                "lifecycle_stages": list(term["lifecycle_stages"]),
                "difficulty": term["difficulty"],
                "learning_order": learning_order,
                "title": localized["title"],
                "short_definition": localized["short_definition"],
                "analogy": localized["analogy"],
                "mechanism": localized["mechanism"],
                "why_it_matters": localized["why_it_matters"],
                "project_example": localized["project_example"],
                "user_says": localized["user_says"],
                "ai_prompt_example": localized["ai_prompt_example"],
                "common_mistake": localized["common_mistake"],
                "boundary": localized["boundary"],
                "status": localized["status"],
                "example": deepcopy(term["example"]),
                "paths": memberships.get(term["slug"], []),
                "url": urls.page(f"/{locale}/terms/{term['slug']}/"),
            }
        )
    return terms


def build_exercises_index(
    catalog: Catalog, locale: str, urls: UrlBuilder
) -> list[dict[str, Any]]:
    memberships = _path_memberships(catalog)
    exercises: list[dict[str, Any]] = []
    for term in catalog.terms:
        localized = term["localized"][locale]
        exercise = deepcopy(localized["exercise"])
        exercise.update(
            {
                "id": f"{term['slug']}:{locale}:1",
                "slug": term["slug"],
                "title": localized["title"],
                "question": exercise["prompt"],
                "domain": term["primary_domain"],
                "topics": list(term["topics"]),
                "paths": [item["path"] for item in memberships.get(term["slug"], [])],
                "url": urls.page(f"/{locale}/terms/{term['slug']}/#exercise"),
                "status": localized["status"],
            }
        )
        exercises.append(exercise)
    return exercises


def build_search_index(
    catalog: Catalog, locale: str, urls: UrlBuilder
) -> list[dict[str, Any]]:
    memberships = _path_memberships(catalog)
    documents: list[dict[str, Any]] = []
    for term in catalog.terms:
        localized = term["localized"][locale]
        documents.append(
            {
                "type": "term",
                "id": term["slug"],
                "slug": term["slug"],
                "title": localized["title"],
                "canonical_name": term["canonical_name"],
                "aliases": list(term.get("aliases", [])),
                "summary": localized["short_definition"],
                "user_says": localized["user_says"],
                "domain": term["primary_domain"],
                "domain_title": _domain_name(catalog, term["primary_domain"], locale),
                "topics": list(term["topics"]),
                "paths": memberships.get(term["slug"], []),
                "difficulty": term["difficulty"],
                "status": localized["status"],
                "url": urls.page(f"/{locale}/terms/{term['slug']}/"),
                "badge": _domain_name(catalog, term["primary_domain"], locale),
            }
        )
    for topic in catalog.topics:
        documents.append(
            {
                "type": "topic",
                "id": topic["id"],
                "slug": topic["id"],
                "title": topic["names"][locale],
                "canonical_name": topic["names"]["en"],
                "aliases": [],
                "summary": topic["descriptions"][locale],
                "domain": topic["domain"],
                "term_count": len(topic["terms"]),
                "status": "published",
                "url": urls.page(
                    f"/{locale}/knowledge/{topic['domain']}/{topic['id']}/"
                ),
                "badge": _domain_name(catalog, topic["domain"], locale),
            }
        )
    for path in catalog.paths:
        localized = path["localized"][locale]
        documents.append(
            {
                "type": "path",
                "id": path["slug"],
                "slug": path["slug"],
                "title": localized["title"],
                "canonical_name": path["localized"]["en"]["title"],
                "aliases": [],
                "summary": localized["summary"],
                "chapters": [chapter["title"] for chapter in localized["chapters"]],
                "status": localized["status"],
                "url": urls.page(f"/{locale}/paths/{path['slug']}/"),
                "badge": "Project path",
            }
        )
    return documents


def build_knowledge_graph(
    catalog: Catalog, locale: str, urls: UrlBuilder
) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "slug": term["slug"],
                "title": term["localized"][locale]["title"],
                "domain": term["primary_domain"],
                "topics": list(term["topics"]),
                "url": urls.page(f"/{locale}/terms/{term['slug']}/"),
            }
            for term in catalog.terms
        ],
        "edges": [
            {"source": prerequisite, "target": term["slug"], "type": "prerequisite"}
            for term in catalog.terms
            for prerequisite in term.get("prerequisites", [])
        ]
        + [
            {"source": term["slug"], "target": related, "type": "related"}
            for term in catalog.terms
            for related in term.get("related_terms", [])
        ],
    }

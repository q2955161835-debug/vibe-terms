from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .config import LOCALES
from .explainers import load_explainer
from .models import Catalog


CORE_EXAMPLE_MODES = {
    "prompt": ("interactive", "prompt-constraint-builder"),
    "context-window": ("stepper", "context-window-budget"),
    "ai-agent": ("stepper", "agent-tool-loop"),
    "tool-calling": ("interactive", "tool-calling-boundary"),
    "retrieval-augmented-generation": ("stepper", "retrieval-pipeline"),
    "hallucination": ("compare", "hallucination-evidence"),
    "html": ("compare", "html-structure"),
    "css": ("interactive", "css-cascade"),
    "dom": ("stepper", "dom-update"),
    "component": ("interactive", "component-reuse"),
    "state": ("interactive", "form-save-state"),
    "responsive-design": ("interactive", "responsive-breakpoints"),
    "accessibility": ("compare", "accessible-control"),
    "api": ("stepper", "api-request-response"),
    "request": ("stepper", "request-lifecycle"),
    "http-status-code": ("compare", "http-status-outcomes"),
    "database": ("stepper", "database-write-read"),
    "authentication": ("compare", "authentication-authorization"),
    "git": ("stepper", "git-working-tree"),
    "testing": ("compare", "testing-evidence"),
}

BOUNDARY_TEMPLATES = {
    "en": "Boundary: {definition} Check the concrete project context and the common mistake before treating the label as proof.",
    "zh-cn": "边界：{definition} 使用这个术语前，请结合具体项目上下文，并核对下方的常见误区。",
    "zh-tw": "邊界：{definition} 使用這個術語前，請結合具體專案脈絡，並核對下方的常見誤區。",
    "ja": "境界：{definition} この用語を根拠として扱う前に、具体的なプロジェクトの文脈と下記のよくある誤解を確認してください。",
    "ko": "경계: {definition} 이 용어를 근거로 사용하기 전에 구체적인 프로젝트 맥락과 아래의 흔한 오해를 확인하세요.",
    "de": "Abgrenzung: {definition} Prüfe den konkreten Projektkontext und den häufigen Irrtum unten, bevor du die Bezeichnung als Beleg verwendest.",
    "ru": "Граница: {definition} Прежде чем считать термин доказательством, проверьте контекст проекта и типичную ошибку ниже.",
}

EXERCISE_PROMPTS = {
    "en": "{title}: choose the description that matches this term.",
    "zh-cn": "{title}：选择最符合这个术语的描述。",
    "zh-tw": "{title}：選擇最符合這個術語的描述。",
    "ja": "{title}：この用語に最も合う説明を選んでください。",
    "ko": "{title}: 이 용어와 가장 잘 맞는 설명을 선택하세요.",
    "de": "{title}: Wähle die Beschreibung, die am besten zu diesem Begriff passt.",
    "ru": "{title}: Выберите описание, которое лучше всего соответствует этому термину.",
}


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"missing content file: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"content file must contain a mapping: {path}")
    return value


def _unique(records: list[dict[str, Any]], field: str, label: str) -> None:
    values = [record.get(field) for record in records]
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if None in values or "" in values:
        raise ValueError(f"{label} requires a non-empty {field}")
    if duplicates:
        raise ValueError(f"duplicate {label} {field}: {duplicates}")


def _normalize_sources(slug: str, sources: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if isinstance(sources, list):
        for index, source in enumerate(sources, start=1):
            if isinstance(source, str) and source.strip():
                normalized.append({"title": f"Source {index}", "url": source.strip()})
            elif isinstance(source, dict) and source.get("url"):
                normalized.append(
                    {
                        "title": str(source.get("title") or f"Source {index}"),
                        "url": str(source["url"]),
                    }
                )
    return normalized


def _normalize_exercise(
    localized: dict[str, Any], locale: str, canonical_name: str
) -> dict[str, Any]:
    existing = localized.get("exercise")
    if isinstance(existing, dict) and existing.get("options"):
        exercise = deepcopy(existing)
        options: list[dict[str, str]] = []
        for index, option in enumerate(exercise["options"], start=1):
            if isinstance(option, dict):
                option_id = str(option.get("id") or f"option-{index}")
                label = str(option.get("label") or option.get("text") or option_id)
            else:
                option_id = f"option-{index}"
                label = str(option)
            options.append({"id": option_id, "label": label})
        answer = exercise.get("answer")
        if isinstance(answer, int) and 0 <= answer < len(options):
            answer = options[answer]["id"]
        exercise.update(
            {
                "type": str(exercise.get("type") or "single-choice"),
                "prompt": str(exercise.get("prompt") or exercise.get("question") or ""),
                "options": options,
                "answer": str(answer),
                "explanations": exercise.get("explanations") or {},
                "content_status": str(
                    exercise.get("content_status") or "authored"
                ),
            }
        )
        return exercise

    quiz = localized.get("quiz")
    if isinstance(quiz, list) and quiz and isinstance(quiz[0], dict):
        question = quiz[0]
        raw_options = question.get("options") or []
        options = [
            {"id": f"option-{index + 1}", "label": str(option)}
            for index, option in enumerate(raw_options)
        ]
        answer_index = question.get("answer", 0)
        if not isinstance(answer_index, int) or not 0 <= answer_index < len(options):
            answer_index = 0
        answer = options[answer_index]["id"] if options else "option-1"
        explanations = {
            option["id"]: (
                "This matches the canonical definition."
                if option["id"] == answer
                else "Compare this choice with the definition and boundary above."
            )
            for option in options
        }
        return {
            "type": "single-choice",
            "prompt": str(question.get("question") or f"What best describes {canonical_name}?"),
            "options": options,
            "answer": answer,
            "explanations": explanations,
            "content_status": "normalized-from-authored-quiz",
        }

    definition = str(localized["short_definition"])
    mistake = str(localized.get("common_mistake") or canonical_name)
    analogy = str(localized.get("analogy") or canonical_name)
    return {
        "type": "single-choice",
        "prompt": EXERCISE_PROMPTS[locale].format(title=localized["title"]),
        "options": [
            {"id": "definition", "label": definition},
            {"id": "mistake", "label": mistake},
            {"id": "analogy", "label": analogy},
        ],
        "answer": "definition",
        "explanations": {
            "definition": definition,
            "mistake": mistake,
            "analogy": analogy,
        },
        "content_status": (
            "generated-from-local-draft" if locale != "en" else "normalized-fallback"
        ),
    }


def _normalize_localized(
    slug: str,
    canonical_name: str,
    locale: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    localized = deepcopy(raw)
    required = (
        "title",
        "short_definition",
        "analogy",
        "why_it_matters",
        "ai_prompt_example",
        "common_mistake",
        "status",
        "source_content_version",
    )
    missing = [field for field in required if not localized.get(field)]
    if missing:
        raise ValueError(f"{slug}/{locale} is missing localized fields: {missing}")
    localized.setdefault("mechanism", localized["short_definition"])
    localized.setdefault("project_example", localized["analogy"])
    localized.setdefault("user_says", localized["project_example"])
    localized.setdefault(
        "boundary",
        BOUNDARY_TEMPLATES[locale].format(
            definition=localized["short_definition"]
        ),
    )
    localized["sources"] = _normalize_sources(slug, localized.get("sources"))
    localized["exercise"] = _normalize_exercise(localized, locale, canonical_name)
    return localized


def _normalize_paths(content_root: Path) -> list[dict[str, Any]]:
    paths_root = content_root / "paths"
    if not paths_root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for directory in sorted(item for item in paths_root.iterdir() if item.is_dir()):
        meta = _read_yaml(directory / "meta.yaml")
        localized = {
            locale: _read_yaml(directory / f"{locale}.yaml") for locale in LOCALES
        }
        chapters: list[dict[str, Any]] = []
        for chapter in meta.get("chapters", []):
            chapter_copy = deepcopy(chapter)
            chapter_copy.setdefault("slug", chapter_copy.get("id"))
            chapter_copy.setdefault("term_slugs", [])
            chapters.append(chapter_copy)
        path = {**deepcopy(meta), "chapters": chapters, "localized": localized}
        result.append(path)
    return result


def load_catalog(content_root: Path, minimum_terms: int) -> Catalog:
    content_root = Path(content_root).resolve()
    domains = list(_read_yaml(content_root / "taxonomy" / "domains.yaml").get("domains", []))
    stages = list(_read_yaml(content_root / "taxonomy" / "lifecycle.yaml").get("stages", []))
    term_dirs = sorted(
        directory
        for directory in (content_root / "terms").iterdir()
        if directory.is_dir() and (directory / "meta.yaml").is_file()
    )
    if len(term_dirs) < minimum_terms:
        raise ValueError(
            f"catalog requires at least {minimum_terms} terms, found {len(term_dirs)}"
        )

    raw_metas = [_read_yaml(directory / "meta.yaml") for directory in term_dirs]
    canonical_to_slug = {
        str(meta["canonical_name"]): str(meta["slug"]) for meta in raw_metas
    }
    slug_set = {str(meta["slug"]) for meta in raw_metas}
    explainer_root = content_root / "explainers"
    explainer_paths = sorted(explainer_root.glob("*.yaml")) if explainer_root.is_dir() else []
    visual_explainers: dict[str, dict[str, Any]] = {}
    for explainer_path in explainer_paths:
        explainer_slug = explainer_path.stem
        if explainer_slug not in slug_set:
            raise ValueError(f"explainer has no canonical term: {explainer_slug}")
        visual_explainers[explainer_slug] = load_explainer(
            explainer_path, explainer_slug
        )

    topics_path = content_root / "taxonomy" / "topics.yaml"
    if topics_path.is_file():
        topics = list(_read_yaml(topics_path).get("topics", []))
    else:
        topics = [
            {
                "id": f"{domain['id']}-overview",
                "domain": domain["id"],
                "names": {locale: domain[locale] for locale in LOCALES},
                "descriptions": {locale: domain[locale] for locale in LOCALES},
                "terms": [
                    str(meta["slug"])
                    for meta in raw_metas
                    if meta["primary_domain"] == domain["id"]
                ],
            }
            for domain in domains
        ]
    topics_by_term: dict[str, list[str]] = {slug: [] for slug in slug_set}
    for topic in topics:
        for slug in topic.get("terms", []):
            if slug in topics_by_term:
                topics_by_term[slug].append(str(topic["id"]))

    terms: list[dict[str, Any]] = []
    for directory, meta in zip(term_dirs, raw_metas):
        slug = str(meta["slug"])
        if directory.name != slug:
            raise ValueError(f"term directory and slug differ for {slug}")
        localized = {
            locale: _normalize_localized(
                slug,
                str(meta["canonical_name"]),
                locale,
                _read_yaml(directory / f"{locale}.yaml"),
            )
            for locale in LOCALES
        }
        if not localized["en"]["sources"]:
            localized["en"]["sources"] = [
                {
                    "title": "Canonical English Vibe Terms entry",
                    "url": f"/en/terms/{slug}/",
                    "kind": "internal-provenance",
                }
            ]
        for locale in LOCALES[1:]:
            if not localized[locale]["sources"]:
                localized[locale]["sources"] = deepcopy(localized["en"]["sources"])
        related = [
            value
            for item in meta.get("related_terms", [])
            for value in [canonical_to_slug.get(str(item), str(item))]
        ]
        mode, example_id = CORE_EXAMPLE_MODES.get(
            slug, ("static", f"{slug}-static")
        )
        term = {
            **deepcopy(meta),
            "lifecycle_stages": list(
                meta.get("lifecycle_stages") or [meta.get("lifecycle_stage")]
            ),
            "topics": topics_by_term.get(slug, []),
            "prerequisites": list(meta.get("prerequisites") or []),
            "related_terms": related,
            "example": {"mode": mode, "id": example_id},
            "localized": localized,
        }
        if slug in visual_explainers:
            term["visual_explainer"] = visual_explainers[slug]
        terms.append(term)

    catalog = Catalog(
        tuple(LOCALES),
        tuple(domains),
        tuple(topics),
        tuple(terms),
        tuple(_normalize_paths(content_root)),
    )
    validate_catalog(catalog, stage_ids={str(stage["id"]) for stage in stages})
    return catalog


def _ensure_prerequisite_dag(terms: tuple[dict[str, Any], ...]) -> None:
    edges = {term["slug"]: set(term.get("prerequisites", [])) for term in terms}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(slug: str) -> None:
        if slug in visiting:
            raise ValueError(f"prerequisite cycle includes {slug}")
        if slug in visited:
            return
        visiting.add(slug)
        for parent in edges.get(slug, set()):
            visit(parent)
        visiting.remove(slug)
        visited.add(slug)

    for slug in edges:
        visit(slug)


def validate_catalog(
    catalog: Catalog, *, stage_ids: set[str] | None = None
) -> None:
    if catalog.locales != tuple(LOCALES):
        raise ValueError("catalog must define exactly the eight supported locales")
    domains = list(catalog.domains)
    topics = list(catalog.topics)
    terms = list(catalog.terms)
    paths = list(catalog.paths)
    _unique(domains, "id", "domain")
    _unique(topics, "id", "topic")
    _unique(terms, "slug", "term")
    _unique(terms, "canonical_name", "term")
    _unique(paths, "slug", "path")

    domain_ids = {domain["id"] for domain in domains}
    topic_ids = {topic["id"] for topic in topics}
    term_slugs = {term["slug"] for term in terms}
    assigned: list[str] = []
    for topic in topics:
        if topic.get("domain") not in domain_ids:
            raise ValueError(f"unknown domain for topic {topic['id']}")
        assigned.extend(topic.get("terms", []))
    if set(assigned) != term_slugs or len(assigned) != len(term_slugs):
        raise ValueError("topics must assign every term exactly once")

    for term in terms:
        slug = term["slug"]
        if term.get("primary_domain") not in domain_ids:
            raise ValueError(f"unknown domain for {slug}: {term.get('primary_domain')}")
        if not set(term.get("topics", [])) <= topic_ids:
            raise ValueError(f"unknown topic for {slug}")
        for related in term.get("related_terms", []):
            if related not in term_slugs:
                raise ValueError(f"unknown related term for {slug}: {related}")
        for prerequisite in term.get("prerequisites", []):
            if prerequisite not in term_slugs:
                raise ValueError(f"unknown prerequisite for {slug}: {prerequisite}")
        if stage_ids is not None and not set(term.get("lifecycle_stages", [])) <= stage_ids:
            raise ValueError(f"unknown lifecycle stage for {slug}")
        if explainer := term.get("visual_explainer"):
            if explainer.get("term") != slug:
                raise ValueError(f"visual explainer term mismatch for {slug}")
        if set(term.get("localized", {})) != set(LOCALES):
            raise ValueError(f"{slug} must have all eight localized records")
        for locale, localized in term["localized"].items():
            if localized["source_content_version"] != term["content_version"]:
                raise ValueError(f"stale source_content_version for {slug}/{locale}")
            exercise = localized["exercise"]
            option_ids = {option["id"] for option in exercise["options"]}
            if exercise["answer"] not in option_ids:
                raise ValueError(f"invalid exercise answer for {slug}/{locale}")

    for path in paths:
        chapter_ids: set[str] = set()
        for chapter in path.get("chapters", []):
            chapter_id = chapter.get("id")
            if chapter_id in chapter_ids:
                raise ValueError(f"duplicate chapter id in {path['slug']}: {chapter_id}")
            chapter_ids.add(chapter_id)
            unknown = set(chapter.get("term_slugs", [])) - term_slugs
            if unknown:
                raise ValueError(f"unknown path terms in {path['slug']}: {sorted(unknown)}")
    _ensure_prerequisite_dag(catalog.terms)

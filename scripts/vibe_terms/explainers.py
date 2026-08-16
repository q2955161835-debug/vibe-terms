from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


PATTERNS = frozenset(
    {
        "anatomy",
        "compare",
        "sequence",
        "state-machine",
        "request-response",
        "pipeline",
        "hierarchy",
        "code-result",
        "data-mapping",
        "lifecycle",
        "boundary",
        "layout",
        "timeline",
        "evidence",
    }
)

COPY_LOCALE = {
    "en": "en",
    "zh-cn": "zh-cn",
    "zh-tw": "zh-cn",
    "ja": "en",
    "ko": "en",
    "de": "en",
    "ru": "en",
}

COPY_LOCALES = frozenset({"en", "zh-cn"})
_SCALAR_TYPES = (str, int, float, bool)


def resolve_explainer_locale(locale: str) -> str:
    try:
        return COPY_LOCALE[locale]
    except KeyError as error:
        raise ValueError(f"unsupported page locale: {locale}") from error


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return dict(value)


def _non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _scalar(value: Any, label: str) -> None:
    if not isinstance(value, _SCALAR_TYPES):
        raise ValueError(f"{label} must be an escaped scalar")


def _unique_ids(records: list[dict[str, Any]], field: str, label: str) -> set[str]:
    identifiers: list[str] = []
    for index, record in enumerate(records, start=1):
        identifiers.append(_non_empty_string(record.get(field), f"{label} {index} {field}"))
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            raise ValueError(f"duplicate {label} {field}: {identifier}")
        seen.add(identifier)
    return seen


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"missing explainer file: {path}") from error
    except yaml.YAMLError as error:
        raise ValueError(f"invalid explainer YAML: {path}") from error
    return _mapping(raw, f"explainer file {path}")


def _validate_copy(copy: Any, state_ids: set[str], label_keys: set[str]) -> dict[str, Any]:
    copy_mapping = _mapping(copy, "copy")
    if set(copy_mapping) != COPY_LOCALES:
        raise ValueError("copy locales must be exactly: en, zh-cn")

    normalized: dict[str, Any] = {}
    for locale in sorted(COPY_LOCALES):
        localized = _mapping(copy_mapping[locale], f"copy/{locale}")
        _non_empty_string(localized.get("heading"), f"copy/{locale} heading")
        _non_empty_string(localized.get("intro"), f"copy/{locale} intro")
        localized_states = _mapping(localized.get("states"), f"copy/{locale} states")
        if set(localized_states) != state_ids:
            raise ValueError(f"copy state keys differ for {locale}")
        for state_id, state_copy in localized_states.items():
            state_mapping = _mapping(state_copy, f"copy/{locale} state {state_id}")
            _non_empty_string(
                state_mapping.get("label"), f"copy/{locale} state {state_id} label"
            )
            _non_empty_string(
                state_mapping.get("conclusion"),
                f"copy/{locale} state {state_id} conclusion",
            )

        labels = _mapping(localized.get("labels"), f"copy/{locale} labels")
        if set(labels) != label_keys:
            raise ValueError(f"copy label keys differ for {locale}")
        for label_key, label in labels.items():
            _non_empty_string(label, f"copy/{locale} label {label_key}")
        normalized[locale] = localized
    return normalized


def _validate_states(states: Any) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    if not isinstance(states, list) or not states:
        raise ValueError("states must be a non-empty list")
    normalized = [_mapping(state, "state") for state in states]
    state_ids = _unique_ids(normalized, "id", "state")
    value_keys: set[str] = set()
    for state in normalized:
        state_id = state["id"]
        focus = state.get("focus")
        if not isinstance(focus, list):
            raise ValueError(f"state {state_id} focus must be a list")
        for target in focus:
            _non_empty_string(target, f"state {state_id} focus target")
        values = _mapping(state.get("values"), f"state {state_id} values")
        for key, value in values.items():
            _non_empty_string(key, f"state {state_id} value key")
            _scalar(value, f"state {state_id} value {key}")
            value_keys.add(key)
    return normalized, state_ids, value_keys


def _validate_scene(
    scene: Any, states: list[dict[str, Any]], value_keys: set[str]
) -> tuple[dict[str, Any], set[str]]:
    normalized = _mapping(scene, "scene")
    nodes = normalized.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("scene nodes must be a non-empty list")
    normalized_nodes = [_mapping(node, "scene node") for node in nodes]
    node_ids = _unique_ids(normalized_nodes, "id", "node")
    label_keys: set[str] = set()
    for node in normalized_nodes:
        node_id = node["id"]
        _non_empty_string(node.get("role"), f"node {node_id} role")
        label_key = _non_empty_string(node.get("label_key"), f"node {node_id} label_key")
        label_keys.add(label_key)
        has_value = "value" in node
        has_value_from = "value_from" in node
        if has_value and has_value_from:
            raise ValueError(f"node {node_id} cannot define both value and value_from")
        if has_value:
            _scalar(node["value"], f"node {node_id} value")
        if has_value_from:
            value_from = _non_empty_string(node["value_from"], f"node {node_id} value_from")
            if value_from not in value_keys:
                raise ValueError(f"unknown value_from key {value_from}")

    for state in states:
        for target in state["focus"]:
            if target not in node_ids:
                raise ValueError(f"unknown focus target {target}")

    relations = normalized.get("relations")
    if not isinstance(relations, list):
        raise ValueError("scene relations must be a list")
    normalized_relations = [_mapping(relation, "scene relation") for relation in relations]
    for relation in normalized_relations:
        for endpoint in ("from", "to"):
            identifier = _non_empty_string(relation.get(endpoint), f"relation {endpoint}")
            if identifier not in node_ids:
                raise ValueError(f"unknown relation endpoint {identifier}")

    normalized["nodes"] = normalized_nodes
    normalized["relations"] = normalized_relations
    return normalized, label_keys


def load_explainer(path: Path, expected_slug: str) -> dict[str, Any]:
    """Load one explainer and reject incomplete or inconsistent scene data."""
    raw = _load_yaml(Path(path))
    if raw.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if raw.get("term") != expected_slug:
        raise ValueError(f"explainer term must be {expected_slug}")
    pattern = raw.get("pattern")
    if pattern not in PATTERNS:
        raise ValueError(f"unknown pattern {pattern}")
    complexity = raw.get("complexity")
    if isinstance(complexity, bool) or not isinstance(complexity, int) or not 1 <= complexity <= 4:
        raise ValueError("complexity must be 1..4")

    states, _, value_keys = _validate_states(raw.get("states"))
    scene, label_keys = _validate_scene(raw.get("scene"), states, value_keys)
    copy = _validate_copy(raw.get("copy"), {state["id"] for state in states}, label_keys)

    normalized = deepcopy(raw)
    normalized["states"] = states
    normalized["scene"] = scene
    normalized["copy"] = copy
    return normalized


def load_explainers(
    content_root: Path, expected_slugs: set[str]
) -> dict[str, dict[str, Any]]:
    """Load the requested canonical explainer subset without inventing copy."""
    root = Path(content_root) / "explainers"
    missing = [slug for slug in sorted(expected_slugs) if not (root / f"{slug}.yaml").is_file()]
    if missing:
        raise ValueError(f"missing explainer files: {', '.join(missing)}")
    return {
        slug: load_explainer(root / f"{slug}.yaml", slug)
        for slug in sorted(expected_slugs)
    }

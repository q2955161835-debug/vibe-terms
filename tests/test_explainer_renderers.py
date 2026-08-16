from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from scripts.vibe_terms.explainers import PATTERNS, load_explainer
from scripts.vibe_terms.explainer_renderers import RENDERERS, render_visual_explainer


ROOT = Path(__file__).resolve().parents[1]
CSS_FIXTURE = ROOT / "tests" / "fixtures" / "explainers" / "css.yaml"


@pytest.fixture
def css_explainer() -> dict[str, Any]:
    return load_explainer(CSS_FIXTURE, "css")


def _explainer(pattern: str, state_count: int) -> dict[str, Any]:
    node_ids = [f"{pattern}-source", f"{pattern}-middle", f"{pattern}-target"]
    state_ids = [f"state-{index}" for index in range(state_count)]
    labels = {node_id: f"{pattern} {index}" for index, node_id in enumerate(node_ids)}
    states = [
        {
            "id": state_id,
            "focus": [node_ids[index % len(node_ids)]],
            "values": {"dynamic": f"value {index}"},
        }
        for index, state_id in enumerate(state_ids)
    ]

    def localized(locale: str) -> dict[str, Any]:
        prefix = "中文" if locale == "zh-cn" else "English"
        return {
            "heading": f"{prefix} {pattern} heading",
            "intro": f"{prefix} {pattern} intro",
            "states": {
                state_id: {
                    "label": f"{prefix} {state_id}",
                    "conclusion": f"{prefix} conclusion {state_id}",
                }
                for state_id in state_ids
            },
            "labels": labels,
        }

    return {
        "pattern": pattern,
        "copy": {"en": localized("en"), "zh-cn": localized("zh-cn")},
        "states": states,
        "scene": {
            "nodes": [
                {
                    "id": node_id,
                    "role": f"role-{pattern}-{index}",
                    "label_key": node_id,
                    "value_from": "dynamic" if index == 1 else None,
                    "value": None if index == 1 else f"static {index}",
                }
                for index, node_id in enumerate(node_ids)
            ],
            "relations": [
                {"from": node_ids[0], "to": node_ids[1]},
                {"from": node_ids[1], "to": node_ids[2]},
            ],
        },
    }


def _valid_explainer(pattern: str, state_count: int) -> dict[str, Any]:
    """Build the same validated shape the renderer consumes, without I/O."""
    explainer = _explainer(pattern, state_count)
    for node in explainer["scene"]["nodes"]:
        if node["value_from"] is None:
            del node["value_from"]
        else:
            del node["value"]
    return explainer


def test_every_allowed_pattern_has_exactly_one_renderer() -> None:
    assert set(RENDERERS) == set(PATTERNS)


def test_renderer_escapes_code_and_keeps_every_state_in_transcript(
    css_explainer: dict[str, Any],
) -> None:
    broken = deepcopy(css_explainer)
    broken["scene"]["nodes"][0]["value"] = "</code><script>alert(1)</script>"

    html = render_visual_explainer(broken, "zh-tw")

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert 'data-explainer-locale="zh-cn"' in html
    assert html.count('class="visual-transcript-item"') == len(broken["states"])


@pytest.mark.parametrize(
    ("pattern", "state_count", "markers"),
    [
        ("anatomy", 1, ('class="visual-anatomy"', '<dl class="visual-anatomy-parts">')),
        ("compare", 2, ('class="visual-compare"', 'class="visual-compare-column"')),
        ("sequence", 3, ('class="visual-sequence"', '<ol class="visual-sequence-steps">')),
        ("state-machine", 4, ('class="visual-state-machine"', 'class="visual-state-machine-transitions"')),
        ("request-response", 2, ('class="visual-request-response"', 'class="visual-request-endpoint"', 'class="visual-contract-panel"')),
        ("pipeline", 3, ('class="visual-pipeline"', '<ol class="visual-pipeline-stages">')),
        ("hierarchy", 4, ('class="visual-hierarchy"', '<ul class="visual-hierarchy-tree">')),
        ("code-result", 2, ('class="visual-code-result"', 'class="visual-code-result-output"')),
        ("data-mapping", 3, ('class="visual-data-mapping"', 'class="visual-mapping-source-column"', 'class="visual-mapping-target-column"')),
        ("lifecycle", 4, ('class="visual-lifecycle"', '<ol class="visual-lifecycle-phases">')),
        ("boundary", 2, ('class="visual-boundary"', 'class="visual-trust-zone"')),
        ("layout", 3, ('class="visual-layout"', 'class="visual-layout-dimension"', '>Width<', '>Height<')),
        ("timeline", 4, ('class="visual-timeline"', '<ol class="visual-timeline-events">')),
        ("evidence", 2, ('class="visual-evidence"', 'class="visual-evidence-claim"', 'class="visual-evidence-sources"')),
    ],
)
def test_each_pattern_preserves_its_specific_semantic_structure(
    pattern: str, state_count: int, markers: tuple[str, ...]
) -> None:
    explainer = _valid_explainer(pattern, state_count)

    html = render_visual_explainer(explainer, "en")

    for marker in markers:
        assert marker in html
    for node in explainer["scene"]["nodes"]:
        assert html.count(f'data-explainer-node="{node["id"]}"') == 1
        assert f"visual-node--{node['role']}" in html
    assert html.count('class="visual-transcript-item"') == state_count
    if state_count == 1:
        assert "visual-state-controls" not in html
    else:
        assert 'class="visual-state-controls" role="group" aria-label=' in html
        assert html.count("data-explainer-state-control=") == state_count


def test_renderer_uses_english_fallback_for_de() -> None:
    html = render_visual_explainer(_valid_explainer("anatomy", 1), "de")

    assert 'data-explainer-locale="en"' in html
    assert "English anatomy heading" in html
    assert "中文 anatomy heading" not in html


def test_renderer_uses_simplified_chinese_fallback_for_traditional_chinese() -> None:
    html = render_visual_explainer(_valid_explainer("anatomy", 1), "zh-tw")

    assert 'data-explainer-locale="zh-cn"' in html
    assert "中文 anatomy heading" in html
    assert "English anatomy heading" not in html


def test_request_response_keeps_a_single_validated_node_unique() -> None:
    explainer = _valid_explainer("request-response", 1)
    explainer["scene"]["nodes"] = explainer["scene"]["nodes"][:1]
    explainer["scene"]["relations"] = []

    html = render_visual_explainer(explainer, "en")

    assert html.count('class="visual-request-endpoint"') == 2
    assert 'class="visual-contract-panel"' in html
    assert html.count('data-explainer-node="request-response-source"') == 1


def test_request_response_describes_a_contract_without_reusing_endpoint_nodes() -> None:
    explainer = _valid_explainer("request-response", 1)
    explainer["scene"]["nodes"] = explainer["scene"]["nodes"][:2]
    explainer["scene"]["relations"] = [
        {"from": "request-response-source", "to": "request-response-middle"}
    ]

    html = render_visual_explainer(explainer, "en")

    assert 'class="visual-contract-relations"' in html
    assert 'data-contract-from="request-response-source"' in html
    assert 'data-contract-to="request-response-middle"' in html
    assert html.count('data-explainer-node="request-response-source"') == 1
    assert html.count('data-explainer-node="request-response-middle"') == 1


def test_hierarchy_keeps_nested_list_structure_without_declared_relations() -> None:
    explainer = _valid_explainer("hierarchy", 1)
    explainer["scene"]["relations"] = []

    html = render_visual_explainer(explainer, "en")

    assert html.count('<ul class="visual-hierarchy') >= 2
    assert html.count("data-explainer-node=") == len(explainer["scene"]["nodes"])

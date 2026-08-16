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
        ("request-response", 2, ('class="visual-request-response"', 'visual-request-endpoint--request', 'visual-request-endpoint--response', 'class="visual-contract-panel"')),
        ("pipeline", 3, ('class="visual-pipeline"', '<ol class="visual-pipeline-stages">')),
        ("hierarchy", 4, ('class="visual-hierarchy"', '<ul class="visual-hierarchy-tree">')),
        ("code-result", 2, ('class="visual-code-result"', 'class="visual-code-result-output"')),
        ("data-mapping", 3, ('class="visual-data-mapping"', 'class="visual-mapping-source-column"', 'class="visual-mapping-target-column"')),
        ("lifecycle", 4, ('class="visual-lifecycle"', '<ol class="visual-lifecycle-phases">')),
        ("boundary", 2, ('class="visual-boundary"', 'class="visual-boundary-relations"')),
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

    assert html.count("data-explainer-endpoint=") == 2
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


def test_request_response_has_distinct_authored_endpoint_roles_and_relation_contract() -> None:
    explainer = _valid_explainer("request-response", 1)

    html = render_visual_explainer(explainer, "en")

    assert 'class="visual-request-endpoint visual-request-endpoint--request"' in html
    assert 'class="visual-request-endpoint visual-request-endpoint--response"' in html
    assert 'data-explainer-endpoint="request"' in html
    assert 'data-explainer-endpoint="response"' in html
    assert 'aria-label="request-response 0"' in html
    assert 'aria-label="request-response 2"' in html
    assert html.count('data-contract-from=') == len(explainer["scene"]["relations"])
    assert html.count('data-contract-to=') == len(explainer["scene"]["relations"])


def test_request_response_derives_endpoint_roles_from_relations_when_reordered() -> None:
    explainer = _valid_explainer("request-response", 1)
    source, middle, target = explainer["scene"]["nodes"]
    explainer["scene"]["nodes"] = [target, source, middle]

    html = render_visual_explainer(explainer, "en")

    assert (
        '<section class="visual-request-endpoint visual-request-endpoint--request" '
        'data-explainer-endpoint="request" aria-label="request-response 0">'
        in html
    )
    assert (
        '<section class="visual-request-endpoint visual-request-endpoint--response" '
        'data-explainer-endpoint="response" aria-label="request-response 2">'
        in html
    )


def test_data_mapping_is_relation_driven_when_nodes_are_reordered() -> None:
    explainer = _valid_explainer("data-mapping", 1)
    source, middle, target = explainer["scene"]["nodes"]
    explainer["scene"]["nodes"] = [target, source, middle]
    explainer["scene"]["relations"] = [
        {"from": source["id"], "to": target["id"]},
        {"from": middle["id"], "to": target["id"]},
    ]

    html = render_visual_explainer(explainer, "en")

    assert html.count('data-mapping-from=') == 2
    assert html.count('data-mapping-to=') == 2
    assert html.count(f'data-mapping-from="{source["id"]}"') == 1
    assert html.count(f'data-mapping-from="{middle["id"]}"') == 1
    assert html.count(f'data-mapping-to="{target["id"]}"') == 2
    assert html.count("data-explainer-node=") == len(explainer["scene"]["nodes"])


def test_boundary_keeps_declared_relation_evidence_without_positional_trust_claims() -> None:
    explainer = _valid_explainer("boundary", 1)
    source, middle, target = explainer["scene"]["nodes"]
    explainer["scene"]["nodes"] = [target, source, middle]
    explainer["scene"]["relations"] = [{"from": target["id"], "to": source["id"]}]

    html = render_visual_explainer(explainer, "en")

    assert "Trusted" not in html
    assert "Untrusted" not in html
    assert html.count('data-boundary-from=') == 1
    assert html.count('data-boundary-to=') == 1
    assert f'data-boundary-from="{target["id"]}"' in html
    assert f'data-boundary-to="{source["id"]}"' in html
    assert html.count("data-explainer-node=") == len(explainer["scene"]["nodes"])


@pytest.mark.parametrize(
    "relations",
    [
        [
            {"from": "hierarchy-source", "to": "hierarchy-middle"},
            {"from": "hierarchy-target", "to": "hierarchy-middle"},
        ],
        [
            {"from": "hierarchy-source", "to": "hierarchy-middle"},
            {"from": "hierarchy-middle", "to": "hierarchy-target"},
            {"from": "hierarchy-target", "to": "hierarchy-source"},
        ],
    ],
    ids=["dag", "cycle"],
)
def test_hierarchy_keeps_every_declared_edge_without_repeating_nodes(
    relations: list[dict[str, str]],
) -> None:
    explainer = _valid_explainer("hierarchy", 1)
    explainer["scene"]["relations"] = relations

    html = render_visual_explainer(explainer, "en")

    assert html.count('data-hierarchy-from=') == len(relations)
    assert html.count('data-hierarchy-to=') == len(relations)
    assert html.count("data-explainer-node=") == len(explainer["scene"]["nodes"])


@pytest.mark.parametrize("pattern", sorted(PATTERNS))
def test_zh_cn_renderer_chrome_has_no_english_labels(pattern: str) -> None:
    html = render_visual_explainer(_valid_explainer(pattern, 2), "zh-cn")

    for english_chrome in (
        "Explainer states",
        "Contract",
        "Option A",
        "Option B",
        "Source",
        "Target",
        "Trusted zone",
        "Untrusted zone",
        "Width",
        "Height",
        "> to <",
    ):
        assert english_chrome not in html


def test_single_node_zh_cn_request_response_localizes_the_empty_response_name() -> None:
    explainer = _valid_explainer("request-response", 1)
    explainer["scene"]["nodes"] = explainer["scene"]["nodes"][:1]
    explainer["scene"]["relations"] = []

    html = render_visual_explainer(explainer, "zh-cn")

    assert 'aria-label="响应端点"' in html
    assert "Response endpoint" not in html


def test_state_machine_relation_text_uses_authored_labels_not_node_ids() -> None:
    explainer = _valid_explainer("state-machine", 1)

    html = render_visual_explainer(explainer, "en")

    assert (
        '<span data-transition-node-ref="state-machine-source">state-machine 0</span>'
        in html
    )
    assert (
        '<span data-transition-node-ref="state-machine-middle">state-machine 1</span>'
        in html
    )

from __future__ import annotations

from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale
from scripts.vibe_terms.explainer_renderers.base import _esc, render_node, render_shell


def _render_context(explainer: dict[str, Any], page_locale: str) -> tuple[dict[str, Any], dict[str, Any]]:
    copy = explainer["copy"][resolve_explainer_locale(page_locale)]
    return copy, explainer["states"][0]


def render_sequence(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    steps = "".join(
        f'<li class="visual-sequence-step">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = f'<div class="visual-sequence"><ol class="visual-sequence-steps">{steps}</ol></div>'
    return render_shell(explainer, page_locale, canvas)


def render_pipeline(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    stages = "".join(
        f'<li class="visual-pipeline-stage">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = f'<div class="visual-pipeline"><ol class="visual-pipeline-stages">{stages}</ol></div>'
    return render_shell(explainer, page_locale, canvas)


def render_request_response(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    request = nodes[0]
    response = nodes[-1] if len(nodes) > 1 else None
    contract_nodes = nodes[1:-1] if response else []
    contract = "".join(render_node(node, copy, state) for node in contract_nodes)
    relations = "".join(
        f'<li data-contract-from="{_esc(relation["from"])}" data-contract-to="{_esc(relation["to"])}">'
        f'{_esc(relation["from"])} to {_esc(relation["to"])}</li>'
        for relation in explainer["scene"]["relations"]
    )
    response_label = (
        _esc(copy["labels"][response["label_key"]])
        if response is not None
        else "Response endpoint"
    )
    response_node = render_node(response, copy, state) if response is not None else ""
    canvas = (
        '<div class="visual-request-response">'
        f'<section class="visual-request-endpoint" aria-label="{_esc(copy["labels"][request["label_key"]])}">'
        f"{render_node(request, copy, state)}</section>"
        f'<section class="visual-contract-panel" aria-label="Contract"><p>Contract</p>{contract}'
        f'<ol class="visual-contract-relations">{relations}</ol></section>'
        f'<section class="visual-request-endpoint" aria-label="{response_label}">'
        f"{response_node}</section></div>"
    )
    return render_shell(explainer, page_locale, canvas)


def render_lifecycle(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    phases = "".join(
        f'<li class="visual-lifecycle-phase">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = f'<div class="visual-lifecycle"><ol class="visual-lifecycle-phases">{phases}</ol></div>'
    return render_shell(explainer, page_locale, canvas)


def render_timeline(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    events = "".join(
        f'<li class="visual-timeline-event">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = f'<div class="visual-timeline"><ol class="visual-timeline-events">{events}</ol></div>'
    return render_shell(explainer, page_locale, canvas)

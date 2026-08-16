from __future__ import annotations

from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale
from scripts.vibe_terms.explainer_renderers.base import _esc, render_node, render_shell


def _render_context(explainer: dict[str, Any], page_locale: str) -> tuple[dict[str, Any], dict[str, Any]]:
    copy = explainer["copy"][resolve_explainer_locale(page_locale)]
    return copy, explainer["states"][0]


def render_compare(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    split = max(1, len(nodes) // 2)
    left = "".join(render_node(node, copy, state) for node in nodes[:split])
    right = "".join(render_node(node, copy, state) for node in nodes[split:])
    canvas = (
        '<div class="visual-compare">'
        f'<section class="visual-compare-column" aria-label="Option A">{left}</section>'
        f'<section class="visual-compare-column" aria-label="Option B">{right}</section></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_code_result(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    sources = "".join(render_node(node, copy, state) for node in nodes[:-1])
    output = render_node(nodes[-1], copy, state)
    canvas = (
        '<div class="visual-code-result">'
        f'<section class="visual-code-result-source" aria-label="Code">{sources}</section>'
        f'<section class="visual-code-result-output" aria-label="Result">{output}</section></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_state_machine(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    states = "".join(
        f'<li class="visual-state-machine-state">{render_node(node, copy, state)}</li>'
        for node in nodes
    )
    transitions = "".join(
        f'<li data-transition-from="{_esc(relation["from"])}" data-transition-to="{_esc(relation["to"])}">'
        f'{_esc(relation["from"])} to {_esc(relation["to"])} </li>'
        for relation in explainer["scene"]["relations"]
    )
    canvas = (
        '<div class="visual-state-machine">'
        f'<ol class="visual-state-machine-states">{states}</ol>'
        f'<ol class="visual-state-machine-transitions">{transitions}</ol></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_evidence(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    claim = render_node(nodes[0], copy, state)
    sources = "".join(
        f'<li>{render_node(node, copy, state)}</li>' for node in nodes[1:]
    )
    canvas = (
        '<div class="visual-evidence">'
        f'<blockquote class="visual-evidence-claim">{claim}</blockquote>'
        f'<ul class="visual-evidence-sources">{sources}</ul></div>'
    )
    return render_shell(explainer, page_locale, canvas)

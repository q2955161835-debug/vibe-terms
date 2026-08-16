from __future__ import annotations

from html import escape
from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)


def render_node(node: dict[str, Any], copy: dict[str, Any], state: dict[str, Any]) -> str:
    label = _esc(copy["labels"][node["label_key"]])
    value = state["values"].get(node.get("value_from"), node.get("value", ""))
    active = " is-active" if node["id"] in state["focus"] else ""
    return (
        f'<article class="visual-node visual-node--{_esc(node["role"])}{active}" '
        f'data-explainer-node="{_esc(node["id"])}"><strong>{label}</strong>'
        f"<code>{_esc(value)}</code></article>"
    )


def render_state_controls(states: list[dict[str, Any]], copy: dict[str, Any]) -> str:
    if len(states) < 2:
        return ""
    buttons = "".join(
        f'<button type="button" data-explainer-state-control="{_esc(state["id"])}" '
        f'aria-pressed="{str(index == 0).lower()}">{_esc(copy["states"][state["id"]]["label"])}</button>'
        for index, state in enumerate(states)
    )
    return (
        '<div class="visual-state-controls" role="group" aria-label="Explainer states">'
        f"{buttons}</div>"
    )


def render_transcript(states: list[dict[str, Any]], copy: dict[str, Any]) -> str:
    items = "".join(
        f'<li class="visual-transcript-item"><strong>{_esc(copy["states"][state["id"]]["label"])}</strong>'
        f'<p>{_esc(copy["states"][state["id"]]["conclusion"])}</p></li>'
        for state in states
    )
    return f'<ol class="visual-transcript">{items}</ol>'


def render_shell(explainer: dict[str, Any], page_locale: str, canvas: str) -> str:
    copy_locale = resolve_explainer_locale(page_locale)
    copy = explainer["copy"][copy_locale]
    states = explainer["states"]
    first = states[0]["id"]
    return (
        f'<section data-visual-explainer data-explainer-pattern="{_esc(explainer["pattern"])}" '
        f'data-explainer-locale="{_esc(copy_locale)}"><h2>{_esc(copy["heading"])}</h2>'
        f'<p>{_esc(copy["intro"])}</p>{render_state_controls(states, copy)}{canvas}'
        f'<p data-explainer-conclusion aria-live="polite">{_esc(copy["states"][first]["conclusion"])}</p>'
        f"{render_transcript(states, copy)}</section>"
    )

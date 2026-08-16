from __future__ import annotations

from html import escape
from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale

_UI_LABELS = {
    "en": {
        "states": "Explainer states",
        "contract": "Contract",
        "response_endpoint": "Response endpoint",
        "option_a": "Option A",
        "option_b": "Option B",
        "code": "Code",
        "result": "Result",
        "width": "Width",
        "height": "Height",
    },
    "zh-cn": {
        "states": "讲解状态",
        "contract": "契约",
        "response_endpoint": "响应端点",
        "option_a": "选项甲",
        "option_b": "选项乙",
        "code": "代码",
        "result": "结果",
        "width": "宽度",
        "height": "高度",
    },
}


def _esc(value: Any) -> str:
    return escape(str(value), quote=True)


def ui_label(page_locale: str, key: str) -> str:
    return _UI_LABELS[resolve_explainer_locale(page_locale)][key]


def render_node(node: dict[str, Any], copy: dict[str, Any], state: dict[str, Any]) -> str:
    label = _esc(copy["labels"][node["label_key"]])
    value = state["values"].get(node.get("value_from"), node.get("value", ""))
    active = " is-active" if node["id"] in state["focus"] else ""
    return (
        f'<article class="visual-node visual-node--{_esc(node["role"])}{active}" '
        f'data-explainer-node="{_esc(node["id"])}"><strong>{label}</strong>'
        f"<code>{_esc(value)}</code></article>"
    )


def render_state_controls(
    states: list[dict[str, Any]], copy: dict[str, Any], page_locale: str
) -> str:
    if len(states) < 2:
        return ""
    buttons = "".join(
        f'<button type="button" data-explainer-state-control="{_esc(state["id"])}" '
        f'aria-pressed="{str(index == 0).lower()}">{_esc(copy["states"][state["id"]]["label"])}</button>'
        for index, state in enumerate(states)
    )
    return (
        f'<div class="visual-state-controls" role="group" aria-label="{_esc(ui_label(page_locale, "states"))}">'
        f"{buttons}</div>"
    )


def render_transcript(states: list[dict[str, Any]], copy: dict[str, Any]) -> str:
    items = "".join(
        f'<li class="visual-transcript-item"><strong>{_esc(copy["states"][state["id"]]["label"])}</strong>'
        f'<p>{_esc(copy["states"][state["id"]]["conclusion"])}</p></li>'
        for state in states
    )
    return f'<ol class="visual-transcript">{items}</ol>'


def render_state_metadata(explainer: dict[str, Any], copy: dict[str, Any]) -> str:
    dynamic_nodes = [
        node for node in explainer["scene"]["nodes"] if node.get("value_from")
    ]
    metadata = []
    for state in explainer["states"]:
        state_id = state["id"]
        focus = "".join(
            f'<span data-explainer-state-focus="{_esc(node_id)}"></span>'
            for node_id in state["focus"]
        )
        values = "".join(
            f'<span data-explainer-state-value-for="{_esc(node["id"])}">'
            f'{_esc(state["values"][node["value_from"]])}</span>'
            for node in dynamic_nodes
        )
        metadata.append(
            f'<div data-explainer-state="{_esc(state_id)}" '
            f'data-explainer-conclusion="{_esc(copy["states"][state_id]["conclusion"])}" '
            f'hidden aria-hidden="true">{focus}{values}</div>'
        )
    return "".join(metadata)


def render_shell(explainer: dict[str, Any], page_locale: str, canvas: str) -> str:
    copy_locale = resolve_explainer_locale(page_locale)
    copy = explainer["copy"][copy_locale]
    states = explainer["states"]
    first = states[0]["id"]
    return (
        f'<section data-visual-explainer data-explainer-pattern="{_esc(explainer["pattern"])}" '
        f'data-explainer-locale="{_esc(copy_locale)}"><h2>{_esc(copy["heading"])}</h2>'
        f'<p>{_esc(copy["intro"])}</p>{render_state_controls(states, copy, copy_locale)}{canvas}'
        f'<p data-explainer-conclusion aria-live="polite">{_esc(copy["states"][first]["conclusion"])}</p>'
        f"{render_state_metadata(explainer, copy)}"
        f"{render_transcript(states, copy)}</section>"
    )

from __future__ import annotations

from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale
from scripts.vibe_terms.explainer_renderers.base import _esc, render_node, render_shell


def _render_context(explainer: dict[str, Any], page_locale: str) -> tuple[dict[str, Any], dict[str, Any]]:
    copy = explainer["copy"][resolve_explainer_locale(page_locale)]
    return copy, explainer["states"][0]


def render_anatomy(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    parts = "".join(
        f'<div><dt>{_esc(copy["labels"][node["label_key"]])}</dt><dd>{render_node(node, copy, state)}</dd></div>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = f'<div class="visual-anatomy"><dl class="visual-anatomy-parts">{parts}</dl></div>'
    return render_shell(explainer, page_locale, canvas)


def render_hierarchy(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    by_id = {node["id"]: node for node in nodes}
    children: dict[str, list[str]] = {node["id"]: [] for node in nodes}
    targets: set[str] = set()
    for relation in explainer["scene"]["relations"]:
        children[relation["from"]].append(relation["to"])
        targets.add(relation["to"])
    rendered: set[str] = set()

    def branch(node_id: str, ancestors: set[str]) -> str:
        if node_id in rendered or node_id in ancestors:
            return ""
        rendered.add(node_id)
        descendants = "".join(branch(child, ancestors | {node_id}) for child in children[node_id])
        nested = f'<ul class="visual-hierarchy-children">{descendants}</ul>' if descendants else ""
        return f"<li>{render_node(by_id[node_id], copy, state)}{nested}</li>"

    roots = [node["id"] for node in nodes if node["id"] not in targets]
    tree = "".join(branch(root, set()) for root in roots)
    tree += "".join(branch(node["id"], set()) for node in nodes)
    canvas = (
        '<div class="visual-hierarchy"><ul class="visual-hierarchy-tree">'
        f'<li class="visual-hierarchy-root"><ul class="visual-hierarchy-children">{tree}</ul></li>'
        "</ul></div>"
    )
    return render_shell(explainer, page_locale, canvas)


def render_data_mapping(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    midpoint = max(1, len(nodes) // 2)
    sources = "".join(render_node(node, copy, state) for node in nodes[:midpoint])
    targets = "".join(render_node(node, copy, state) for node in nodes[midpoint:])
    canvas = (
        '<div class="visual-data-mapping">'
        f'<section class="visual-mapping-source-column" aria-label="Source">{sources}</section>'
        f'<section class="visual-mapping-target-column" aria-label="Target">{targets}</section></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_boundary(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    split = max(1, (len(nodes) + 1) // 2)
    trusted = "".join(render_node(node, copy, state) for node in nodes[:split])
    untrusted = "".join(render_node(node, copy, state) for node in nodes[split:])
    canvas = (
        '<div class="visual-boundary">'
        f'<section class="visual-trust-zone" aria-label="Trusted zone">{trusted}</section>'
        f'<section class="visual-trust-zone" aria-label="Untrusted zone">{untrusted}</section></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_layout(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    cells = "".join(
        f'<li class="visual-layout-cell">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = (
        '<div class="visual-layout"><p class="visual-layout-dimension"><span>Width</span><span>Height</span></p>'
        f'<ul class="visual-layout-grid">{cells}</ul></div>'
    )
    return render_shell(explainer, page_locale, canvas)

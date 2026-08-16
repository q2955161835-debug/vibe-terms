from __future__ import annotations

from typing import Any

from scripts.vibe_terms.explainers import resolve_explainer_locale
from scripts.vibe_terms.explainer_renderers.base import _esc, render_node, render_shell, ui_label


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
        if node_id in ancestors:
            return (
                f'<li class="visual-hierarchy-reference" data-hierarchy-node-ref="{_esc(node_id)}">'
                f'{_esc(copy["labels"][by_id[node_id]["label_key"]])}</li>'
            )
        if node_id in rendered:
            return ""
        rendered.add(node_id)
        descendants = "".join(branch(child, ancestors | {node_id}) for child in children[node_id])
        nested = f'<ul class="visual-hierarchy-children">{descendants}</ul>' if descendants else ""
        return f"<li>{render_node(by_id[node_id], copy, state)}{nested}</li>"

    roots = [node["id"] for node in nodes if node["id"] not in targets]
    tree = "".join(branch(root, set()) for root in roots)
    tree += "".join(branch(node["id"], set()) for node in nodes)
    relation_evidence = "".join(
        f'<li data-hierarchy-from="{_esc(relation["from"])}" data-hierarchy-to="{_esc(relation["to"])}">'
        f'<span data-hierarchy-node-ref="{_esc(relation["from"])}">{_esc(copy["labels"][by_id[relation["from"]]["label_key"]])}</span>'
        f'<span data-hierarchy-node-ref="{_esc(relation["to"])}">{_esc(copy["labels"][by_id[relation["to"]]["label_key"]])}</span></li>'
        for relation in explainer["scene"]["relations"]
    )
    canvas = (
        '<div class="visual-hierarchy"><ul class="visual-hierarchy-tree">'
        f'<li class="visual-hierarchy-root"><ul class="visual-hierarchy-children">{tree}</ul></li>'
        f'</ul><ol class="visual-hierarchy-relations">{relation_evidence}</ol></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_data_mapping(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    by_id = {node["id"]: node for node in nodes}
    relations = explainer["scene"]["relations"]
    source_ids = list(dict.fromkeys(relation["from"] for relation in relations))
    target_ids = list(dict.fromkeys(relation["to"] for relation in relations))
    sources = "".join(
        f'<li data-mapping-node-ref="{_esc(node_id)}">{_esc(copy["labels"][by_id[node_id]["label_key"]])}</li>'
        for node_id in source_ids
    )
    targets = "".join(
        f'<li data-mapping-node-ref="{_esc(node_id)}">{_esc(copy["labels"][by_id[node_id]["label_key"]])}</li>'
        for node_id in target_ids
    )
    mapping_relations = "".join(
        f'<li data-mapping-from="{_esc(relation["from"])}" data-mapping-to="{_esc(relation["to"])}">'
        f'<span data-mapping-node-ref="{_esc(relation["from"])}">{_esc(copy["labels"][by_id[relation["from"]]["label_key"]])}</span>'
        f'<span data-mapping-node-ref="{_esc(relation["to"])}">{_esc(copy["labels"][by_id[relation["to"]]["label_key"]])}</span></li>'
        for relation in relations
    )
    node_catalog = "".join(f"<li>{render_node(node, copy, state)}</li>" for node in nodes)
    columns = (
        '<section class="visual-mapping-source-column"><ul>'
        f"{sources}</ul></section><section class=\"visual-mapping-target-column\"><ul>{targets}</ul></section>"
        if relations
        else ""
    )
    canvas = (
        '<div class="visual-data-mapping">'
        f'{columns}<ol class="visual-mapping-relations">{mapping_relations}</ol>'
        f'<ul class="visual-mapping-nodes">{node_catalog}</ul></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_boundary(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    nodes = explainer["scene"]["nodes"]
    by_id = {node["id"]: node for node in nodes}
    relations = "".join(
        f'<li data-boundary-from="{_esc(relation["from"])}" data-boundary-to="{_esc(relation["to"])}">'
        f'<span data-boundary-node-ref="{_esc(relation["from"])}">{_esc(copy["labels"][by_id[relation["from"]]["label_key"]])}</span>'
        f'<span data-boundary-node-ref="{_esc(relation["to"])}">{_esc(copy["labels"][by_id[relation["to"]]["label_key"]])}</span></li>'
        for relation in explainer["scene"]["relations"]
    )
    node_catalog = "".join(f"<li>{render_node(node, copy, state)}</li>" for node in nodes)
    canvas = (
        '<div class="visual-boundary">'
        f'<ol class="visual-boundary-relations">{relations}</ol>'
        f'<ul class="visual-boundary-nodes">{node_catalog}</ul></div>'
    )
    return render_shell(explainer, page_locale, canvas)


def render_layout(explainer: dict[str, Any], page_locale: str) -> str:
    copy, state = _render_context(explainer, page_locale)
    cells = "".join(
        f'<li class="visual-layout-cell">{render_node(node, copy, state)}</li>'
        for node in explainer["scene"]["nodes"]
    )
    canvas = (
        f'<div class="visual-layout"><p class="visual-layout-dimension"><span>{_esc(ui_label(page_locale, "width"))}</span><span>{_esc(ui_label(page_locale, "height"))}</span></p>'
        f'<ul class="visual-layout-grid">{cells}</ul></div>'
    )
    return render_shell(explainer, page_locale, canvas)

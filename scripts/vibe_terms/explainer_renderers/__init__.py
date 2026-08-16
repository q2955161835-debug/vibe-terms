from __future__ import annotations

from typing import Any, Callable

from .decisions import (
    render_code_result,
    render_compare,
    render_evidence,
    render_state_machine,
)
from .flows import (
    render_lifecycle,
    render_pipeline,
    render_request_response,
    render_sequence,
    render_timeline,
)
from .structures import (
    render_anatomy,
    render_boundary,
    render_data_mapping,
    render_hierarchy,
    render_layout,
)


Renderer = Callable[[dict[str, Any], str], str]

RENDERERS: dict[str, Renderer] = {
    "anatomy": render_anatomy,
    "compare": render_compare,
    "sequence": render_sequence,
    "state-machine": render_state_machine,
    "request-response": render_request_response,
    "pipeline": render_pipeline,
    "hierarchy": render_hierarchy,
    "code-result": render_code_result,
    "data-mapping": render_data_mapping,
    "lifecycle": render_lifecycle,
    "boundary": render_boundary,
    "layout": render_layout,
    "timeline": render_timeline,
    "evidence": render_evidence,
}


def render_visual_explainer(explainer: dict[str, Any], page_locale: str) -> str:
    return RENDERERS[explainer["pattern"]](explainer, page_locale)

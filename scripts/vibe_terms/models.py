from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Catalog:
    locales: tuple[str, ...]
    domains: tuple[dict[str, Any], ...]
    topics: tuple[dict[str, Any], ...]
    terms: tuple[dict[str, Any], ...]
    paths: tuple[dict[str, Any], ...]

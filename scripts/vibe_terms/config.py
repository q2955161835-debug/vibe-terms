from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


LOCALES = ("en", "zh-cn", "zh-tw", "ja", "ko", "de", "ru")
HTML_LANG = {
    "en": "en",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "ja": "ja",
    "ko": "ko",
    "de": "de",
    "ru": "ru",
}
LANGUAGE_NAMES = {
    "en": "English",
    "zh-cn": "简体中文",
    "zh-tw": "繁體中文",
    "ja": "日本語",
    "ko": "한국어",
    "de": "Deutsch",
    "ru": "Русский",
}
PRODUCT_NAME = "Vibe Terms"


@dataclass(frozen=True)
class BuildConfig:
    content_root: Path
    output_root: Path
    site_url: str
    base_path: str
    minimum_terms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_root", Path(self.content_root).resolve())
        object.__setattr__(self, "output_root", Path(self.output_root).resolve())
        if self.minimum_terms < 1:
            raise ValueError("minimum_terms must be positive")

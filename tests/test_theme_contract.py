from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
THEME_TOKENS = {
    "--canvas", "--canvas-subtle", "--panel", "--panel-raised",
    "--panel-muted", "--text-primary", "--text-secondary", "--text-faint",
    "--border", "--border-strong", "--accent", "--accent-surface",
    "--accent-contrast", "--focus-ring",
}


def test_styles_define_every_semantic_token_for_light_dark_and_system() -> None:
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    for selector in (':root[data-theme="light"]', ':root[data-theme="dark"]'):
        block = css.split(selector, 1)[1].split("}", 1)[0]
        assert THEME_TOKENS <= set(re.findall(r"--[a-z-]+(?=\s*:)", block))
    assert '@media (prefers-color-scheme: dark)' in css
    assert ':root[data-theme="system"]' in css


def test_clarity_components_do_not_force_light_surfaces() -> None:
    css = (ROOT / "web" / "clarity.css").read_text(encoding="utf-8")
    for forbidden in ("background: #fff", "background: #ffffff", "color: #11151c"):
        assert forbidden not in css.lower()

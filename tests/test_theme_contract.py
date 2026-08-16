from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
THEME_TOKENS = {
    "--canvas", "--canvas-subtle", "--panel", "--panel-raised",
    "--panel-muted", "--text-primary", "--text-secondary", "--text-faint",
    "--border", "--border-strong", "--accent", "--accent-surface",
    "--accent-contrast", "--focus-ring",
}


def _tokens(block: str) -> set[str]:
    return set(re.findall(r"--[a-z-]+(?=\s*:)", block))


def _system_block(css: str, scheme: str) -> str:
    match = re.search(
        rf'@media \(prefers-color-scheme: {scheme}\) \{{\s*'
        r':root\[data-theme="system"\] \{(?P<block>.*?)\n  \}',
        css,
        re.DOTALL,
    )
    assert match is not None
    return match.group("block")


def test_styles_define_every_semantic_token_for_light_dark_and_system() -> None:
    css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    for selector, scheme in ((
        ':root[data-theme="light"]', "light"),
        (':root[data-theme="dark"]', "dark"),
    ):
        block = css.split(selector, 1)[1].split("}", 1)[0]
        assert THEME_TOKENS <= _tokens(block)
        assert re.search(rf"color-scheme:\s*{scheme}\s*;", block)
    for scheme in ("light", "dark"):
        block = _system_block(css, scheme)
        assert THEME_TOKENS <= _tokens(block)
        assert re.search(rf"color-scheme:\s*{scheme}\s*;", block)


def test_clarity_components_do_not_force_light_surfaces() -> None:
    css = (ROOT / "web" / "clarity.css").read_text(encoding="utf-8")
    for forbidden in ("background: #fff", "background: #ffffff", "color: #11151c"):
        assert forbidden not in css.lower()


def test_explorer_and_term_navigation_keep_visible_interaction_cues() -> None:
    css = (ROOT / "web" / "clarity.css").read_text(encoding="utf-8")
    assert ".explorer-tabs::-webkit-scrollbar" in css
    assert "scrollbar-width: thin" in css
    assert ".term-card-head a::after" in css
    assert '.term-actions [data-bookmark][aria-pressed="true"]' in css
    assert ".term-pagination a[rel=\"next\"]" in css

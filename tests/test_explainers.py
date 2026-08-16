from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from scripts.vibe_terms.explainers import load_explainer, resolve_explainer_locale


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "explainers" / "css.yaml"


@pytest.mark.parametrize(
    ("page_locale", "copy_locale"),
    [
        ("en", "en"),
        ("zh-cn", "zh-cn"),
        ("zh-tw", "zh-cn"),
        ("ja", "en"),
        ("ko", "en"),
        ("de", "en"),
        ("ru", "en"),
    ],
)
def test_visual_copy_locale_is_explicit(page_locale: str, copy_locale: str) -> None:
    assert resolve_explainer_locale(page_locale) == copy_locale


def test_explainer_rejects_missing_focus_targets(tmp_path: Path) -> None:
    path = tmp_path / "css.yaml"
    path.write_text(
        """
schema_version: 1
term: css
pattern: code-result
complexity: 2
copy:
  en: {heading: CSS result, intro: Follow the rule, states: {base: {label: Base, conclusion: Result}}, labels: {source: Source}}
  zh-cn: {heading: CSS 结果, intro: 观察规则, states: {base: {label: 基础, conclusion: 结果}}, labels: {source: 源码}}
states: [{id: base, focus: [missing], values: {}}]
scene: {nodes: [{id: source, role: code, label_key: source, value: rule}], relations: []}
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown focus target missing"):
        load_explainer(path, "css")


def test_explainer_normalizes_a_complete_fixture_without_generic_copy() -> None:
    explainer = load_explainer(FIXTURE, "css")

    assert explainer["term"] == "css"
    assert explainer["copy"]["en"]["heading"] == (
        "How two CSS rules decide the final button color"
    )
    assert explainer["states"][1]["values"]["computed-color"] == "#db2777"


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda item: item.__setitem__("pattern", "unknown"), "unknown pattern unknown"),
        (
            lambda item: item["copy"].pop("zh-cn"),
            "copy locales must be exactly: en, zh-cn",
        ),
        (
            lambda item: item["copy"]["zh-cn"]["states"].__setitem__(
                "different", item["copy"]["zh-cn"]["states"].pop("base")
            ),
            "copy state keys differ for zh-cn",
        ),
        (
            lambda item: item["scene"]["nodes"].append(
                deepcopy(item["scene"]["nodes"][0])
            ),
            "duplicate node id: primary-rule",
        ),
        (
            lambda item: item["scene"]["relations"][0].__setitem__("to", "missing"),
            "unknown relation endpoint missing",
        ),
        (lambda item: item.__setitem__("complexity", 5), "complexity must be 1..4"),
    ],
)
def test_explainer_rejects_invalid_contract_variants(
    tmp_path: Path, mutate, error: str
) -> None:
    item = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    mutate(item)
    path = tmp_path / "css.yaml"
    path.write_text(yaml.safe_dump(item, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        load_explainer(path, "css")


def test_audit_lists_only_missing_requested_domain_slugs() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            "scripts/audit_explainers.py",
            "--domains",
            "frontend-engineering",
            "--list-missing",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    expected = sorted(
        path.parent.name
        for path in (ROOT / "content" / "terms").glob("*/meta.yaml")
        if yaml.safe_load(path.read_text(encoding="utf-8"))["primary_domain"]
        == "frontend-engineering"
    )
    assert completed.stdout.splitlines() == expected
    assert "frontend-engineering: 0/" in completed.stderr
    assert "patterns: none" in completed.stderr
    assert "complexities: none" in completed.stderr

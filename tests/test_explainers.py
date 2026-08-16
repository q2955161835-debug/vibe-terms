from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from scripts import audit_explainers
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


def test_every_dynamic_node_resolves_in_every_renderer_state(tmp_path: Path) -> None:
    """The renderer reads every scene node for every state, not only focused nodes."""
    item = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    item["states"][1]["values"].pop("computed-color")
    path = tmp_path / "css.yaml"
    path.write_text(yaml.safe_dump(item, allow_unicode=True), encoding="utf-8")

    with pytest.raises(
        ValueError, match="state override is missing value_from key computed-color"
    ):
        load_explainer(path, "css")


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (
            lambda item: item.__setitem__("schema_version", True),
            "schema_version must be exactly integer 1",
        ),
        (
            lambda item: item.__setitem__("unexpected", True),
            "unknown root keys: unexpected",
        ),
        (
            lambda item: item["states"][0].__setitem__("unexpected", True),
            "unknown state keys: unexpected",
        ),
        (
            lambda item: item["scene"].__setitem__("unexpected", True),
            "unknown scene keys: unexpected",
        ),
        (
            lambda item: item["scene"]["nodes"][0].__setitem__("unexpected", True),
            "unknown node keys: unexpected",
        ),
        (
            lambda item: item["scene"]["relations"][0].__setitem__(
                "unexpected", True
            ),
            "unknown relation keys: unexpected",
        ),
        (
            lambda item: item["copy"]["en"].__setitem__("unexpected", True),
            "unknown copy/en keys: unexpected",
        ),
        (
            lambda item: item["copy"]["en"]["states"]["base"].__setitem__(
                "unexpected", True
            ),
            "unknown copy/en state base keys: unexpected",
        ),
        (
            lambda item: item["copy"]["en"]["labels"].__setitem__(
                "unexpected", "Unexpected"
            ),
            "unknown copy/en label keys: unexpected",
        ),
        (
            lambda item: item["states"][0]["values"].__setitem__(
                "unexpected", "Unexpected"
            ),
            "unknown state base value keys: unexpected",
        ),
    ],
)
def test_explainer_rejects_unknown_contract_keys(
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
    frontend_slugs = {
        path.parent.name
        for path in (ROOT / "content" / "terms").glob("*/meta.yaml")
        if yaml.safe_load(path.read_text(encoding="utf-8"))["primary_domain"]
        == "frontend-engineering"
    }
    expected = sorted(
        slug
        for slug in frontend_slugs
        if not (ROOT / "content" / "explainers" / f"{slug}.yaml").is_file()
    )
    assert completed.stdout.splitlines() == expected
    assert f"frontend-engineering: {len(frontend_slugs) - len(expected)}/{len(frontend_slugs)}" in completed.stderr
    assert "patterns:" in completed.stderr
    assert "complexities:" in completed.stderr


def test_audit_list_missing_emits_no_blank_line_when_subset_is_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    content = tmp_path / "content"
    explainer_dir = content / "explainers"
    explainer_dir.mkdir(parents=True)
    shutil.copy(FIXTURE, explainer_dir / "css.yaml")
    arguments = argparse.Namespace(
        domains=["frontend-engineering"], list_missing=True, require_complete=False
    )
    monkeypatch.setattr(audit_explainers, "CONTENT", content)
    monkeypatch.setattr(audit_explainers, "parse_args", lambda: arguments)
    monkeypatch.setattr(
        audit_explainers,
        "_selected_terms",
        lambda _domains: ({"css": "frontend-engineering"}, ["frontend-engineering"]),
    )

    assert audit_explainers.main() == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "frontend-engineering: 1/1" in captured.err

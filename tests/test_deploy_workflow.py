from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pages_workflow_runs_the_full_verifier_before_upload() -> None:
    workflow = (ROOT / ".github" / "workflows" / "deploy-pages.yml").read_text(
        encoding="utf-8"
    )
    verifier = "RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh"
    upload = "actions/upload-pages-artifact@"
    assert "requirements-dev.txt" in workflow
    assert "playwright install --with-deps chromium" in workflow
    assert verifier in workflow
    assert workflow.index(verifier) < workflow.index(upload)

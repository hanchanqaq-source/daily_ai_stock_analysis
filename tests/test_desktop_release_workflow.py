# -*- coding: utf-8 -*-
"""Contracts for recoverable fixed-commit Desktop releases."""

from pathlib import Path
import subprocess

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "desktop-release.yml"


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _workflow() -> dict:
    return yaml.load(_workflow_text(), Loader=yaml.BaseLoader)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_manual_release_inputs_and_concurrency_are_tag_scoped() -> None:
    workflow = _workflow()
    dispatch_inputs = workflow["on"]["workflow_dispatch"]["inputs"]

    assert set(dispatch_inputs) == {
        "release_tag",
        "release_commit",
        "release_message",
    }
    assert all(value["required"] == "true" for value in dispatch_inputs.values())
    assert workflow["concurrency"]["group"] == (
        "desktop-release-${{ github.event_name == 'workflow_dispatch' "
        "&& inputs.release_tag || github.ref_name }}"
    )


def test_preflight_validates_fixed_commit_and_builds_checkout_its_output() -> None:
    workflow = _workflow()
    jobs = workflow["jobs"]
    preflight = jobs["preflight"]
    text = _workflow_text()

    assert preflight["permissions"] == {"contents": "read"}
    assert set(preflight["outputs"]) == {
        "release_tag",
        "release_commit",
        "release_message",
    }
    assert "^[0-9a-fA-F]{40}$" in text
    assert "^v(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$" in text
    assert 'if [[ "${GITHUB_EVENT_NAME}" == "workflow_dispatch" ]] &&' in text
    assert 'git cat-file -t "${release_commit}"' in text
    assert '"${release_object_type}" != "commit"' in text
    assert "git merge-base --is-ancestor" in text
    assert "origin/main" in text

    for job_name in ("build-windows", "build-macos"):
        job = jobs[job_name]
        assert job["needs"] == "preflight"
        checkout = job["steps"][0]
        assert checkout["uses"] == "actions/checkout@v5"
        assert checkout["with"]["ref"] == (
            "${{ needs.preflight.outputs.release_commit }}"
        )


def test_tag_and_release_guards_are_recoverable_and_fail_closed() -> None:
    workflow = _workflow()
    jobs = workflow["jobs"]
    preflight_text = str(jobs["preflight"])
    publish_text = str(jobs["publish-release"])
    workflow_text = _workflow_text()

    assert "git cat-file -t" in workflow_text
    assert "lightweight" in workflow_text
    assert "refs/tags/${RELEASE_TAG}^{}" in workflow_text
    assert "remote_target_object" in workflow_text
    assert "remote_target_type" in workflow_text
    assert "remote_tag_name" in workflow_text
    assert '"${remote_target_object}" != "${release_commit}"' in workflow_text
    assert '"${remote_target_type}" != "commit"' in workflow_text
    assert '"${remote_tag_name}" != "${release_tag}"' in workflow_text
    assert "gh api" in preflight_text
    assert "404" in preflight_text
    assert "unable to confirm release state" in workflow_text.lower()

    assert "git tag -a" in publish_text
    assert "refs/tags/${RELEASE_TAG}:refs/tags/${RELEASE_TAG}" in publish_text
    assert "--force" not in publish_text
    assert "gh release create" in publish_text
    assert "--verify-tag" in publish_text
    assert "softprops/action-gh-release" not in workflow_text


def test_git_object_fixtures_distinguish_commit_and_nested_tag_targets(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "PP02 Test")
    _git(repo, "config", "user.email", "pp02-test@example.invalid")
    _git(repo, "commit", "--allow-empty", "-m", "release target")
    release_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "tag", "-a", "v1.2.3", release_commit, "-m", "release")
    _git(repo, "tag", "-a", "nested", "v1.2.3", "-m", "nested")

    tag_object = _git(repo, "rev-parse", "refs/tags/v1.2.3")
    assert _git(repo, "cat-file", "-t", release_commit) == "commit"
    assert _git(repo, "cat-file", "-t", tag_object) == "tag"

    direct_header = _git(repo, "cat-file", "-p", "refs/tags/v1.2.3")
    nested_header = _git(repo, "cat-file", "-p", "refs/tags/nested")
    assert f"object {release_commit}" in direct_header
    assert "type commit" in direct_header
    assert "type tag" in nested_header


def test_publish_is_single_run_after_all_builds_with_minimal_permissions() -> None:
    workflow = _workflow()
    jobs = workflow["jobs"]
    publish = jobs["publish-release"]

    assert publish["needs"] == ["preflight", "build-windows", "build-macos"]
    assert publish["permissions"] == {"contents": "write"}
    assert jobs["safe-candidate"]["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    for name, job in jobs.items():
        if name not in {"publish-release", "safe-candidate"}:
            assert job["permissions"] == {"contents": "read"}

    workflow_text = _workflow_text()
    assert "push:" in workflow_text
    assert "tags:" in workflow_text
    assert workflow_text.index("git tag -a") < workflow_text.index(
        "gh release create"
    )


def test_windows_final_zip_cleanup_retries_locked_files_and_fails_closed() -> None:
    workflow = _workflow()
    windows_steps = workflow["jobs"]["build-windows"]["steps"]
    prepare_step = next(
        step
        for step in windows_steps
        if step.get("name") == "Prepare release artifact (Windows)"
    )
    script = prepare_step["run"]

    assert "function Remove-OwnedReleaseDirectoryWithRetry" in script
    assert "for ($attempt = 1; $attempt -le 15; $attempt++)" in script
    assert (
        "Remove-Item -LiteralPath $OwnedRoot -Recurse -Force "
        "-ErrorAction Stop"
    ) in script
    assert "if ($attempt -eq 15)" in script
    assert "Start-Sleep -Seconds 1" in script
    assert (
        "Failed to remove release-owned extraction directory after "
        "$attempt attempts."
    ) in script

    cleanup_call = (
        "Remove-OwnedReleaseDirectoryWithRetry "
        "-OwnedRoot $releaseFinalExtract"
    )
    assert script.count(cleanup_call) == 2
    assert script.index("outside the owned runner root") < script.index(cleanup_call)
    assert (
        "Remove-Item -LiteralPath $releaseFinalExtract -Recurse -Force"
        not in script
    )


def test_pre_lifecycle_failure_does_not_add_diagnostic_upload_error() -> None:
    windows_steps = _workflow()["jobs"]["build-windows"]["steps"]
    installer_diagnostics = next(
        step
        for step in windows_steps
        if step.get("name") == "Upload Windows installer diagnostics"
    )
    defender_reports = next(
        step
        for step in windows_steps
        if step.get("name") == "Upload Windows Defender reports"
    )

    assert installer_diagnostics["if"] == "always()"
    assert installer_diagnostics["with"]["if-no-files-found"] == "warn"
    assert defender_reports["if"] == "always()"
    assert defender_reports["with"]["if-no-files-found"] == "error"

    ci_workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    ci_workflow = yaml.load(
        ci_workflow_path.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    ci_windows_steps = ci_workflow["jobs"]["desktop-futu-package-windows"]["steps"]
    ci_installer_diagnostics = next(
        step
        for step in ci_windows_steps
        if step.get("name") == "📤 Upload Windows installer diagnostics"
    )
    assert ci_installer_diagnostics["with"]["if-no-files-found"] == "error"

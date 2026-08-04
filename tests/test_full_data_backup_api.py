"""HTTP contracts for the formal PP02 full-data backup API."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.middlewares.error_handler import add_error_handlers
from src.services.full_data_backup_service import (
    FullDataBackupConflictError,
    FullDataBackupValidationError,
)


def _backup_document() -> dict:
    document = {
        "format": "pp02.full-data.backup",
        "format_version": 1,
        "metadata": {
            "application_version": "test-app-7.4.1",
            "created_at": "2026-08-04T12:34:56+00:00",
            "database_schema_version": 1,
            "project_id": "PP02",
            "project_name": "AI 每日股票分析",
        },
        "manifest": {
            "table_row_counts": {"analysis_history": 1},
            "categories": {"analysis": {"status": "included"}},
            "excluded": ["credentials"],
        },
        "data": {"configuration": {"values": {}}, "tables": {"analysis_history": []}},
        "integrity": {"algorithm": "sha256", "value": ""},
    }
    digest_source = copy.deepcopy(document)
    del digest_source["integrity"]["value"]
    document["integrity"]["value"] = hashlib.sha256(
        json.dumps(
            digest_source,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return document


def _load_endpoint_module():
    path = Path(__file__).resolve().parents[1] / "api" / "v1" / "endpoints" / "full_data_backup.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("full_data_backup_endpoint_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _BackupServiceStub:
    def __init__(self, document: dict) -> None:
        self.document = document
        self.preview_error: BaseException | None = None
        self.restore_error: BaseException | None = None
        self.export_error: BaseException | None = None
        self.restore_warnings: list[str] = []

    def export_backup(self) -> dict:
        if self.export_error:
            raise self.export_error
        return self.document

    def preview_restore(self, backup: dict) -> dict:
        if self.preview_error:
            raise self.preview_error
        assert backup == self.document
        return {
            "preview_token": "preview-token-123",
            "incoming_digest": "a" * 64,
            "destination_digest": "b" * 64,
            "issued_at": "2026-08-04T12:34:56+00:00",
            "expires_at": "2026-08-04T12:39:56+00:00",
            "incoming_table_row_counts": {"analysis_history": 1},
            "destination_table_row_counts": {"analysis_history": 3},
            "restart_required": True,
        }

    def restore_backup(self, backup: dict, *, preview_token: str) -> dict:
        if self.restore_error:
            raise self.restore_error
        assert backup == self.document
        assert preview_token == "preview-token-123"
        return {
            "success": True,
            "incoming_digest": "a" * 64,
            "destination_digest_before": "b" * 64,
            "destination_digest_after": "c" * 64,
            "restored_table_row_counts": {"analysis_history": 1},
            "recovery_filename": "pp02-full-data-recovery-20260804T123456Z.json",
            "recovery": {
                "directory": "/private/recovery",
                "filename": "pp02-full-data-recovery-20260804T123456Z.json",
                "path": "/private/recovery/pp02-full-data-recovery-20260804T123456Z.json",
                "digest": "d" * 64,
                "destination_digest": "b" * 64,
            },
            "restart_required": True,
            "warnings": list(self.restore_warnings),
        }


def _client(service: _BackupServiceStub) -> TestClient:
    endpoint = _load_endpoint_module()
    assert endpoint is not None, "Task 5 must provide api.v1.endpoints.full_data_backup"
    app = FastAPI()
    app.include_router(endpoint.router, prefix="/api/v1/system/full-data-backup")

    @app.get("/unrelated-validation")
    def unrelated_validation(required_value: int) -> dict:
        return {"required_value": required_value}

    add_error_handlers(app)
    app.dependency_overrides[endpoint.get_full_data_backup_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


def test_export_downloads_canonical_document_with_stable_filename() -> None:
    """A changed canonical serialization or download header must fail this test."""
    document = _backup_document()
    response = _client(_BackupServiceStub(document)).get("/api/v1/system/full-data-backup/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["content-disposition"] == (
        'attachment; filename="pp02-full-data-backup-20260804T123456Z.json"'
    )
    assert response.content == (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def test_preview_returns_manifest_counts_warnings_and_token() -> None:
    """Dropping any user-facing preview guardrail must fail this test."""
    document = _backup_document()
    response = _client(_BackupServiceStub(document)).post(
        "/api/v1/system/full-data-backup/preview",
        json=document,
    )

    assert response.status_code == 200
    assert response.json() == {
        "manifest": document["manifest"],
        "warnings": [],
        "preview_token": "preview-token-123",
        "incoming_digest": "a" * 64,
        "destination_digest": "b" * 64,
        "issued_at": "2026-08-04T12:34:56+00:00",
        "expires_at": "2026-08-04T12:39:56+00:00",
        "incoming_table_row_counts": {"analysis_history": 1},
        "destination_table_row_counts": {"analysis_history": 3},
        "restart_required": True,
    }


def test_restore_returns_recovery_metadata_digests_and_restart_requirement() -> None:
    """Exposing recovery paths or omitting restore evidence must fail this test."""
    document = _backup_document()
    response = _client(_BackupServiceStub(document)).post(
        "/api/v1/system/full-data-backup/restore",
        json={"backup": document, "preview_token": "preview-token-123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["incoming_digest"] == "a" * 64
    assert payload["destination_digest_before"] == "b" * 64
    assert payload["destination_digest_after"] == "c" * 64
    assert payload["restored_table_row_counts"] == {"analysis_history": 1}
    assert payload["recovery"] == {
        "filename": "pp02-full-data-recovery-20260804T123456Z.json",
        "digest": "d" * 64,
        "destination_digest": "b" * 64,
    }
    assert payload["restart_required"] is True
    assert payload["warnings"] == []
    assert "/private/recovery" not in response.text


def test_restore_returns_truthful_committed_warning_in_success_response() -> None:
    document = _backup_document()
    service = _BackupServiceStub(document)
    service.restore_warnings = [
        "Configuration receipt finalization failed after committed restore."
    ]

    response = _client(service).post(
        "/api/v1/system/full-data-backup/restore",
        json={"backup": document, "preview_token": "preview-token-123"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["warnings"] == service.restore_warnings


def test_validation_and_conflict_errors_are_stable_and_do_not_echo_backup_content() -> None:
    """A route that leaks service errors or maps stale restores incorrectly must fail."""
    document = _backup_document()
    secret_marker = "payload-secret-marker"
    document["data"]["configuration"]["values"] = {"SAFE_KEY": secret_marker}

    validation_service = _BackupServiceStub(document)
    validation_service.preview_error = FullDataBackupValidationError(secret_marker)
    validation_response = _client(validation_service).post(
        "/api/v1/system/full-data-backup/preview", json=document
    )
    assert validation_response.status_code == 400
    assert validation_response.json() == {
        "error": "full_data_backup_validation_failed",
        "message": "Full-data backup validation failed",
    }
    assert secret_marker not in validation_response.text

    conflict_service = _BackupServiceStub(document)
    conflict_service.restore_error = FullDataBackupConflictError(secret_marker)
    conflict_response = _client(conflict_service).post(
        "/api/v1/system/full-data-backup/restore",
        json={"backup": document, "preview_token": "preview-token-123"},
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "error": "full_data_backup_conflict",
        "message": "Full-data backup restore conflict",
    }
    assert secret_marker not in conflict_response.text


def test_unexpected_error_is_generic_and_does_not_echo_filesystem_or_payload_content() -> None:
    """A generic failure response must remain safe even when export fails noisily."""
    service = _BackupServiceStub(_backup_document())
    service.export_error = RuntimeError("/private/config.json payload-secret-marker")

    response = _client(service).get("/api/v1/system/full-data-backup/export")

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "message": "Full-data backup operation failed",
    }
    assert "/private/config.json" not in response.text
    assert "payload-secret-marker" not in response.text


def test_process_interruptions_are_not_converted_to_http_errors() -> None:
    """Catching BaseException would hide a required process interruption."""
    service = _BackupServiceStub(_backup_document())
    service.export_error = KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        _client(service).get("/api/v1/system/full-data-backup/export")


def test_backup_request_validation_is_sanitized_before_the_endpoint_runs() -> None:
    """A global validation handler leaking invalid backup input must fail this test."""
    secret_marker = "payload-secret-marker"
    private_path = "/private/payload.json"
    document = _backup_document()
    malformed_json = '{"format":"pp02.full-data.backup","marker":"' + secret_marker
    invalid_document = copy.deepcopy(document)
    invalid_document["format_version"] = 2
    missing_field_document = copy.deepcopy(document)
    del missing_field_document["integrity"]
    extra_field_document = copy.deepcopy(document)
    extra_field_document["unexpected"] = private_path
    restore_extra_field = {
        "backup": document,
        "preview_token": "preview-token-123",
        "unexpected": secret_marker,
    }

    client = _client(_BackupServiceStub(document))
    responses = [
        client.post(
            "/api/v1/system/full-data-backup/preview",
            content=malformed_json,
            headers={"content-type": "application/json"},
        ),
        client.post("/api/v1/system/full-data-backup/preview", json=invalid_document),
        client.post("/api/v1/system/full-data-backup/preview", json=missing_field_document),
        client.post("/api/v1/system/full-data-backup/preview", json=extra_field_document),
        client.post("/api/v1/system/full-data-backup/restore", json=restore_extra_field),
    ]

    for response in responses:
        assert response.status_code == 400
        assert response.json() == {
            "error": "full_data_backup_validation_failed",
            "message": "Full-data backup validation failed",
        }
        assert secret_marker not in response.text
        assert private_path not in response.text
        assert "errors" not in response.text
        assert "input" not in response.text


def test_unrelated_request_validation_remains_422() -> None:
    """The full-backup exception branch must not alter unrelated route validation."""
    client = _client(_BackupServiceStub(_backup_document()))
    response = client.get("/unrelated-validation")

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"

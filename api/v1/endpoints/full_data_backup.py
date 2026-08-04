"""Formal HTTP transport for PP02 complete non-secret data backups."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import get_database_manager, get_system_config_service
from api.v1.schemas.common import ErrorResponse
from api.v1.schemas.full_data_backup import (
    FullDataBackupDocument,
    FullDataBackupPreviewResponse,
    FullDataBackupRestoreRequest,
    FullDataBackupRestoreResponse,
)
from src.services.system_config_service import SystemConfigService
from src.storage import DatabaseManager


logger = logging.getLogger(__name__)
router = APIRouter()


def get_full_data_backup_service(
    db_manager: DatabaseManager = Depends(get_database_manager),
    config_service: SystemConfigService = Depends(get_system_config_service),
) -> Any:
    """Build the backup service from the standard application dependencies."""
    # This stays local because the service imports an API schema. Importing it
    # while api.v1 is assembling its router would otherwise create a cycle.
    from src.services.full_data_backup_service import FullDataBackupService

    return FullDataBackupService(
        db_manager=db_manager,
        config_service=config_service,
    )


def _full_data_backup_errors() -> tuple[type[Exception], type[Exception]]:
    """Load service-owned exception classes after the API router is assembled."""
    from src.services.full_data_backup_service import (
        FullDataBackupConflictError,
        FullDataBackupValidationError,
    )

    return FullDataBackupValidationError, FullDataBackupConflictError


def _validation_error() -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "error": "full_data_backup_validation_failed",
            "message": "Full-data backup validation failed",
        },
    )


def _conflict_error() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "error": "full_data_backup_conflict",
            "message": "Full-data backup restore conflict",
        },
    )


def _internal_error() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={
            "error": "internal_error",
            "message": "Full-data backup operation failed",
        },
    )


def _export_filename(backup: dict) -> str:
    created_at = str(backup["metadata"]["created_at"])
    parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    timestamp = parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"pp02-full-data-backup-{timestamp}.json"


@router.get(
    "/export",
    response_model=FullDataBackupDocument,
    responses={500: {"model": ErrorResponse}},
    summary="Download a canonical PP02 full-data backup",
)
def export_full_data_backup(
    service: Any = Depends(get_full_data_backup_service),
) -> Response:
    """Serialize the service-owned backup document canonically for download."""
    try:
        backup = service.export_backup()
        canonical_document = json.dumps(
            backup,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ) + "\n"
        return Response(
            content=canonical_document,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{_export_filename(backup)}"'
            },
        )
    except Exception:
        logger.error("Full-data backup export failed")
        raise _internal_error()


@router.post(
    "/preview",
    response_model=FullDataBackupPreviewResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Validate a full-data backup and issue a restore preview token",
)
def preview_full_data_backup(
    request: FullDataBackupDocument,
    service: Any = Depends(get_full_data_backup_service),
) -> FullDataBackupPreviewResponse:
    """Delegate validation and token issuance entirely to the backup service."""
    try:
        preview = service.preview_restore(request.model_dump())
        return FullDataBackupPreviewResponse(
            manifest=request.manifest,
            warnings=[],
            **preview,
        )
    except _full_data_backup_errors()[0]:
        raise _validation_error()
    except Exception:
        logger.error("Full-data backup preview failed")
        raise _internal_error()


@router.post(
    "/restore",
    response_model=FullDataBackupRestoreResponse,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Restore a full-data backup validated by a fresh preview token",
)
def restore_full_data_backup(
    request: FullDataBackupRestoreRequest,
    service: Any = Depends(get_full_data_backup_service),
) -> FullDataBackupRestoreResponse:
    """Delegate transactional restore and return only safe recovery metadata."""
    try:
        restored = service.restore_backup(
            request.backup.model_dump(),
            preview_token=request.preview_token,
        )
        recovery = restored["recovery"]
        return FullDataBackupRestoreResponse(
            success=restored["success"],
            warnings=restored.get("warnings", []),
            incoming_digest=restored["incoming_digest"],
            destination_digest_before=restored["destination_digest_before"],
            destination_digest_after=restored["destination_digest_after"],
            restored_table_row_counts=restored["restored_table_row_counts"],
            recovery_filename=restored["recovery_filename"],
            recovery={
                "filename": recovery["filename"],
                "digest": recovery["digest"],
                "destination_digest": recovery["destination_digest"],
            },
            restart_required=restored["restart_required"],
        )
    except _full_data_backup_errors()[0]:
        raise _validation_error()
    except _full_data_backup_errors()[1]:
        raise _conflict_error()
    except Exception:
        logger.error("Full-data backup restore failed")
        raise _internal_error()

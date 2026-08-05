"""Transport schemas for the versioned PP02 complete data backup document."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class FullDataBackupIntegrity(BaseModel):
    """The checksum envelope; its value excludes only itself from the digest."""

    model_config = ConfigDict(extra="forbid")

    algorithm: Literal["sha256"]
    value: str


class FullDataBackupDocument(BaseModel):
    """Strict root shape; service-level validation owns the closed allow-list."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["pp02.full-data.backup"]
    format_version: Literal[1]
    metadata: Dict[str, Any]
    manifest: Dict[str, Any]
    data: Dict[str, Any]
    integrity: FullDataBackupIntegrity


class FullDataBackupPreviewResponse(BaseModel):
    """Safe, user-facing restore preview emitted after service validation."""

    manifest: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    preview_token: str
    incoming_digest: str
    destination_digest: str
    issued_at: str
    expires_at: str
    incoming_table_row_counts: Dict[str, int]
    destination_table_row_counts: Dict[str, int]
    restart_required: bool


class FullDataBackupRestoreRequest(BaseModel):
    """A validated backup plus its short-lived restore preview token."""

    model_config = ConfigDict(extra="forbid")

    backup: FullDataBackupDocument
    preview_token: str


class FullDataBackupRecoveryResponse(BaseModel):
    """Recovery evidence intentionally excludes the local recovery path."""

    filename: str
    digest: str
    destination_digest: str


class FullDataBackupRestoreResponse(BaseModel):
    """Evidence returned after an atomic restore completes."""

    success: bool
    warnings: List[str] = Field(default_factory=list)
    incoming_digest: str
    destination_digest_before: str
    destination_digest_after: str
    restored_table_row_counts: Dict[str, int]
    recovery_filename: str
    recovery: FullDataBackupRecoveryResponse
    restart_required: bool

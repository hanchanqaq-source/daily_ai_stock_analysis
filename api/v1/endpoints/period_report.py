# -*- coding: utf-8 -*-
"""Explicit application-only generation endpoint for R3.5 period reports."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.v1.schemas.period_report import (
    PeriodReportGenerateRequest,
    PeriodReportResponse,
)
from src.services.period_report_service import PeriodReportService
from src.storage import DatabaseManager


logger = logging.getLogger(__name__)
router = APIRouter()


def get_database_manager() -> DatabaseManager:
    """Return the existing formal database manager without loading unrelated services."""
    return DatabaseManager.get_instance()


@router.post(
    "/generate",
    response_model=PeriodReportResponse,
    summary="手动生成周期报告",
    description=(
        "只聚合已经保存的正式分析与市场复盘历史。"
        "下周展望不会调用模型，并在现有分析历史中保存可追溯快照。"
    ),
)
def generate_period_report(
    request: PeriodReportGenerateRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PeriodReportResponse:
    try:
        payload = PeriodReportService(db_manager=db_manager).generate(request.period)
        return PeriodReportResponse.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_period", "message": str(exc)},
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("生成周期报告失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "period_report_failed", "message": "生成周期报告失败"},
        ) from exc


@router.get(
    "/latest",
    response_model=PeriodReportResponse,
    summary="读取最新已保存周期报告",
)
def get_latest_period_report(
    period: str,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PeriodReportResponse:
    try:
        payload = PeriodReportService(db_manager=db_manager).get_latest(period)
        if payload is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "period_report_not_found", "message": "未找到已保存的周期报告"},
            )
        return PeriodReportResponse.model_validate(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_period", "message": str(exc)},
        ) from exc


@router.get(
    "/{report_id}",
    response_model=PeriodReportResponse,
    summary="读取已保存周期报告",
)
def get_period_report(
    report_id: int,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> PeriodReportResponse:
    payload = PeriodReportService(db_manager=db_manager).get_report(report_id)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "period_report_not_found", "message": "未找到已保存的周期报告"},
        )
    return PeriodReportResponse.model_validate(payload)

# -*- coding: utf-8 -*-
"""Database access for canonical persisted period reports."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import desc, select

from src.storage import DatabaseManager, PeriodReportRecord


class PeriodReportRepository:
    """Persist one canonical report for each fixed period window identity."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db = db_manager or DatabaseManager.get_instance()

    def upsert_report(
        self,
        *,
        period: str,
        report_kind: str,
        start_date: date,
        end_date: date,
        content: Dict[str, Any],
        source_history_ids: Iterable[int],
        status: str,
        generated_at: datetime,
    ) -> PeriodReportRecord:
        """Replace canonical content in-place when the period identity already exists."""
        source_ids_json = json.dumps(sorted({int(value) for value in source_history_ids}))
        with self.db.get_session() as session:
            row = session.execute(
                select(PeriodReportRecord).where(
                    PeriodReportRecord.period == period,
                    PeriodReportRecord.report_kind == report_kind,
                    PeriodReportRecord.start_date == start_date,
                    PeriodReportRecord.end_date == end_date,
                )
            ).scalar_one_or_none()
            if row is None:
                row = PeriodReportRecord(
                    period=period,
                    report_kind=report_kind,
                    start_date=start_date,
                    end_date=end_date,
                    content_json="{}",
                    source_record_ids_json=source_ids_json,
                    status=status,
                    generated_at=generated_at,
                )
                session.add(row)
                session.flush()
            else:
                row.source_record_ids_json = source_ids_json
                row.status = status
                row.generated_at = generated_at
            stored_content = dict(content)
            stored_content["report_id"] = int(row.id)
            stored_content["status"] = status
            row.content_json = json.dumps(
                stored_content,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            session.commit()
            session.refresh(row)
            return row

    def get_report(self, report_id: int) -> Optional[PeriodReportRecord]:
        with self.db.get_session() as session:
            return session.get(PeriodReportRecord, report_id)

    def get_latest(self, period: str) -> Optional[PeriodReportRecord]:
        with self.db.get_session() as session:
            return session.execute(
                select(PeriodReportRecord)
                .where(PeriodReportRecord.period == period)
                .order_by(desc(PeriodReportRecord.generated_at), desc(PeriodReportRecord.id))
                .limit(1)
            ).scalar_one_or_none()

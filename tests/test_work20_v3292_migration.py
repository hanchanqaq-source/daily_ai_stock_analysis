# -*- coding: utf-8 -*-
"""Synthetic v3.29.2 database migration contract for Work20."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import select

from src.config import Config
from src.storage import (
    AnalysisHistory,
    DatabaseManager,
    DatabaseSchemaMigration,
    PERIOD_REPORT_SCHEMA_VERSION,
    PeriodReportRecord,
)


class Work20V3292MigrationTestCase(unittest.TestCase):
    def _create_v3292_fixture(self, db_path: str) -> None:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """CREATE TABLE analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id VARCHAR(64),
                code VARCHAR(10) NOT NULL,
                name VARCHAR(50),
                report_type VARCHAR(16),
                sentiment_score INTEGER,
                operation_advice VARCHAR(20),
                trend_prediction VARCHAR(50),
                analysis_summary TEXT,
                raw_result TEXT,
                news_content TEXT,
                context_snapshot TEXT,
                ideal_buy FLOAT,
                secondary_buy FLOAT,
                stop_loss FLOAT,
                take_profit FLOAT,
                created_at DATETIME
            )"""
            )
            conn.executemany(
                """INSERT INTO analysis_history (
                id, query_id, code, name, report_type, analysis_summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        4101,
                        "work20-stock-query",
                        "600519",
                        "Synthetic Stock",
                        "detailed",
                        "synthetic stock history",
                        "2026-08-04 09:00:00",
                    ),
                    (
                        4201,
                        "work20-market-query",
                        "MARKET",
                        "Synthetic Market",
                        "market_review",
                        "synthetic market history",
                        "2026-08-04 10:00:00",
                    ),
                ],
            )

    def test_startup_adds_period_reports_without_changing_v3292_history_rows(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "v3292.sqlite")

        try:
            self._create_v3292_fixture(db_path)
            with sqlite3.connect(db_path) as conn:
                self.assertIsNone(
                    conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='period_reports'"
                    ).fetchone()
                )

            DatabaseManager.reset_instance()
            db = DatabaseManager(db_url=f"sqlite:///{db_path}")

            with db.get_session() as session:
                history_rows = session.execute(
                    select(AnalysisHistory.id, AnalysisHistory.query_id, AnalysisHistory.analysis_summary)
                    .where(AnalysisHistory.id.in_([4101, 4201]))
                    .order_by(AnalysisHistory.id)
                ).all()
                marker = session.get(DatabaseSchemaMigration, PERIOD_REPORT_SCHEMA_VERSION)
                report_count = session.query(PeriodReportRecord).count()

            self.assertEqual(
                history_rows,
                [
                    (4101, "work20-stock-query", "synthetic stock history"),
                    (4201, "work20-market-query", "synthetic market history"),
                ],
            )
            self.assertIsNotNone(marker)
            self.assertEqual(marker.version, PERIOD_REPORT_SCHEMA_VERSION)
            self.assertEqual(report_count, 0)

            with sqlite3.connect(db_path) as conn:
                table = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='period_reports'"
                ).fetchone()
                indexes = conn.execute("PRAGMA index_list(period_reports)").fetchall()

            self.assertEqual(table, ("period_reports",))
            self.assertTrue(any(int(index[2]) == 1 for index in indexes))
        finally:
            DatabaseManager.reset_instance()
            Config.reset_instance()
            temp_dir.cleanup()

    def test_failed_period_report_verification_rolls_back_schema_and_marker(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "v3292-verification-failure.sqlite")

        try:
            self._create_v3292_fixture(db_path)
            DatabaseManager.reset_instance()
            with patch.object(
                DatabaseManager,
                "_verify_period_report_schema",
                side_effect=RuntimeError("injected period report verification failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected period report verification failure"):
                    DatabaseManager(db_url=f"sqlite:///{db_path}")

            with sqlite3.connect(db_path) as conn:
                period_reports_table = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='period_reports'"
                ).fetchone()
                schema_migrations_table = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                ).fetchone()
                history_rows = conn.execute(
                    "SELECT id, query_id FROM analysis_history ORDER BY id"
                ).fetchall()

            self.assertIsNone(period_reports_table)
            self.assertIsNone(schema_migrations_table)
            self.assertEqual(
                history_rows,
                [(4101, "work20-stock-query"), (4201, "work20-market-query")],
            )
        finally:
            DatabaseManager.reset_instance()
            Config.reset_instance()
            temp_dir.cleanup()

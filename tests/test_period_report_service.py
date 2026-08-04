# -*- coding: utf-8 -*-
"""R3.5 behavior tests for manual period reports and next-week outlooks."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from src.services.history_service import HistoryService
from src.storage import AnalysisHistory, DatabaseManager, PeriodReportRecord

try:
    from src.services.period_report_service import (
        INSUFFICIENT_OUTLOOK_MESSAGE,
        OUTLOOK_DISCLAIMER,
        PERIOD_OUTLOOK_REPORT_TYPE,
        PeriodReportService,
    )
except ModuleNotFoundError:
    PeriodReportService = None  # type: ignore[assignment,misc]
    INSUFFICIENT_OUTLOOK_MESSAGE = "近期有效数据不足，暂不能形成下周展望。"
    OUTLOOK_DISCLAIMER = "下周展望基于已有历史分析形成，仅供参考，不代表确定结果。"
    PERIOD_OUTLOOK_REPORT_TYPE = "period_outlook"


def _item(
    record_id: int,
    code: str,
    *,
    created_at: datetime,
    name: str | None = None,
    report_type: str = "detailed",
    trend: str = "看多",
    advice: str = "持有",
    action: str | None = "hold",
    sentiment: int = 65,
    summary: str = "趋势保持稳定",
    region: str | None = None,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "query_id": f"query-{record_id}",
        "stock_code": code,
        "stock_name": name or f"标的{code}",
        "report_type": report_type,
        "region": region,
        "trend_prediction": trend,
        "analysis_summary": summary,
        "sentiment_score": sentiment,
        "operation_advice": advice,
        "action": action,
        "action_label": advice,
        "model_used": "fixture-model",
        "created_at": created_at.astimezone().isoformat(),
        "market_phase_summary": None,
        "current_price": None,
        "change_pct": None,
        "volume_ratio": None,
        "turnover_rate": None,
    }


class _FakeHistoryService:
    def __init__(
        self,
        items: list[dict[str, Any]],
        details: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self.items = items
        self.details = details or {}
        self.calls: list[dict[str, Any]] = []

    def get_history_list(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(dict(kwargs))
        start = date.fromisoformat(kwargs["start_date"]) if kwargs.get("start_date") else None
        end = date.fromisoformat(kwargs["end_date"]) if kwargs.get("end_date") else None
        report_type = kwargs.get("report_type")

        filtered = []
        for item in self.items:
            created = datetime.fromisoformat(item["created_at"]).date()
            if start and created < start:
                continue
            if end and created > end:
                continue
            if report_type and item["report_type"] != report_type:
                continue
            filtered.append(item)
        return {"total": len(filtered), "items": filtered}

    def get_history_detail_by_id(self, record_id: int) -> dict[str, Any] | None:
        return self.details.get(record_id)


class PeriodWindowTestCase(unittest.TestCase):
    def _service(self) -> Any:
        self.assertIsNotNone(
            PeriodReportService,
            "R3.5 requires src.services.period_report_service.PeriodReportService",
        )
        return PeriodReportService(history_service=_FakeHistoryService([]))

    def test_all_period_windows_are_calendar_correct_across_new_year(self) -> None:
        service = self._service()
        as_of = date(2026, 1, 1)

        expected = {
            "week_to_date": (date(2025, 12, 29), date(2026, 1, 1)),
            "previous_week": (date(2025, 12, 22), date(2025, 12, 28)),
            "next_week": (date(2026, 1, 5), date(2026, 1, 11)),
            "weeks_5": (date(2025, 12, 1), date(2026, 1, 1)),
            "weeks_10": (date(2025, 10, 27), date(2026, 1, 1)),
            "month_1": (date(2025, 12, 2), date(2026, 1, 1)),
            "months_2": (date(2025, 11, 2), date(2026, 1, 1)),
        }

        for period, (expected_start, expected_end) in expected.items():
            with self.subTest(period=period):
                window = service.resolve_window(period, as_of)
                self.assertEqual(window.start_date, expected_start)
                self.assertEqual(window.end_date, expected_end)

    def test_month_window_clamps_to_real_month_end(self) -> None:
        service = self._service()

        one_month = service.resolve_window("month_1", date(2026, 3, 31))
        two_months = service.resolve_window("months_2", date(2026, 3, 31))

        self.assertEqual(one_month.start_date, date(2026, 3, 1))
        self.assertEqual(two_months.start_date, date(2026, 2, 1))

    def test_unknown_period_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported period"):
            self._service().resolve_window("quarter", date(2026, 7, 30))


class PeriodAggregationTestCase(unittest.TestCase):
    def _service(
        self,
        items: list[dict[str, Any]],
        details: dict[int, dict[str, Any]] | None = None,
    ) -> tuple[Any, _FakeHistoryService]:
        self.assertIsNotNone(PeriodReportService)
        history = _FakeHistoryService(items, details)
        return PeriodReportService(history_service=history), history

    def test_historical_report_separates_stock_etf_and_market_review(self) -> None:
        created = datetime(2026, 7, 29, 12, 0).astimezone()
        items = [
            _item(1, "600519", created_at=created, name="贵州茅台", trend="看多"),
            _item(2, "512880", created_at=created, name="证券ETF", trend="中性"),
            _item(
                3,
                "MARKET",
                created_at=created,
                name="大盘复盘",
                report_type="market_review",
                trend="大盘复盘",
                action=None,
                region="cn",
            ),
            _item(
                4,
                "PERIOD",
                created_at=created,
                report_type=PERIOD_OUTLOOK_REPORT_TYPE,
            ),
            _item(5, "000001", created_at=created, report_type="alphasift_screen"),
        ]
        service, history = self._service(items)

        report = service.generate("week_to_date", as_of=date(2026, 7, 30))

        self.assertEqual([row["stock_code"] for row in report["stock_summaries"]], ["600519"])
        self.assertEqual([row["stock_code"] for row in report["etf_summaries"]], ["512880"])
        self.assertEqual([row["record_id"] for row in report["market_reviews"]], [3])
        self.assertEqual(report["source_record_count"], 3)
        self.assertEqual(len(history.calls), 1)
        self.assertEqual(history.calls[0]["start_date"], "2026-07-27")
        self.assertEqual(history.calls[0]["end_date"], "2026-07-30")
        self.assertEqual(history.calls[0]["page"], 1)

    def test_historical_summary_groups_records_and_counts_directions(self) -> None:
        items = [
            _item(1, "AAPL", created_at=datetime(2026, 7, 30, 9, 0).astimezone(), trend="看多"),
            _item(2, "AAPL", created_at=datetime(2026, 7, 29, 9, 0).astimezone(), trend="看空"),
            _item(3, "AAPL", created_at=datetime(2026, 7, 28, 9, 0).astimezone(), trend="震荡"),
        ]
        service, _ = self._service(items)

        report = service.generate("week_to_date", as_of=date(2026, 7, 30))

        summary = report["stock_summaries"][0]
        self.assertEqual(summary["record_count"], 3)
        self.assertEqual(summary["latest_record_id"], 1)
        self.assertEqual(
            summary["direction_counts"],
            {"bullish": 1, "neutral": 1, "bearish": 1, "unknown": 0},
        )
        self.assertEqual(summary["source_record_ids"], [1, 2, 3])


class NextWeekOutlookTestCase(unittest.TestCase):
    def _service(
        self,
        items: list[dict[str, Any]],
        details: dict[int, dict[str, Any]] | None = None,
        db_manager: Any = None,
    ) -> Any:
        self.assertIsNotNone(PeriodReportService)
        return PeriodReportService(
            history_service=_FakeHistoryService(items, details),
            db_manager=db_manager,
        )

    def test_outlook_uses_recent_14_calendar_days_and_rejects_stale_records(self) -> None:
        as_of = date(2026, 7, 30)
        accepted = _item(
            1,
            "600519",
            created_at=datetime(2026, 7, 17, 9, 0).astimezone(),
            trend="看多",
        )
        stale = _item(
            2,
            "000001",
            created_at=datetime(2026, 7, 16, 9, 0).astimezone(),
            trend="看空",
        )

        report = self._service([accepted, stale]).generate("next_week", as_of=as_of)

        self.assertEqual([row["stock_code"] for row in report["outlook"]["stocks"]], ["600519"])
        self.assertEqual(report["outlook"]["source_record_ids"], [1])
        self.assertEqual(report["outlook"]["data_as_of"], accepted["created_at"])

    def test_outlook_maps_direction_confidence_evidence_risk_and_invalidation(self) -> None:
        created = datetime(2026, 7, 30, 9, 0).astimezone()
        items = [
            _item(
                11,
                "600519",
                created_at=created,
                name="贵州茅台",
                trend="强烈看多",
                advice="加仓",
                action="add",
                sentiment=82,
                summary="趋势和策略同向",
            ),
            _item(
                12,
                "512880",
                created_at=created - timedelta(hours=1),
                name="证券ETF",
                trend="震荡",
                advice="观望",
                action="watch",
                sentiment=50,
            ),
            _item(
                13,
                "AAPL",
                created_at=created - timedelta(hours=2),
                name="Apple",
                trend="看空",
                advice="减仓",
                action="reduce",
                sentiment=28,
            ),
        ]
        details = {
            11: {
                "id": 11,
                "ideal_buy": 145.0,
                "stop_loss": 138.0,
                "take_profit": 168.0,
                "raw_result": {
                    "confidence_level": "高",
                    "risk_warning": "需求走弱与大盘回撤风险",
                    "dashboard": {
                        "strategy_synthesis": {
                            "final_signal": "buy",
                            "summary": "多策略形成一致支持",
                        }
                    },
                },
            },
            12: {
                "id": 12,
                "raw_result": {"confidence_level": "中"},
                "ideal_buy": 1.02,
                "take_profit": 1.12,
            },
            13: {
                "id": 13,
                "raw_result": {
                    "confidence_level": "low",
                    "risk_warning": "业绩与估值波动",
                },
                "take_profit": 225.0,
            },
        }

        report = self._service(items, details).generate("next_week", as_of=date(2026, 7, 30))

        stock_rows = {row["stock_code"]: row for row in report["outlook"]["stocks"]}
        etf_rows = {row["stock_code"]: row for row in report["outlook"]["etfs"]}
        self.assertEqual(stock_rows["600519"]["tendency"], "看多")
        self.assertEqual(stock_rows["600519"]["confidence"], "高")
        self.assertIn("趋势：强烈看多", stock_rows["600519"]["historical_signals"])
        self.assertIn("策略信号：buy", stock_rows["600519"]["historical_signals"])
        self.assertEqual(stock_rows["600519"]["risks"], ["需求走弱与大盘回撤风险"])
        self.assertIn("138", " ".join(stock_rows["600519"]["invalidation_conditions"]))
        self.assertEqual(etf_rows["512880"]["tendency"], "中性")
        self.assertEqual(stock_rows["AAPL"]["tendency"], "看空")
        self.assertEqual(stock_rows["AAPL"]["confidence"], "低")
        self.assertIn("225", " ".join(stock_rows["AAPL"]["invalidation_conditions"]))
        self.assertEqual(report["disclaimer"], OUTLOOK_DISCLAIMER)

    def test_outlook_does_not_invent_direction_when_records_are_not_qualified(self) -> None:
        item = _item(
            1,
            "600519",
            created_at=datetime(2026, 7, 30, 9, 0).astimezone(),
            trend="暂无结论",
            advice="",
            action=None,
            sentiment=50,
        )

        report = self._service([item]).generate("next_week", as_of=date(2026, 7, 30))

        self.assertEqual(report["outlook"]["status"], "insufficient_data")
        self.assertEqual(report["outlook"]["message"], INSUFFICIENT_OUTLOOK_MESSAGE)
        self.assertEqual(report["outlook"]["stocks"], [])
        self.assertEqual(report["outlook"]["etfs"], [])
        self.assertEqual(report["outlook"]["source_record_count"], 0)


class PeriodOutlookPersistenceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(PeriodReportService)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.env_path = self.data_dir / ".env"
        self.db_path = self.data_dir / "period-report.db"
        self.env_path.write_text(
            "\n".join(
                [
                    "STOCK_LIST=600519,512880",
                    "ADMIN_AUTH_ENABLED=false",
                    f"DATABASE_PATH={self.db_path}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        os.environ["ENV_FILE"] = str(self.env_path)
        os.environ["DATABASE_PATH"] = str(self.db_path)
        DatabaseManager.reset_instance()
        storage_config = SimpleNamespace(
            sqlite_wal_enabled=True,
            sqlite_busy_timeout_ms=5000,
            sqlite_write_retry_max=2,
            sqlite_write_retry_base_delay=0.01,
        )
        with patch("src.storage.get_config", return_value=storage_config):
            self.db = DatabaseManager(db_url=f"sqlite:///{self.db_path}")

    def tearDown(self) -> None:
        DatabaseManager.reset_instance()
        os.environ.pop("ENV_FILE", None)
        os.environ.pop("DATABASE_PATH", None)
        self.temp_dir.cleanup()

    def _seed_analysis(
        self,
        *,
        record_id: int,
        code: str,
        created_at: datetime,
        trend: str = "看多",
        name: str = "贵州茅台",
    ) -> None:
        with self.db.get_session() as session:
            session.add(
                AnalysisHistory(
                    id=record_id,
                    query_id=f"query-{record_id}",
                    code=code,
                    name=name,
                    report_type="detailed",
                    sentiment_score=70,
                    operation_advice="持有",
                    trend_prediction=trend,
                    analysis_summary="正式历史摘要",
                    raw_result=json.dumps(
                        {
                            "code": code,
                            "name": name,
                            "confidence_level": "中",
                            "risk_warning": "市场波动",
                        },
                        ensure_ascii=False,
                    ),
                    created_at=created_at,
                )
            )
            session.commit()

    @staticmethod
    def _snapshot_payload() -> dict[str, Any]:
        return {
            "snapshot_version": 1,
            "status": "insufficient_data",
            "message": INSUFFICIENT_OUTLOOK_MESSAGE,
            "target_period": {
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
            },
            "generated_at": "2026-07-30T12:00:00",
            "overall_tendency": None,
            "stocks": [],
            "etfs": [],
            "market_signals": [],
            "data_as_of": None,
            "source_record_count": 0,
            "source_record_ids": [],
            "disclaimer": OUTLOOK_DISCLAIMER,
        }

    def test_outlook_snapshot_stays_queryable_but_not_in_official_stock_bar(self) -> None:
        snapshot_id = self.db.save_period_outlook_snapshot(
            query_id="period-outlook-stock-bar",
            snapshot=self._snapshot_payload(),
            created_at=datetime(2026, 7, 30, 7, 0),
        )

        traceable = HistoryService(self.db).get_history_list(
            report_type=PERIOD_OUTLOOK_REPORT_TYPE,
            page=1,
            limit=10,
        )
        stock_bar_records = self.db.get_distinct_stocks_from_history(limit=10)

        self.assertEqual([item["id"] for item in traceable["items"]], [snapshot_id])
        self.assertEqual(stock_bar_records, [])

    def test_outlook_snapshot_is_never_a_backtest_candidate(self) -> None:
        from src.repositories.backtest_repo import BacktestRepository

        snapshot_id = self.db.save_period_outlook_snapshot(
            query_id="period-outlook-backtest",
            snapshot=self._snapshot_payload(),
            created_at=datetime(2024, 1, 1, 7, 0),
        )

        candidates = BacktestRepository(self.db).get_candidates(
            code=None,
            min_age_days=0,
            limit=10,
            eval_window_days=3,
            engine_version="period-report-test",
            force=True,
        )

        self.assertNotIn(snapshot_id, [row.id for row in candidates])

    def test_next_week_saves_traceable_snapshot_in_analysis_history(self) -> None:
        self._seed_analysis(
            record_id=101,
            code="600519",
            created_at=datetime(2026, 7, 30, 9, 0),
        )
        service = PeriodReportService(
            history_service=HistoryService(self.db),
            db_manager=self.db,
            now_provider=lambda: datetime(2026, 7, 30, 12, 0),
        )

        report = service.generate("next_week", as_of=date(2026, 7, 30))

        snapshot_id = report["outlook"]["snapshot_id"]
        self.assertIsInstance(snapshot_id, int)
        with self.db.get_session() as session:
            row = session.get(AnalysisHistory, snapshot_id)
            self.assertIsNotNone(row)
            self.assertEqual(row.report_type, PERIOD_OUTLOOK_REPORT_TYPE)
            self.assertEqual(row.code, "PERIOD")
            payload = json.loads(row.context_snapshot or "{}")
        self.assertEqual(payload["target_period"], {"start_date": "2026-08-03", "end_date": "2026-08-09"})
        self.assertEqual(payload["source_record_ids"], [101])
        self.assertEqual(payload["stocks"][0]["source_record_ids"], [101])

    def test_previous_week_returns_latest_matching_outlook_with_actual_summary(self) -> None:
        self._seed_analysis(
            record_id=201,
            code="600519",
            created_at=datetime(2026, 8, 4, 9, 0),
            trend="看空",
        )
        first_service = PeriodReportService(
            history_service=HistoryService(self.db),
            db_manager=self.db,
            now_provider=lambda: datetime(2026, 7, 30, 12, 0),
        )
        first = first_service.generate("next_week", as_of=date(2026, 7, 30))
        snapshot_id = first["outlook"]["snapshot_id"]

        review_service = PeriodReportService(
            history_service=HistoryService(self.db),
            db_manager=self.db,
            now_provider=lambda: datetime(2026, 8, 10, 12, 0),
        )
        report = review_service.generate("previous_week", as_of=date(2026, 8, 10))

        self.assertEqual(report["start_date"], "2026-08-03")
        self.assertEqual(report["end_date"], "2026-08-09")
        self.assertEqual(report["stock_summaries"][0]["latest_record_id"], 201)
        self.assertEqual(report["matched_outlook"]["snapshot_id"], snapshot_id)
        self.assertEqual(
            report["matched_outlook"]["target_period"],
            {"start_date": "2026-08-03", "end_date": "2026-08-09"},
        )


class CanonicalPeriodReportPersistenceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(PeriodReportService)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "period-report-canonical.db"
        DatabaseManager.reset_instance()
        storage_config = SimpleNamespace(
            sqlite_wal_enabled=True,
            sqlite_busy_timeout_ms=5000,
            sqlite_write_retry_max=2,
            sqlite_write_retry_base_delay=0.01,
        )
        with patch("src.storage.get_config", return_value=storage_config):
            self.db = DatabaseManager(db_url=f"sqlite:///{self.db_path}")

    def tearDown(self) -> None:
        DatabaseManager.reset_instance()
        self.temp_dir.cleanup()

    def _seed_history(self, record_id: int, *, created_at: datetime, code: str = "600519") -> None:
        with self.db.get_session() as session:
            session.add(
                AnalysisHistory(
                    id=record_id,
                    query_id=f"canonical-query-{record_id}",
                    code=code,
                    name=f"Synthetic {code}",
                    report_type="detailed",
                    sentiment_score=70,
                    operation_advice="持有",
                    trend_prediction="看多",
                    analysis_summary=f"synthetic summary {record_id}",
                    raw_result="{}",
                    created_at=created_at,
                )
            )
            session.commit()

    def test_generation_upserts_same_window_and_reloads_exact_content_after_restart(self) -> None:
        self._seed_history(102, created_at=datetime(2026, 7, 29, 9, 0))
        first_service = PeriodReportService(
            history_service=HistoryService(self.db),
            db_manager=self.db,
            now_provider=lambda: datetime(2026, 7, 30, 12, 0),
        )

        first = first_service.generate("week_to_date", as_of=date(2026, 7, 30))
        self.assertGreater(first["report_id"], 0)
        self.assertEqual(first["status"], "ready")

        self._seed_history(101, created_at=datetime(2026, 7, 30, 9, 0))
        replacement = first_service.generate("week_to_date", as_of=date(2026, 7, 30))
        self.assertEqual(replacement["report_id"], first["report_id"])
        self.assertEqual(replacement["source_record_count"], 2)

        with self.db.get_session() as session:
            stored = session.get(PeriodReportRecord, first["report_id"])
            self.assertIsNotNone(stored)
            self.assertEqual(json.loads(stored.source_record_ids_json), [101, 102])

        restarted_db = DatabaseManager(db_url=f"sqlite:///{self.db_path}")
        restarted_service = PeriodReportService(
            history_service=HistoryService(restarted_db),
            db_manager=restarted_db,
        )
        self.assertEqual(restarted_service.get_report(first["report_id"]), replacement)

        different_window = first_service.generate("week_to_date", as_of=date(2026, 7, 31))
        self.assertNotEqual(different_window["report_id"], first["report_id"])

    def test_legacy_outlook_is_read_only_fallback_for_stored_reads(self) -> None:
        legacy_id = 901
        legacy_snapshot = {
            "snapshot_version": 1,
            "status": "insufficient_data",
            "message": INSUFFICIENT_OUTLOOK_MESSAGE,
            "target_period": {"start_date": "2026-08-03", "end_date": "2026-08-09"},
            "generated_at": "2026-07-30T12:00:00",
            "overall_tendency": None,
            "stocks": [],
            "etfs": [],
            "market_signals": [],
            "data_as_of": None,
            "source_record_count": 0,
            "source_record_ids": [],
            "disclaimer": OUTLOOK_DISCLAIMER,
        }
        with self.db.get_session() as session:
            session.add(
                AnalysisHistory(
                    id=legacy_id,
                    query_id="legacy-period-outlook",
                    code="PERIOD",
                    name="Legacy outlook",
                    report_type=PERIOD_OUTLOOK_REPORT_TYPE,
                    context_snapshot=json.dumps(legacy_snapshot, ensure_ascii=False),
                    created_at=datetime(2026, 7, 30, 12, 0),
                )
            )
            session.commit()

        service = PeriodReportService(history_service=HistoryService(self.db), db_manager=self.db)
        latest = service.get_latest("next_week")
        by_id = service.get_report(legacy_id)

        self.assertEqual(latest, by_id)
        self.assertEqual(latest["report_id"], legacy_id)
        self.assertEqual(latest["status"], "insufficient_data")
        self.assertEqual(latest["period"], "next_week")
        self.assertEqual(latest["outlook"]["target_period"], legacy_snapshot["target_period"])
        with self.db.get_session() as session:
            self.assertEqual(session.query(PeriodReportRecord).count(), 0)


if __name__ == "__main__":
    unittest.main()

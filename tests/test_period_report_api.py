# -*- coding: utf-8 -*-
"""R3.5 API contract tests for manual period-report generation."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    from api.v1.schemas.period_report import (
        PeriodReportGenerateRequest,
        PeriodReportResponse,
    )
except (ImportError, ModuleNotFoundError):
    PeriodReportGenerateRequest = None  # type: ignore[assignment,misc]
    PeriodReportResponse = None  # type: ignore[assignment,misc]


def _load_period_report_endpoint():
    path = (
        Path(__file__).resolve().parents[1]
        / "api"
        / "v1"
        / "endpoints"
        / "period_report.py"
    )
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "pp02_period_report_endpoint_under_test",
        path,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    period_report_endpoint = _load_period_report_endpoint()
except (ImportError, ModuleNotFoundError):
    period_report_endpoint = None  # type: ignore[assignment]

if period_report_endpoint is not None:
    PeriodReportGenerateRequest = period_report_endpoint.PeriodReportGenerateRequest
    PeriodReportResponse = period_report_endpoint.PeriodReportResponse


def _historical_payload(period: str = "week_to_date") -> dict:
    return {
        "period": period,
        "report_kind": "historical",
        "start_date": "2026-07-27",
        "end_date": "2026-07-30",
        "generated_at": "2026-07-30T12:00:00+02:00",
        "source_record_count": 3,
        "stock_summaries": [
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "asset_type": "stock",
                "record_count": 1,
                "latest_record_id": 1,
                "latest_created_at": "2026-07-30T09:00:00+02:00",
                "latest_trend": "看多",
                "latest_summary": "趋势稳定",
                "direction_counts": {
                    "bullish": 1,
                    "neutral": 0,
                    "bearish": 0,
                    "unknown": 0,
                },
                "source_record_ids": [1],
            }
        ],
        "etf_summaries": [
            {
                "stock_code": "512880",
                "stock_name": "证券ETF",
                "asset_type": "etf",
                "record_count": 1,
                "latest_record_id": 2,
                "latest_created_at": "2026-07-30T08:00:00+02:00",
                "latest_trend": "中性",
                "latest_summary": "震荡整理",
                "direction_counts": {
                    "bullish": 0,
                    "neutral": 1,
                    "bearish": 0,
                    "unknown": 0,
                },
                "source_record_ids": [2],
            }
        ],
        "market_reviews": [
            {
                "record_id": 3,
                "region": "cn",
                "created_at": "2026-07-30T07:00:00+02:00",
                "summary": "市场复盘",
                "trend_prediction": "大盘复盘",
            }
        ],
        "outlook": None,
        "matched_outlook": None,
        "disclaimer": None,
    }


def _insufficient_outlook_payload() -> dict:
    return {
        "period": "next_week",
        "report_kind": "outlook",
        "start_date": "2026-08-03",
        "end_date": "2026-08-09",
        "generated_at": "2026-07-30T12:00:00+02:00",
        "source_record_count": 0,
        "stock_summaries": [],
        "etf_summaries": [],
        "market_reviews": [],
        "outlook": {
            "snapshot_version": 1,
            "snapshot_id": 44,
            "snapshot_created_at": None,
            "status": "insufficient_data",
            "message": "近期有效数据不足，暂不能形成下周展望。",
            "target_period": {
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
            },
            "generated_at": "2026-07-30T12:00:00+02:00",
            "overall_tendency": None,
            "stocks": [],
            "etfs": [],
            "market_signals": [],
            "data_as_of": None,
            "source_record_count": 0,
            "source_record_ids": [],
            "disclaimer": "下周展望基于已有历史分析形成，仅供参考，不代表确定结果。",
        },
        "matched_outlook": None,
        "disclaimer": "下周展望基于已有历史分析形成，仅供参考，不代表确定结果。",
    }


class PeriodReportSchemaTestCase(unittest.TestCase):
    def test_request_accepts_exactly_the_seven_manual_periods(self) -> None:
        self.assertIsNotNone(PeriodReportGenerateRequest)
        accepted = {
            "week_to_date",
            "previous_week",
            "next_week",
            "weeks_5",
            "weeks_10",
            "month_1",
            "months_2",
        }

        for period in accepted:
            request = PeriodReportGenerateRequest.model_validate({"period": period})
            self.assertEqual(request.period, period)

        with self.assertRaises(Exception):
            PeriodReportGenerateRequest.model_validate({"period": "quarter"})

    def test_response_schema_keeps_asset_and_market_sections_separate(self) -> None:
        self.assertIsNotNone(PeriodReportResponse)

        response = PeriodReportResponse.model_validate(_historical_payload())

        self.assertEqual(response.stock_summaries[0].asset_type, "stock")
        self.assertEqual(response.etf_summaries[0].asset_type, "etf")
        self.assertEqual(response.market_reviews[0].record_id, 3)
        self.assertIsNone(response.outlook)

    def test_response_schema_preserves_insufficient_outlook_contract(self) -> None:
        self.assertIsNotNone(PeriodReportResponse)

        response = PeriodReportResponse.model_validate(_insufficient_outlook_payload())

        self.assertEqual(response.outlook.status, "insufficient_data")
        self.assertEqual(
            response.outlook.message,
            "近期有效数据不足，暂不能形成下周展望。",
        )
        self.assertEqual(response.outlook.source_record_count, 0)


class PeriodReportEndpointTestCase(unittest.TestCase):
    def _client(self, generated_payload: dict) -> tuple[TestClient, MagicMock]:
        self.assertIsNotNone(period_report_endpoint)
        service = MagicMock()
        service.generate.return_value = generated_payload
        app = FastAPI()
        app.include_router(period_report_endpoint.router, prefix="/api/v1/period-report")
        app.dependency_overrides[period_report_endpoint.get_database_manager] = (
            lambda: MagicMock(name="db")
        )
        patcher = patch.object(
            period_report_endpoint,
            "PeriodReportService",
            return_value=service,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return TestClient(app), service

    def test_generate_is_an_explicit_post_and_calls_only_period_service(self) -> None:
        client, service = self._client(_historical_payload())

        response = client.post(
            "/api/v1/period-report/generate",
            json={"period": "week_to_date"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["period"], "week_to_date")
        service.generate.assert_called_once_with("week_to_date")

    def test_invalid_period_is_rejected_before_service_execution(self) -> None:
        client, service = self._client(_historical_payload())

        response = client.post(
            "/api/v1/period-report/generate",
            json={"period": "quarter"},
        )

        self.assertEqual(response.status_code, 422)
        service.generate.assert_not_called()

    def test_next_week_returns_fixed_insufficient_message_without_model_fields(self) -> None:
        client, service = self._client(_insufficient_outlook_payload())

        response = client.post(
            "/api/v1/period-report/generate",
            json={"period": "next_week"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body["outlook"]["message"],
            "近期有效数据不足，暂不能形成下周展望。",
        )
        self.assertNotIn("model", body["outlook"])
        service.generate.assert_called_once_with("next_week")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Regression contract for API stock-analysis history completion."""

from __future__ import annotations

import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.services.analysis_service import AnalysisService
from src.services.run_diagnostics import record_history_run


def _successful_analysis_result() -> SimpleNamespace:
    result = SimpleNamespace(
        success=True,
        code="600519",
        name="贵州茅台",
        current_price=100.0,
        change_pct=1.0,
        model_used="codex-cli",
        analysis_summary="summary",
        operation_advice="持有",
        action=None,
        guardrail_reason=None,
        trend_prediction="震荡",
        sentiment_score=60,
        report_language="zh",
        news_summary="news",
        technical_analysis="technical",
        fundamental_analysis="fundamental",
        risk_warning="risk",
        diagnostic_context_snapshot=None,
        get_sniper_points=lambda: {},
    )
    result.to_dict = lambda: {
        "code": result.code,
        "name": result.name,
        "success": result.success,
        "sentiment_score": result.sentiment_score,
        "operation_advice": result.operation_advice,
        "trend_prediction": result.trend_prediction,
        "analysis_summary": result.analysis_summary,
        "report_language": result.report_language,
    }
    return result


class AnalysisHistoryCompletionContractTestCase(unittest.TestCase):
    def _run_service(self, *, report_saved: bool):
        result = _successful_analysis_result()

        class ControlledPipeline:
            def __init__(self, **_kwargs):
                pass

            def process_single_stock(self, **_kwargs):
                record_history_run(
                    report_saved=report_saved,
                    metadata_saved=report_saved,
                    analysis_history_id=7 if report_saved else None,
                )
                return result

        pipeline_module = types.ModuleType("src.core.pipeline")
        pipeline_module.StockAnalysisPipeline = ControlledPipeline
        service = object.__new__(AnalysisService)
        service.last_error = None

        with patch.dict(sys.modules, {"src.core.pipeline": pipeline_module}), patch(
            "src.config.get_config",
            return_value=SimpleNamespace(report_language="zh"),
        ):
            response = AnalysisService.analyze_stock(
                service,
                "600519",
                report_type="detailed",
                query_id="work12-task",
                send_notification=False,
            )

        return response, service.last_error

    def test_explicit_history_save_failure_cannot_complete_stock_analysis(self) -> None:
        response, last_error = self._run_service(report_saved=False)

        self.assertIsNone(response)
        self.assertIn("历史保存失败", last_error or "")

    def test_saved_history_keeps_successful_stock_analysis_response(self) -> None:
        response, last_error = self._run_service(report_saved=True)

        self.assertIsNotNone(response)
        self.assertEqual(response["stock_code"], "600519")
        self.assertEqual(
            response["diagnostic_summary"]["components"]["history"]["status"],
            "ok",
        )
        self.assertIsNone(last_error)


if __name__ == "__main__":
    unittest.main()

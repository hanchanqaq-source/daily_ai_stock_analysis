# -*- coding: utf-8 -*-
"""Deterministic manual period reports built from persisted analysis history."""

from __future__ import annotations

import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

from src.services.history_service import HistoryService
from src.repositories.period_report_repo import PeriodReportRepository
from src.storage import DatabaseManager


PERIOD_OUTLOOK_REPORT_TYPE = "period_outlook"
FORMAL_ANALYSIS_REPORT_TYPES = frozenset({"simple", "detailed", "full"})
SUPPORTED_PERIODS = frozenset(
    {
        "week_to_date",
        "previous_week",
        "next_week",
        "weeks_5",
        "weeks_10",
        "month_1",
        "months_2",
    }
)
INSUFFICIENT_OUTLOOK_MESSAGE = "近期有效数据不足，暂不能形成下周展望。"
OUTLOOK_DISCLAIMER = "下周展望基于已有历史分析形成，仅供参考，不代表确定结果。"
_HISTORY_PAGE_SIZE = 500


@dataclass(frozen=True)
class PeriodWindow:
    """Inclusive calendar window for one period-report entrance."""

    period: str
    start_date: date
    end_date: date


def _parse_created_at(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _serialize_datetime(value: datetime) -> str:
    return value.astimezone().isoformat() if value.tzinfo is None else value.isoformat()


def _subtract_calendar_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    target_year, target_month_index = divmod(month_index, 12)
    target_month = target_month_index + 1
    target_day = min(value.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _normalize_direction(*values: Any) -> Optional[str]:
    text = " ".join(str(value or "").strip().lower() for value in values if value is not None)
    if not text:
        return None

    bullish_tokens = (
        "强烈看多",
        "看多",
        "bullish",
        "strong buy",
        "buy",
        "add",
        "加仓",
        "买入",
    )
    bearish_tokens = (
        "强烈看空",
        "看空",
        "bearish",
        "strong sell",
        "sell",
        "reduce",
        "减仓",
        "卖出",
    )
    neutral_tokens = (
        "震荡",
        "中性",
        "neutral",
        "hold",
        "watch",
        "观望",
        "持有",
    )

    if any(token in text for token in bullish_tokens):
        return "看多"
    if any(token in text for token in bearish_tokens):
        return "看空"
    if any(token in text for token in neutral_tokens):
        return "中性"
    return None


def _direction_bucket(direction: Optional[str]) -> str:
    if direction == "看多":
        return "bullish"
    if direction == "看空":
        return "bearish"
    if direction == "中性":
        return "neutral"
    return "unknown"


def _normalize_confidence(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"高", "high", "强", "strong"}:
        return "高"
    if normalized in {"中", "medium", "moderate", "中等"}:
        return "中"
    return "低"


def _is_etf(item: Dict[str, Any]) -> bool:
    code = str(item.get("stock_code") or "").strip().upper()
    name = str(item.get("stock_name") or "").strip().upper()
    compact = code
    for prefix in ("SH", "SZ"):
        if compact.startswith(prefix):
            compact = compact[len(prefix):]
    compact = compact.split(".", 1)[0]
    if len(compact) == 6 and compact.isdigit() and compact.startswith(
        ("51", "52", "56", "58", "15", "16", "18")
    ):
        return True
    return "ETF" in name or "EXCHANGE TRADED FUND" in name


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _as_number_text(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed.is_integer():
        return str(int(parsed))
    return f"{parsed:g}"


class PeriodReportService:
    """Build manual reports without calling models or external data sources."""

    def __init__(
        self,
        *,
        history_service: Optional[HistoryService] = None,
        db_manager: Optional[DatabaseManager] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
    ) -> None:
        self.db = db_manager
        if history_service is not None:
            self.history = history_service
        else:
            self.db = self.db or DatabaseManager.get_instance()
            self.history = HistoryService(self.db)
        self.period_reports = PeriodReportRepository(self.db) if self.db is not None else None
        self._now_provider = now_provider or datetime.now

    @staticmethod
    def resolve_window(period: str, as_of: date) -> PeriodWindow:
        if period not in SUPPORTED_PERIODS:
            raise ValueError(f"unsupported period: {period}")

        current_monday = as_of - timedelta(days=as_of.weekday())
        if period == "week_to_date":
            return PeriodWindow(period, current_monday, as_of)
        if period == "previous_week":
            return PeriodWindow(
                period,
                current_monday - timedelta(days=7),
                current_monday - timedelta(days=1),
            )
        if period == "next_week":
            return PeriodWindow(
                period,
                current_monday + timedelta(days=7),
                current_monday + timedelta(days=13),
            )
        if period == "weeks_5":
            return PeriodWindow(period, current_monday - timedelta(weeks=4), as_of)
        if period == "weeks_10":
            return PeriodWindow(period, current_monday - timedelta(weeks=9), as_of)
        if period == "month_1":
            return PeriodWindow(
                period,
                _subtract_calendar_months(as_of, 1) + timedelta(days=1),
                as_of,
            )
        return PeriodWindow(
            period,
            _subtract_calendar_months(as_of, 2) + timedelta(days=1),
            as_of,
        )

    def generate(self, period: str, *, as_of: Optional[date] = None) -> Dict[str, Any]:
        resolved_as_of = as_of or self._now_provider().date()
        window = self.resolve_window(period, resolved_as_of)
        generated_at = self._now_provider()

        if period == "next_week":
            report = self._generate_outlook(
                window=window,
                as_of=resolved_as_of,
                generated_at=generated_at,
            )
        else:
            report = self._generate_historical(window=window, generated_at=generated_at)
            if period == "previous_week":
                report["matched_outlook"] = self._find_matching_outlook(window)
            else:
                report["matched_outlook"] = None
        return self._persist_report(report, window=window, generated_at=generated_at)

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Return a stored canonical or legacy outlook report without generating one."""
        if self.period_reports is not None:
            row = self.period_reports.get_report(report_id)
            if row is not None:
                return self._deserialize_report(row)
        return self._legacy_outlook_report_by_id(report_id)

    def get_latest(self, period: str) -> Optional[Dict[str, Any]]:
        """Return the latest stored report for a period without generating one."""
        if period not in SUPPORTED_PERIODS:
            raise ValueError(f"unsupported period: {period}")
        if self.period_reports is not None:
            row = self.period_reports.get_latest(period)
            if row is not None:
                return self._deserialize_report(row)
        if period == "next_week":
            return self._latest_legacy_outlook_report()
        return None

    def _latest_legacy_outlook_report(self) -> Optional[Dict[str, Any]]:
        """Adapt the newest readable legacy outlook without writing canonical data."""
        for item in self._get_history_items(report_type=PERIOD_OUTLOOK_REPORT_TYPE):
            record_id = int(item.get("id") or 0)
            if not record_id:
                continue
            report = self._legacy_outlook_report_by_id(record_id)
            if report is not None:
                return report
        return None

    def _legacy_outlook_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        detail = self.history.get_history_detail_by_id(report_id) or {}
        if detail.get("report_type") != PERIOD_OUTLOOK_REPORT_TYPE:
            return None
        snapshot = detail.get("context_snapshot")
        if not isinstance(snapshot, dict):
            return None
        target = snapshot.get("target_period")
        if not isinstance(target, dict):
            return None
        start_date = target.get("start_date")
        end_date = target.get("end_date")
        generated_at = snapshot.get("generated_at") or detail.get("created_at")
        if not all(isinstance(value, str) and value for value in (start_date, end_date, generated_at)):
            return None

        outlook = dict(snapshot)
        outlook["snapshot_id"] = report_id
        outlook["snapshot_created_at"] = detail.get("created_at")
        status = outlook.get("status")
        if status not in {"ready", "insufficient_data"}:
            status = "ready"
        return {
            "report_id": report_id,
            "status": status,
            "period": "next_week",
            "report_kind": "outlook",
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": generated_at,
            "source_record_count": int(outlook.get("source_record_count") or 0),
            "stock_summaries": [],
            "etf_summaries": [],
            "market_reviews": [],
            "outlook": outlook,
            "matched_outlook": None,
            "disclaimer": outlook.get("disclaimer"),
        }

    def _persist_report(
        self,
        report: Dict[str, Any],
        *,
        window: PeriodWindow,
        generated_at: datetime,
    ) -> Dict[str, Any]:
        if self.period_reports is None:
            return report
        status = str((report.get("outlook") or {}).get("status") or "ready")
        row = self.period_reports.upsert_report(
            period=window.period,
            report_kind=str(report["report_kind"]),
            start_date=window.start_date,
            end_date=window.end_date,
            content=report,
            source_history_ids=self._source_history_ids(report),
            status=status,
            generated_at=generated_at,
        )
        return self._deserialize_report(row)

    @staticmethod
    def _source_history_ids(value: Any) -> List[int]:
        """Collect source history IDs exposed by the complete response payload."""
        source_ids: set[int] = set()

        def visit(item: Any) -> None:
            if isinstance(item, dict):
                for key, nested in item.items():
                    if key == "source_record_ids" and isinstance(nested, list):
                        for record_id in nested:
                            if isinstance(record_id, int) and record_id > 0:
                                source_ids.add(record_id)
                    elif key == "record_id" and isinstance(nested, int) and nested > 0:
                        source_ids.add(nested)
                    else:
                        visit(nested)
            elif isinstance(item, list):
                for nested in item:
                    visit(nested)

        visit(value)
        return sorted(source_ids)

    @staticmethod
    def _deserialize_report(row: Any) -> Dict[str, Any]:
        payload = json.loads(row.content_json)
        payload["report_id"] = row.id
        payload["status"] = row.status
        return payload

    def _get_history_items(
        self,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        report_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        page = 1
        items: List[Dict[str, Any]] = []
        while True:
            payload = self.history.get_history_list(
                report_type=report_type,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
                page=page,
                limit=_HISTORY_PAGE_SIZE,
            )
            batch = list(payload.get("items") or [])
            items.extend(batch)
            total = int(payload.get("total") or len(items))
            if not batch or len(items) >= total:
                break
            page += 1

        return sorted(
            items,
            key=lambda item: (
                _parse_created_at(item.get("created_at")) or datetime.min,
                int(item.get("id") or 0),
            ),
            reverse=True,
        )

    @staticmethod
    def _formal_analysis_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            item
            for item in items
            if str(item.get("report_type") or "") in FORMAL_ANALYSIS_REPORT_TYPES
            and str(item.get("stock_code") or "").strip().upper() not in {"", "MARKET", "PERIOD"}
        ]

    def _generate_historical(
        self,
        *,
        window: PeriodWindow,
        generated_at: datetime,
    ) -> Dict[str, Any]:
        items = self._get_history_items(
            start_date=window.start_date,
            end_date=window.end_date,
        )
        formal_items = self._formal_analysis_items(items)
        market_items = [
            item for item in items if item.get("report_type") == "market_review"
        ]
        stock_items = [item for item in formal_items if not _is_etf(item)]
        etf_items = [item for item in formal_items if _is_etf(item)]

        return {
            "period": window.period,
            "report_kind": "historical",
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
            "generated_at": _serialize_datetime(generated_at),
            "source_record_count": len(formal_items) + len(market_items),
            "stock_summaries": self._summarize_assets(stock_items, asset_type="stock"),
            "etf_summaries": self._summarize_assets(etf_items, asset_type="etf"),
            "market_reviews": [
                {
                    "record_id": int(item.get("id") or 0),
                    "region": item.get("region"),
                    "created_at": item.get("created_at"),
                    "summary": item.get("analysis_summary"),
                    "trend_prediction": item.get("trend_prediction"),
                }
                for item in market_items
            ],
            "outlook": None,
            "disclaimer": None,
        }

    @staticmethod
    def _summarize_assets(
        items: Iterable[Dict[str, Any]],
        *,
        asset_type: str,
    ) -> List[Dict[str, Any]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            code = str(item.get("stock_code") or "").strip()
            groups.setdefault(code, []).append(item)

        summaries = []
        for code, records in groups.items():
            records.sort(
                key=lambda item: (
                    _parse_created_at(item.get("created_at")) or datetime.min,
                    int(item.get("id") or 0),
                ),
                reverse=True,
            )
            latest = records[0]
            counts = {"bullish": 0, "neutral": 0, "bearish": 0, "unknown": 0}
            for record in records:
                direction = _normalize_direction(
                    record.get("trend_prediction"),
                    record.get("action"),
                    record.get("operation_advice"),
                )
                counts[_direction_bucket(direction)] += 1
            summaries.append(
                {
                    "stock_code": code,
                    "stock_name": latest.get("stock_name"),
                    "asset_type": asset_type,
                    "record_count": len(records),
                    "latest_record_id": int(latest.get("id") or 0),
                    "latest_created_at": latest.get("created_at"),
                    "latest_trend": latest.get("trend_prediction"),
                    "latest_summary": latest.get("analysis_summary"),
                    "direction_counts": counts,
                    "source_record_ids": [int(record.get("id") or 0) for record in records],
                }
            )
        return sorted(summaries, key=lambda item: item["stock_code"])

    def _generate_outlook(
        self,
        *,
        window: PeriodWindow,
        as_of: date,
        generated_at: datetime,
    ) -> Dict[str, Any]:
        cutoff = as_of - timedelta(days=13)
        items = self._get_history_items(start_date=cutoff, end_date=as_of)
        formal_items = self._formal_analysis_items(items)
        market_items = [
            item for item in items if item.get("report_type") == "market_review"
        ]

        qualified_by_code: Dict[str, List[Dict[str, Any]]] = {}
        for item in formal_items:
            direction = _normalize_direction(
                item.get("trend_prediction"),
                item.get("action"),
                item.get("operation_advice"),
            )
            if direction is None:
                continue
            normalized = dict(item)
            normalized["_outlook_direction"] = direction
            code = str(item.get("stock_code") or "").strip()
            qualified_by_code.setdefault(code, []).append(normalized)

        outlook_items = [
            self._build_outlook_item(records)
            for records in qualified_by_code.values()
            if records
        ]
        outlook_items.sort(key=lambda item: item["stock_code"])
        stocks = [item for item in outlook_items if item["asset_type"] == "stock"]
        etfs = [item for item in outlook_items if item["asset_type"] == "etf"]

        source_ids = sorted(
            {
                source_id
                for item in outlook_items
                for source_id in item["source_record_ids"]
            }
            | {int(item.get("id") or 0) for item in market_items if item.get("id")}
        )
        data_times = [
            parsed
            for parsed in (
                _parse_created_at(item.get("created_at"))
                for item in [*formal_items, *market_items]
                if int(item.get("id") or 0) in source_ids
            )
            if parsed is not None
        ]
        data_as_of = _serialize_datetime(max(data_times)) if data_times else None
        status = "ready" if outlook_items else "insufficient_data"
        message = None if outlook_items else INSUFFICIENT_OUTLOOK_MESSAGE

        outlook = {
            "snapshot_version": 1,
            "status": status,
            "message": message,
            "target_period": {
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
            },
            "generated_at": _serialize_datetime(generated_at),
            "overall_tendency": self._overall_tendency(outlook_items),
            "stocks": stocks,
            "etfs": etfs,
            "market_signals": [
                {
                    "record_id": int(item.get("id") or 0),
                    "region": item.get("region"),
                    "created_at": item.get("created_at"),
                    "summary": item.get("analysis_summary"),
                }
                for item in market_items
            ],
            "data_as_of": data_as_of,
            "source_record_count": len(source_ids),
            "source_record_ids": source_ids,
            "disclaimer": OUTLOOK_DISCLAIMER,
        }
        snapshot_id = self._save_outlook_snapshot(outlook, generated_at=generated_at)
        outlook["snapshot_id"] = snapshot_id

        return {
            "period": window.period,
            "report_kind": "outlook",
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
            "generated_at": _serialize_datetime(generated_at),
            "source_record_count": len(source_ids),
            "stock_summaries": [],
            "etf_summaries": [],
            "market_reviews": [],
            "outlook": outlook,
            "matched_outlook": None,
            "disclaimer": OUTLOOK_DISCLAIMER,
        }

    def _build_outlook_item(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        records.sort(
            key=lambda item: (
                _parse_created_at(item.get("created_at")) or datetime.min,
                int(item.get("id") or 0),
            ),
            reverse=True,
        )
        latest = records[0]
        record_id = int(latest.get("id") or 0)
        detail = self.history.get_history_detail_by_id(record_id) or {}
        raw_result = detail.get("raw_result")
        raw = raw_result if isinstance(raw_result, dict) else {}
        dashboard = raw.get("dashboard")
        dashboard = dashboard if isinstance(dashboard, dict) else {}
        synthesis = dashboard.get("strategy_synthesis")
        synthesis = synthesis if isinstance(synthesis, dict) else {}

        tendency = latest["_outlook_direction"]
        confidence = _normalize_confidence(raw.get("confidence_level"))
        strategy_signal = _first_non_empty(
            synthesis.get("final_signal"),
            raw.get("action"),
            latest.get("action"),
        )
        historical_signals = [
            f"趋势：{latest.get('trend_prediction')}"
            if latest.get("trend_prediction")
            else None,
            f"策略信号：{strategy_signal}" if strategy_signal else None,
            f"置信信息：{confidence}",
            f"最近摘要：{latest.get('analysis_summary')}"
            if latest.get("analysis_summary")
            else None,
        ]
        synthesis_summary = _first_non_empty(
            synthesis.get("summary"),
            synthesis.get("summary_text"),
        )
        if synthesis_summary:
            historical_signals.append(f"策略综合：{synthesis_summary}")

        risk_warning = str(raw.get("risk_warning") or "").strip()
        risks = [risk_warning] if risk_warning else ["历史记录未提供明确风险提示。"]
        invalidation = self._build_invalidation_conditions(tendency, detail)

        return {
            "stock_code": str(latest.get("stock_code") or ""),
            "stock_name": latest.get("stock_name"),
            "asset_type": "etf" if _is_etf(latest) else "stock",
            "tendency": tendency,
            "confidence": confidence,
            "historical_signals": [signal for signal in historical_signals if signal],
            "risks": risks,
            "invalidation_conditions": invalidation,
            "data_as_of": latest.get("created_at"),
            "source_record_count": len(records),
            "source_record_ids": [int(record.get("id") or 0) for record in records],
        }

    @staticmethod
    def _build_invalidation_conditions(
        tendency: str,
        detail: Dict[str, Any],
    ) -> List[str]:
        support = _as_number_text(
            _first_non_empty(detail.get("stop_loss"), detail.get("ideal_buy"))
        )
        resistance = _as_number_text(
            _first_non_empty(detail.get("take_profit"), detail.get("secondary_buy"))
        )
        if tendency == "看多":
            if support:
                return [
                    f"价格有效跌破历史支撑参考 {support}。",
                    "后续正式分析的趋势或策略信号转为看空。",
                ]
            return ["后续正式分析的趋势或策略信号转为看空。"]
        if tendency == "看空":
            if resistance:
                return [
                    f"价格有效突破历史压力参考 {resistance}。",
                    "后续正式分析的趋势或策略信号转为看多。",
                ]
            return ["后续正式分析的趋势或策略信号转为看多。"]

        conditions = ["后续正式分析确认趋势脱离中性区间。"]
        if support or resistance:
            bounds = " / ".join(value for value in (support, resistance) if value)
            conditions.insert(0, f"价格有效突破历史支撑/压力参考 {bounds}。")
        return conditions

    @staticmethod
    def _overall_tendency(items: List[Dict[str, Any]]) -> Optional[str]:
        if not items:
            return None
        counts = {"看多": 0, "中性": 0, "看空": 0}
        for item in items:
            counts[item["tendency"]] += 1
        maximum = max(counts.values())
        leaders = [direction for direction, count in counts.items() if count == maximum]
        return leaders[0] if len(leaders) == 1 else "中性"

    def _save_outlook_snapshot(
        self,
        outlook: Dict[str, Any],
        *,
        generated_at: datetime,
    ) -> Optional[int]:
        if self.db is None:
            return None
        return self.db.save_period_outlook_snapshot(
            query_id=f"period-outlook-{uuid4().hex}",
            snapshot=outlook,
            created_at=generated_at,
        )

    def _find_matching_outlook(self, window: PeriodWindow) -> Optional[Dict[str, Any]]:
        items = self._get_history_items(report_type=PERIOD_OUTLOOK_REPORT_TYPE)
        for item in items:
            record_id = int(item.get("id") or 0)
            if not record_id:
                continue
            detail = self.history.get_history_detail_by_id(record_id) or {}
            snapshot = detail.get("context_snapshot")
            if not isinstance(snapshot, dict):
                continue
            target = snapshot.get("target_period")
            if not isinstance(target, dict):
                continue
            if (
                target.get("start_date") == window.start_date.isoformat()
                and target.get("end_date") == window.end_date.isoformat()
            ):
                return {
                    **snapshot,
                    "snapshot_id": record_id,
                    "snapshot_created_at": item.get("created_at"),
                }
        return None

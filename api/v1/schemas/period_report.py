# -*- coding: utf-8 -*-
"""Schemas for manually generated historical period reports and outlooks."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


PeriodKey = Literal[
    "week_to_date",
    "previous_week",
    "next_week",
    "weeks_5",
    "weeks_10",
    "month_1",
    "months_2",
]
OutlookTendency = Literal["看多", "中性", "看空"]
OutlookConfidence = Literal["低", "中", "高"]


class PeriodReportGenerateRequest(BaseModel):
    period: PeriodKey


class PeriodDirectionCounts(BaseModel):
    bullish: int = Field(0, ge=0)
    neutral: int = Field(0, ge=0)
    bearish: int = Field(0, ge=0)
    unknown: int = Field(0, ge=0)


class PeriodAssetSummary(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None
    asset_type: Literal["stock", "etf"]
    record_count: int = Field(..., ge=1)
    latest_record_id: int = Field(..., ge=1)
    latest_created_at: Optional[str] = None
    latest_trend: Optional[str] = None
    latest_summary: Optional[str] = None
    direction_counts: PeriodDirectionCounts
    source_record_ids: List[int] = Field(default_factory=list)


class PeriodMarketReview(BaseModel):
    record_id: int = Field(..., ge=1)
    region: Optional[str] = None
    created_at: Optional[str] = None
    summary: Optional[str] = None
    trend_prediction: Optional[str] = None


class PeriodTargetWindow(BaseModel):
    start_date: str
    end_date: str


class PeriodOutlookItem(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None
    asset_type: Literal["stock", "etf"]
    tendency: OutlookTendency
    confidence: OutlookConfidence
    historical_signals: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    data_as_of: Optional[str] = None
    source_record_count: int = Field(..., ge=1)
    source_record_ids: List[int] = Field(default_factory=list)


class PeriodOutlookMarketSignal(BaseModel):
    record_id: int = Field(..., ge=1)
    region: Optional[str] = None
    created_at: Optional[str] = None
    summary: Optional[str] = None


class PeriodOutlookSnapshot(BaseModel):
    snapshot_version: int = Field(..., ge=1)
    snapshot_id: Optional[int] = Field(None, ge=1)
    snapshot_created_at: Optional[str] = None
    status: Literal["ready", "insufficient_data"]
    message: Optional[str] = None
    target_period: PeriodTargetWindow
    generated_at: str
    overall_tendency: Optional[OutlookTendency] = None
    stocks: List[PeriodOutlookItem] = Field(default_factory=list)
    etfs: List[PeriodOutlookItem] = Field(default_factory=list)
    market_signals: List[PeriodOutlookMarketSignal] = Field(default_factory=list)
    data_as_of: Optional[str] = None
    source_record_count: int = Field(..., ge=0)
    source_record_ids: List[int] = Field(default_factory=list)
    disclaimer: str


class PeriodReportResponse(BaseModel):
    report_id: int = Field(..., ge=1)
    status: Literal["ready", "insufficient_data"]
    period: PeriodKey
    report_kind: Literal["historical", "outlook"]
    start_date: str
    end_date: str
    generated_at: str
    source_record_count: int = Field(..., ge=0)
    stock_summaries: List[PeriodAssetSummary] = Field(default_factory=list)
    etf_summaries: List[PeriodAssetSummary] = Field(default_factory=list)
    market_reviews: List[PeriodMarketReview] = Field(default_factory=list)
    outlook: Optional[PeriodOutlookSnapshot] = None
    matched_outlook: Optional[PeriodOutlookSnapshot] = None
    disclaimer: Optional[str] = None

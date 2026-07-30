# -*- coding: utf-8 -*-
"""Versioned, stock-only backup and atomic restore for the PP02 portfolio ledger."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import delete, select

from src.repositories.portfolio_repo import PortfolioRepository
from src.storage import (
    CURRENT_SCHEMA_VERSION,
    DatabaseManager,
    PortfolioAccount,
    PortfolioCashLedger,
    PortfolioCorporateAction,
    PortfolioDailySnapshot,
    PortfolioPosition,
    PortfolioPositionLot,
    PortfolioTrade,
)

BACKUP_FORMAT = "pp02.portfolio.backup"
BACKUP_FORMAT_VERSION = 1
PP02_PROJECT_ID = "PP02"
PP02_PROJECT_NAME = "AI 每日股票分析"
PP02_APPLICATION_BASE_VERSION = "3.28.0"
VALID_MARKETS = {"cn", "hk", "us", "jp", "kr", "tw"}
COUNT_KEYS = ("accounts", "trades", "cash_ledger", "corporate_actions")


class PortfolioBackupValidationError(ValueError):
    """Raised when a backup document does not match the supported contract."""


class PortfolioBackupConflictError(Exception):
    """Raised when the backup or current ledger changed after preview."""


class PortfolioBackupService:
    """Export and replace the official portfolio ledger without parallel state."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()
        self.repo = PortfolioRepository(db_manager=self.db)

    def export_backup(self) -> Dict[str, Any]:
        with self.db.get_session() as session:
            portfolio = self._read_portfolio(session)
        created_at = datetime.now(timezone.utc).replace(microsecond=0)
        return {
            "format": BACKUP_FORMAT,
            "format_version": BACKUP_FORMAT_VERSION,
            "metadata": {
                "created_at": created_at.isoformat().replace("+00:00", "Z"),
                "project_id": PP02_PROJECT_ID,
                "project_name": PP02_PROJECT_NAME,
                "application_base_version": PP02_APPLICATION_BASE_VERSION,
                "database_schema_version": CURRENT_SCHEMA_VERSION,
            },
            "portfolio": portfolio,
        }

    def preview_restore(self, backup: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._validate_backup(backup)
        with self.db.get_session() as session:
            current = self._read_portfolio(session)
        return self._build_preview(normalized, current)

    def restore_backup(self, backup: Dict[str, Any], *, preview_token: str) -> Dict[str, Any]:
        normalized = self._validate_backup(backup)
        token = str(preview_token or "").strip()
        if not token:
            raise PortfolioBackupConflictError("A fresh restore preview is required.")
        with self.repo.portfolio_write_session() as session:
            current = self._read_portfolio(session)
            expected = self._build_preview(normalized, current)["preview_token"]
            if not hmac.compare_digest(token, expected):
                raise PortfolioBackupConflictError(
                    "Backup or portfolio ledger changed after preview; preview again."
                )
            self._delete_current_portfolio(session)
            self._insert_portfolio(session, normalized["portfolio"])
            session.flush()
        return {"restored_counts": self._counts(normalized["portfolio"])}

    def _build_preview(self, backup: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        token = hashlib.sha256(
            (self._digest(backup) + ":" + self._digest(current)).encode("utf-8")
        ).hexdigest()
        return {
            "mode": "replace",
            "preview_token": token,
            "requires_confirmation": True,
            "incoming_counts": self._counts(backup["portfolio"]),
            "current_counts": self._counts(current),
            "warnings": [
                "恢复会替换当前股票组合账本。",
                "派生持仓、批次和快照不会从备份导入，将由正式事件重新计算。",
            ],
        }

    @staticmethod
    def _counts(portfolio: Dict[str, Any]) -> Dict[str, int]:
        return {key: len(portfolio[key]) for key in COUNT_KEYS}

    @staticmethod
    def _digest(value: Dict[str, Any]) -> str:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _read_portfolio(self, session: Any) -> Dict[str, Any]:
        accounts = session.execute(
            select(PortfolioAccount).order_by(PortfolioAccount.id.asc())
        ).scalars().all()
        trades = session.execute(
            select(PortfolioTrade).order_by(PortfolioTrade.id.asc())
        ).scalars().all()
        cash_rows = session.execute(
            select(PortfolioCashLedger).order_by(PortfolioCashLedger.id.asc())
        ).scalars().all()
        actions = session.execute(
            select(PortfolioCorporateAction).order_by(PortfolioCorporateAction.id.asc())
        ).scalars().all()
        return {
            "accounts": [
                {
                    "id": int(row.id),
                    "name": row.name,
                    "broker": row.broker,
                    "market": row.market,
                    "base_currency": row.base_currency,
                    "is_active": bool(row.is_active),
                    "created_at": self._datetime_text(row.created_at),
                    "updated_at": self._datetime_text(row.updated_at),
                }
                for row in accounts
            ],
            "trades": [
                {
                    "id": int(row.id),
                    "account_id": int(row.account_id),
                    "trade_uid": row.trade_uid,
                    "symbol": row.symbol,
                    "market": row.market,
                    "currency": row.currency,
                    "trade_date": row.trade_date.isoformat(),
                    "side": row.side,
                    "quantity": float(row.quantity),
                    "price": float(row.price),
                    "fee": float(row.fee or 0.0),
                    "tax": float(row.tax or 0.0),
                    "note": row.note,
                    "dedup_hash": row.dedup_hash,
                    "created_at": self._datetime_text(row.created_at),
                }
                for row in trades
            ],
            "cash_ledger": [
                {
                    "id": int(row.id),
                    "account_id": int(row.account_id),
                    "event_date": row.event_date.isoformat(),
                    "direction": row.direction,
                    "amount": float(row.amount),
                    "currency": row.currency,
                    "note": row.note,
                    "created_at": self._datetime_text(row.created_at),
                }
                for row in cash_rows
            ],
            "corporate_actions": [
                {
                    "id": int(row.id),
                    "account_id": int(row.account_id),
                    "symbol": row.symbol,
                    "market": row.market,
                    "currency": row.currency,
                    "effective_date": row.effective_date.isoformat(),
                    "action_type": row.action_type,
                    "cash_dividend_per_share": (
                        None
                        if row.cash_dividend_per_share is None
                        else float(row.cash_dividend_per_share)
                    ),
                    "split_ratio": None if row.split_ratio is None else float(row.split_ratio),
                    "note": row.note,
                    "created_at": self._datetime_text(row.created_at),
                }
                for row in actions
            ],
        }

    def _validate_backup(self, backup: Dict[str, Any]) -> Dict[str, Any]:
        root = self._object(backup, "backup")
        self._keys(root, {"format", "format_version", "metadata", "portfolio"}, "backup")
        if root["format"] != BACKUP_FORMAT:
            raise PortfolioBackupValidationError("Unsupported backup format.")
        if root["format_version"] != BACKUP_FORMAT_VERSION:
            raise PortfolioBackupValidationError("Unsupported backup format version.")
        metadata = self._object(root["metadata"], "metadata")
        self._keys(
            metadata,
            {
                "created_at",
                "project_id",
                "project_name",
                "application_base_version",
                "database_schema_version",
            },
            "metadata",
        )
        if metadata["project_id"] != PP02_PROJECT_ID or metadata["project_name"] != PP02_PROJECT_NAME:
            raise PortfolioBackupValidationError("Backup is not a PP02 stock portfolio backup.")
        normalized_metadata = {
            "created_at": self._datetime_text(
                self._parse_datetime(metadata["created_at"], "metadata.created_at"),
                utc_suffix=True,
            ),
            "project_id": PP02_PROJECT_ID,
            "project_name": PP02_PROJECT_NAME,
            "application_base_version": self._text(
                metadata["application_base_version"],
                "metadata.application_base_version",
                32,
            ),
            "database_schema_version": self._text(
                metadata["database_schema_version"],
                "metadata.database_schema_version",
                128,
            ),
        }
        portfolio = self._object(root["portfolio"], "portfolio")
        self._keys(portfolio, set(COUNT_KEYS), "portfolio")
        normalized = {
            "accounts": self._accounts(portfolio["accounts"]),
            "trades": self._trades(portfolio["trades"]),
            "cash_ledger": self._cash(portfolio["cash_ledger"]),
            "corporate_actions": self._actions(portfolio["corporate_actions"]),
        }
        self._relationships(normalized)
        return {
            "format": BACKUP_FORMAT,
            "format_version": BACKUP_FORMAT_VERSION,
            "metadata": normalized_metadata,
            "portfolio": normalized,
        }

    def _accounts(self, value: Any) -> List[Dict[str, Any]]:
        fields = {
            "id", "name", "broker", "market", "base_currency", "is_active",
            "created_at", "updated_at",
        }
        result = []
        seen: Set[int] = set()
        for index, raw in enumerate(self._list(value, "portfolio.accounts")):
            label = f"portfolio.accounts[{index}]"
            row = self._object(raw, label)
            self._keys(row, fields, label)
            row_id = self._positive_int(row["id"], label + ".id")
            if row_id in seen:
                raise PortfolioBackupValidationError("Duplicate account id in backup.")
            seen.add(row_id)
            market = self._market(row["market"], label + ".market")
            result.append(
                {
                    "id": row_id,
                    "name": self._text(row["name"], label + ".name", 64),
                    "broker": self._optional_text(row["broker"], label + ".broker", 64),
                    "market": market,
                    "base_currency": self._currency(row["base_currency"], label + ".base_currency"),
                    "is_active": self._boolean(row["is_active"], label + ".is_active"),
                    "created_at": self._optional_datetime(row["created_at"], label + ".created_at"),
                    "updated_at": self._optional_datetime(row["updated_at"], label + ".updated_at"),
                }
            )
        return result

    def _trades(self, value: Any) -> List[Dict[str, Any]]:
        fields = {
            "id", "account_id", "trade_uid", "symbol", "market", "currency",
            "trade_date", "side", "quantity", "price", "fee", "tax", "note",
            "dedup_hash", "created_at",
        }
        result = []
        for index, raw in enumerate(self._list(value, "portfolio.trades")):
            label = f"portfolio.trades[{index}]"
            row = self._object(raw, label)
            self._keys(row, fields, label)
            side = self._text(row["side"], label + ".side", 8).lower()
            if side not in {"buy", "sell"}:
                raise PortfolioBackupValidationError(label + ".side is not supported.")
            result.append(
                {
                    "id": self._positive_int(row["id"], label + ".id"),
                    "account_id": self._positive_int(row["account_id"], label + ".account_id"),
                    "trade_uid": self._optional_text(row["trade_uid"], label + ".trade_uid", 128),
                    "symbol": self._text(row["symbol"], label + ".symbol", 16),
                    "market": self._market(row["market"], label + ".market"),
                    "currency": self._currency(row["currency"], label + ".currency"),
                    "trade_date": self._parse_date(row["trade_date"], label + ".trade_date"),
                    "side": side,
                    "quantity": self._positive_number(row["quantity"], label + ".quantity"),
                    "price": self._positive_number(row["price"], label + ".price"),
                    "fee": self._nonnegative(row["fee"], label + ".fee"),
                    "tax": self._nonnegative(row["tax"], label + ".tax"),
                    "note": self._optional_text(row["note"], label + ".note", 255),
                    "dedup_hash": self._optional_text(row["dedup_hash"], label + ".dedup_hash", 64),
                    "created_at": self._optional_datetime(row["created_at"], label + ".created_at"),
                }
            )
        return result

    def _cash(self, value: Any) -> List[Dict[str, Any]]:
        fields = {"id", "account_id", "event_date", "direction", "amount", "currency", "note", "created_at"}
        result = []
        for index, raw in enumerate(self._list(value, "portfolio.cash_ledger")):
            label = f"portfolio.cash_ledger[{index}]"
            row = self._object(raw, label)
            self._keys(row, fields, label)
            direction = self._text(row["direction"], label + ".direction", 8).lower()
            if direction not in {"in", "out"}:
                raise PortfolioBackupValidationError(label + ".direction is not supported.")
            result.append(
                {
                    "id": self._positive_int(row["id"], label + ".id"),
                    "account_id": self._positive_int(row["account_id"], label + ".account_id"),
                    "event_date": self._parse_date(row["event_date"], label + ".event_date"),
                    "direction": direction,
                    "amount": self._positive_number(row["amount"], label + ".amount"),
                    "currency": self._currency(row["currency"], label + ".currency"),
                    "note": self._optional_text(row["note"], label + ".note", 255),
                    "created_at": self._optional_datetime(row["created_at"], label + ".created_at"),
                }
            )
        return result

    def _actions(self, value: Any) -> List[Dict[str, Any]]:
        fields = {
            "id", "account_id", "symbol", "market", "currency", "effective_date",
            "action_type", "cash_dividend_per_share", "split_ratio", "note", "created_at",
        }
        result = []
        for index, raw in enumerate(self._list(value, "portfolio.corporate_actions")):
            label = f"portfolio.corporate_actions[{index}]"
            row = self._object(raw, label)
            self._keys(row, fields, label)
            action_type = self._text(row["action_type"], label + ".action_type", 24).lower()
            if action_type not in {"cash_dividend", "split_adjustment"}:
                raise PortfolioBackupValidationError(label + ".action_type is not supported.")
            dividend = self._optional_nonnegative(
                row["cash_dividend_per_share"], label + ".cash_dividend_per_share"
            )
            ratio = self._optional_positive(row["split_ratio"], label + ".split_ratio")
            if action_type == "cash_dividend" and dividend is None:
                raise PortfolioBackupValidationError(label + ".cash_dividend_per_share is required.")
            if action_type == "split_adjustment" and ratio is None:
                raise PortfolioBackupValidationError(label + ".split_ratio is required.")
            result.append(
                {
                    "id": self._positive_int(row["id"], label + ".id"),
                    "account_id": self._positive_int(row["account_id"], label + ".account_id"),
                    "symbol": self._text(row["symbol"], label + ".symbol", 16),
                    "market": self._market(row["market"], label + ".market"),
                    "currency": self._currency(row["currency"], label + ".currency"),
                    "effective_date": self._parse_date(row["effective_date"], label + ".effective_date"),
                    "action_type": action_type,
                    "cash_dividend_per_share": dividend,
                    "split_ratio": ratio,
                    "note": self._optional_text(row["note"], label + ".note", 255),
                    "created_at": self._optional_datetime(row["created_at"], label + ".created_at"),
                }
            )
        return result

    @staticmethod
    def _relationships(portfolio: Dict[str, Any]) -> None:
        account_ids = {row["id"] for row in portfolio["accounts"]}
        for group in ("trades", "cash_ledger", "corporate_actions"):
            ids: Set[int] = set()
            for row in portfolio[group]:
                if row["id"] in ids:
                    raise PortfolioBackupValidationError("Duplicate " + group + " id in backup.")
                ids.add(row["id"])
                if row["account_id"] not in account_ids:
                    raise PortfolioBackupValidationError(group + " references an unknown account.")
        uids: Set[Any] = set()
        hashes: Set[Any] = set()
        for row in portfolio["trades"]:
            if row["trade_uid"]:
                key = (row["account_id"], row["trade_uid"])
                if key in uids:
                    raise PortfolioBackupValidationError("Duplicate trade_uid in backup.")
                uids.add(key)
            if row["dedup_hash"]:
                key = (row["account_id"], row["dedup_hash"])
                if key in hashes:
                    raise PortfolioBackupValidationError("Duplicate trade dedup_hash in backup.")
                hashes.add(key)

    @staticmethod
    def _delete_current_portfolio(session: Any) -> None:
        for model in (
            PortfolioDailySnapshot,
            PortfolioPositionLot,
            PortfolioPosition,
            PortfolioCorporateAction,
            PortfolioCashLedger,
            PortfolioTrade,
            PortfolioAccount,
        ):
            session.execute(delete(model))

    @staticmethod
    def _insert_portfolio(session: Any, portfolio: Dict[str, Any]) -> None:
        for row in portfolio["accounts"]:
            session.add(PortfolioAccount(owner_id=None, **row))
        session.flush()
        for row in portfolio["trades"]:
            session.add(PortfolioTrade(**row))
        for row in portfolio["cash_ledger"]:
            session.add(PortfolioCashLedger(**row))
        for row in portfolio["corporate_actions"]:
            session.add(PortfolioCorporateAction(**row))

    @staticmethod
    def _object(value: Any, label: str) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise PortfolioBackupValidationError(label + " must be an object.")
        return value

    @staticmethod
    def _list(value: Any, label: str) -> List[Any]:
        if not isinstance(value, list):
            raise PortfolioBackupValidationError(label + " must be a list.")
        return value

    @staticmethod
    def _keys(value: Dict[str, Any], expected: Set[str], label: str) -> None:
        actual = set(value)
        if actual != expected:
            raise PortfolioBackupValidationError(
                label + " fields do not match the backup contract; missing="
                + str(sorted(expected - actual)) + ", extra=" + str(sorted(actual - expected))
            )

    @staticmethod
    def _text(value: Any, label: str, maximum: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PortfolioBackupValidationError(label + " must be a non-empty string.")
        text = value.strip()
        if len(text) > maximum:
            raise PortfolioBackupValidationError(label + " is too long.")
        return text

    @classmethod
    def _optional_text(cls, value: Any, label: str, maximum: int) -> Optional[str]:
        return None if value is None else cls._text(value, label, maximum)

    @staticmethod
    def _boolean(value: Any, label: str) -> bool:
        if not isinstance(value, bool):
            raise PortfolioBackupValidationError(label + " must be a boolean.")
        return value

    @staticmethod
    def _positive_int(value: Any, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise PortfolioBackupValidationError(label + " must be a positive integer.")
        return value

    @staticmethod
    def _number(value: Any, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PortfolioBackupValidationError(label + " must be a number.")
        number = float(value)
        if not math.isfinite(number):
            raise PortfolioBackupValidationError(label + " must be finite.")
        return number

    @classmethod
    def _positive_number(cls, value: Any, label: str) -> float:
        number = cls._number(value, label)
        if number <= 0:
            raise PortfolioBackupValidationError(label + " must be greater than zero.")
        return number

    @classmethod
    def _nonnegative(cls, value: Any, label: str) -> float:
        number = cls._number(value, label)
        if number < 0:
            raise PortfolioBackupValidationError(label + " must be non-negative.")
        return number

    @classmethod
    def _optional_positive(cls, value: Any, label: str) -> Optional[float]:
        return None if value is None else cls._positive_number(value, label)

    @classmethod
    def _optional_nonnegative(cls, value: Any, label: str) -> Optional[float]:
        return None if value is None else cls._nonnegative(value, label)

    @classmethod
    def _currency(cls, value: Any, label: str) -> str:
        return cls._text(value, label, 8).upper()

    @classmethod
    def _market(cls, value: Any, label: str) -> str:
        market = cls._text(value, label, 8).lower()
        if market not in VALID_MARKETS:
            raise PortfolioBackupValidationError(label + " is not supported.")
        return market

    @staticmethod
    def _parse_date(value: Any, label: str) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise PortfolioBackupValidationError(label + " must be ISO date.") from exc

    @staticmethod
    def _parse_datetime(value: Any, label: str) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        else:
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError) as exc:
                raise PortfolioBackupValidationError(label + " must be ISO datetime.") from exc
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    @classmethod
    def _optional_datetime(cls, value: Any, label: str) -> Optional[datetime]:
        return None if value is None else cls._parse_datetime(value, label)

    @staticmethod
    def _datetime_text(value: Optional[datetime], *, utc_suffix: bool = False) -> Optional[str]:
        if value is None:
            return None
        parsed = value
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        text = parsed.isoformat()
        return text + "Z" if utc_suffix else text

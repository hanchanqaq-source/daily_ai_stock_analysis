# -*- coding: utf-8 -*-
"""R3.4 behavior tests for PP02 stock-only portfolio backup and restore."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

try:
    import litellm  # noqa: F401
except ModuleNotFoundError:
    sys.modules["litellm"] = MagicMock()

import src.auth as auth
from api.app import create_app
from src.config import Config
from src.services.portfolio_service import PortfolioService
from src.storage import CURRENT_SCHEMA_VERSION, DatabaseManager

try:
    from src.services.portfolio_backup_service import (
        PortfolioBackupConflictError,
        PortfolioBackupService,
        PortfolioBackupValidationError,
    )
except ModuleNotFoundError:
    PortfolioBackupService = None  # type: ignore[assignment]
    PortfolioBackupConflictError = RuntimeError  # type: ignore[assignment,misc]
    PortfolioBackupValidationError = ValueError  # type: ignore[assignment,misc]


def _reset_auth_globals() -> None:
    auth._auth_enabled = None
    auth._session_secret = None
    auth._password_hash_salt = None
    auth._password_hash_stored = None
    auth._rate_limit = {}


class PortfolioBackupTestCase(unittest.TestCase):
    def setUp(self) -> None:
        _reset_auth_globals()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.env_path = self.data_dir / ".env"
        self.db_path = self.data_dir / "portfolio_backup_test.db"
        self.env_path.write_text(
            "\n".join(
                [
                    "STOCK_LIST=600519",
                    "GEMINI_API_KEY=test",
                    "ADMIN_AUTH_ENABLED=false",
                    f"DATABASE_PATH={self.db_path}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        os.environ["ENV_FILE"] = str(self.env_path)
        os.environ["DATABASE_PATH"] = str(self.db_path)
        Config.reset_instance()
        DatabaseManager.reset_instance()
        self.db = DatabaseManager.get_instance()
        self.portfolio = PortfolioService()
        self.client = TestClient(create_app(static_dir=self.data_dir / "empty-static"))

    def tearDown(self) -> None:
        DatabaseManager.reset_instance()
        Config.reset_instance()
        os.environ.pop("ENV_FILE", None)
        os.environ.pop("DATABASE_PATH", None)
        self.temp_dir.cleanup()

    def _backup_service(self):
        self.assertIsNotNone(
            PortfolioBackupService,
            "R3.4 requires src.services.portfolio_backup_service.PortfolioBackupService",
        )
        return PortfolioBackupService(db_manager=self.db)

    def _seed_current_ledger(self) -> int:
        account = self.portfolio.create_account(
            name="Current",
            broker="Demo",
            market="cn",
            base_currency="CNY",
            owner_id="legacy-owner-must-not-export",
        )
        account_id = int(account["id"])
        self.portfolio.record_cash_ledger(
            account_id=account_id,
            event_date=date(2026, 1, 1),
            direction="in",
            amount=10000,
            currency="CNY",
            note="opening cash",
        )
        self.portfolio.record_trade(
            account_id=account_id,
            symbol="600519",
            trade_date=date(2026, 1, 2),
            side="buy",
            quantity=10,
            price=100,
            market="cn",
            currency="CNY",
            trade_uid="current-buy-1",
            note="seed",
        )
        self.portfolio.record_corporate_action(
            account_id=account_id,
            symbol="600519",
            effective_date=date(2026, 1, 3),
            action_type="cash_dividend",
            market="cn",
            currency="CNY",
            cash_dividend_per_share=1,
            note="dividend",
        )
        inactive = self.portfolio.create_account(
            name="Inactive",
            broker=None,
            market="us",
            base_currency="USD",
        )
        self.portfolio.deactivate_account(int(inactive["id"]))
        return account_id

    @staticmethod
    def _replacement_backup() -> dict:
        return {
            "format": "pp02.portfolio.backup",
            "format_version": 1,
            "metadata": {
                "created_at": "2026-07-30T03:00:00Z",
                "project_id": "PP02",
                "project_name": "AI 每日股票分析",
                "application_base_version": "3.28.0",
                "database_schema_version": CURRENT_SCHEMA_VERSION,
            },
            "portfolio": {
                "accounts": [
                    {
                        "id": 42,
                        "name": "Restored",
                        "broker": "Backup Broker",
                        "market": "cn",
                        "base_currency": "CNY",
                        "is_active": True,
                        "created_at": "2026-02-01T00:00:00",
                        "updated_at": "2026-02-01T00:00:00",
                    },
                    {
                        "id": 43,
                        "name": "Restored inactive",
                        "broker": None,
                        "market": "us",
                        "base_currency": "USD",
                        "is_active": False,
                        "created_at": "2026-02-01T00:00:00",
                        "updated_at": "2026-02-01T00:00:00",
                    },
                ],
                "trades": [
                    {
                        "id": 51,
                        "account_id": 42,
                        "trade_uid": "restored-buy-1",
                        "symbol": "600519",
                        "market": "cn",
                        "currency": "CNY",
                        "trade_date": "2026-02-02",
                        "side": "buy",
                        "quantity": 3.0,
                        "price": 100.0,
                        "fee": 1.0,
                        "tax": 0.0,
                        "note": "restored trade",
                        "dedup_hash": "restored-dedup-1",
                        "created_at": "2026-02-02T00:00:00",
                    }
                ],
                "cash_ledger": [
                    {
                        "id": 61,
                        "account_id": 42,
                        "event_date": "2026-02-01",
                        "direction": "in",
                        "amount": 1000.0,
                        "currency": "CNY",
                        "note": "restored cash",
                        "created_at": "2026-02-01T00:00:00",
                    }
                ],
                "corporate_actions": [],
            },
        }

    def test_export_is_versioned_and_contains_only_official_portfolio_events(self) -> None:
        self._seed_current_ledger()

        backup = self._backup_service().export_backup()

        self.assertEqual(backup["format"], "pp02.portfolio.backup")
        self.assertEqual(backup["format_version"], 1)
        self.assertEqual(backup["metadata"]["project_id"], "PP02")
        self.assertEqual(backup["metadata"]["application_base_version"], "3.28.0")
        self.assertEqual(backup["metadata"]["database_schema_version"], CURRENT_SCHEMA_VERSION)
        self.assertTrue(backup["metadata"]["created_at"].endswith("Z"))
        self.assertEqual(len(backup["portfolio"]["accounts"]), 2)
        self.assertEqual(len(backup["portfolio"]["trades"]), 1)
        self.assertEqual(len(backup["portfolio"]["cash_ledger"]), 1)
        self.assertEqual(len(backup["portfolio"]["corporate_actions"]), 1)
        self.assertNotIn("owner_id", backup["portfolio"]["accounts"][0])
        self.assertEqual(
            set(backup["portfolio"]),
            {"accounts", "trades", "cash_ledger", "corporate_actions"},
        )
        serialized = str(backup).lower()
        for excluded in ("portfolio_positions", "position_lots", ".env", "api_key", "fund"):
            self.assertNotIn(excluded, serialized)

    def test_preview_is_read_only_and_reports_replace_counts(self) -> None:
        current_account_id = self._seed_current_ledger()
        backup = self._replacement_backup()

        preview = self._backup_service().preview_restore(backup)

        self.assertEqual(preview["mode"], "replace")
        self.assertTrue(preview["requires_confirmation"])
        self.assertEqual(preview["incoming_counts"]["accounts"], 2)
        self.assertEqual(preview["incoming_counts"]["trades"], 1)
        self.assertEqual(preview["current_counts"]["accounts"], 2)
        self.assertEqual(preview["current_counts"]["trades"], 1)
        self.assertTrue(preview["preview_token"])
        accounts = self.portfolio.list_accounts(include_inactive=True)
        self.assertEqual([item["id"] for item in accounts], [current_account_id, current_account_id + 1])

    def test_restore_rejects_stale_preview_without_changing_current_ledger(self) -> None:
        current_account_id = self._seed_current_ledger()
        service = self._backup_service()
        backup = self._replacement_backup()
        preview = service.preview_restore(backup)
        self.portfolio.record_cash_ledger(
            account_id=current_account_id,
            event_date=date(2026, 1, 4),
            direction="in",
            amount=25,
            currency="CNY",
        )

        with self.assertRaises(PortfolioBackupConflictError):
            service.restore_backup(
                backup,
                preview_token=preview["preview_token"],
            )

        self.assertEqual(
            [item["name"] for item in self.portfolio.list_accounts(include_inactive=True)],
            ["Current", "Inactive"],
        )
        self.assertEqual(
            self.portfolio.list_cash_ledger_events(account_id=current_account_id)["total"],
            2,
        )

    def test_confirmed_restore_replaces_ledger_atomically_and_replays_positions(self) -> None:
        self._seed_current_ledger()
        service = self._backup_service()
        backup = self._replacement_backup()
        preview = service.preview_restore(backup)

        result = service.restore_backup(backup, preview_token=preview["preview_token"])

        self.assertEqual(result["restored_counts"]["accounts"], 2)
        self.assertEqual(result["restored_counts"]["trades"], 1)
        self.assertEqual(
            [item["name"] for item in self.portfolio.list_accounts(include_inactive=True)],
            ["Restored", "Restored inactive"],
        )
        snapshot = self.portfolio.get_portfolio_snapshot(
            account_id=42,
            as_of=date(2026, 2, 2),
            include_realtime=False,
        )
        self.assertEqual(snapshot["accounts"][0]["positions"][0]["quantity"], 3.0)
        exported = service.export_backup()
        self.assertEqual(exported["portfolio"]["accounts"][0]["id"], 42)
        self.assertNotIn("owner_id", exported["portfolio"]["accounts"][0])

    def test_invalid_backup_is_rejected_before_current_data_changes(self) -> None:
        current_account_id = self._seed_current_ledger()
        backup = self._replacement_backup()
        backup["format_version"] = 999

        with self.assertRaises(PortfolioBackupValidationError):
            self._backup_service().preview_restore(backup)

        self.assertEqual(
            self.portfolio.list_trade_events(account_id=current_account_id)["total"],
            1,
        )

    def test_api_requires_preview_token_before_restore(self) -> None:
        current_account_id = self._seed_current_ledger()

        export_response = self.client.get("/api/v1/portfolio/backup/export")
        self.assertEqual(export_response.status_code, 200, export_response.text)
        self.assertIn("attachment;", export_response.headers.get("content-disposition", ""))
        backup = self._replacement_backup()

        preview_response = self.client.post(
            "/api/v1/portfolio/backup/preview",
            json=backup,
        )
        self.assertEqual(preview_response.status_code, 200, preview_response.text)
        preview = preview_response.json()
        self.assertTrue(preview["requires_confirmation"])

        rejected = self.client.post(
            "/api/v1/portfolio/backup/restore",
            json={"backup": backup, "preview_token": "wrong-token"},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)
        self.assertEqual(
            self.portfolio.list_trade_events(account_id=current_account_id)["total"],
            1,
        )

        restored = self.client.post(
            "/api/v1/portfolio/backup/restore",
            json={"backup": backup, "preview_token": preview["preview_token"]},
        )
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()["restored_counts"]["accounts"], 2)
        self.assertEqual(
            [item["name"] for item in self.portfolio.list_accounts(include_inactive=True)],
            ["Restored", "Restored inactive"],
        )


if __name__ == "__main__":
    unittest.main()

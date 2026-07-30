# -*- coding: utf-8 -*-
"""R3.3 tests for quick position adjustment on the official event ledger."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import select

try:
    import litellm  # noqa: F401
except ModuleNotFoundError:
    sys.modules["litellm"] = MagicMock()

import src.auth as auth
from api.app import create_app
from src.config import Config
from src.services.portfolio_service import PortfolioConflictError, PortfolioService
from src.storage import DatabaseManager, PortfolioPosition


def _reset_auth_globals() -> None:
    auth._auth_enabled = None
    auth._session_secret = None
    auth._password_hash_salt = None
    auth._password_hash_stored = None
    auth._rate_limit = {}


class QuickPositionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        _reset_auth_globals()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.env_path = self.data_dir / ".env"
        self.db_path = self.data_dir / "quick_position_test.db"
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
        self.service = PortfolioService()
        self.client = TestClient(create_app(static_dir=self.data_dir / "empty-static"))

    def tearDown(self) -> None:
        DatabaseManager.reset_instance()
        Config.reset_instance()
        os.environ.pop("ENV_FILE", None)
        os.environ.pop("DATABASE_PATH", None)
        self.temp_dir.cleanup()

    def _seed_position(self, quantity: float = 10.0) -> int:
        account = self.service.create_account(
            name="Main",
            broker="Demo",
            market="cn",
            base_currency="CNY",
        )
        account_id = account["id"]
        self.service.record_cash_ledger(
            account_id=account_id,
            event_date=date(2026, 1, 1),
            direction="in",
            amount=10000,
            currency="CNY",
        )
        self.service.record_trade(
            account_id=account_id,
            symbol="600519",
            trade_date=date(2026, 1, 2),
            side="buy",
            quantity=quantity,
            price=100,
            market="cn",
            currency="CNY",
        )
        return account_id

    def test_preview_is_read_only_and_describes_buy_delta(self) -> None:
        account_id = self._seed_position()

        preview = self.service.preview_position_adjustment(
            account_id=account_id,
            symbol="600519",
            target_quantity=15,
            trade_date=date(2026, 1, 3),
            price=90,
            fee=1,
            tax=0,
            preview_uid="preview-read-only",
        )

        self.assertEqual(preview["current_quantity"], 10.0)
        self.assertEqual(preview["target_quantity"], 15.0)
        self.assertEqual(preview["side"], "buy")
        self.assertEqual(preview["trade_quantity"], 5.0)
        self.assertEqual(preview["cash_change"], -451.0)
        self.assertTrue(preview["requires_event"])
        self.assertEqual(self.service.list_trade_events(account_id=account_id)["total"], 1)
        with self.db.get_session() as session:
            cached_positions = session.execute(
                select(PortfolioPosition).where(PortfolioPosition.account_id == account_id)
            ).scalars().all()
        self.assertEqual(cached_positions, [])

    def test_confirm_writes_one_official_trade_and_replays_target(self) -> None:
        account_id = self._seed_position()
        preview = self.service.preview_position_adjustment(
            account_id=account_id,
            symbol="600519",
            target_quantity=15,
            trade_date=date(2026, 1, 3),
            price=90,
            preview_uid="preview-confirm-buy",
        )

        result = self.service.confirm_position_adjustment(
            account_id=account_id,
            symbol="600519",
            target_quantity=15,
            trade_date=date(2026, 1, 3),
            price=90,
            fee=0,
            tax=0,
            preview_uid=preview["preview_uid"],
            expected_current_quantity=preview["current_quantity"],
        )

        self.assertGreater(result["trade_id"], 0)
        events = self.service.list_trade_events(account_id=account_id, page=1, page_size=20)
        self.assertEqual(events["total"], 2)
        self.assertEqual(events["items"][0]["side"], "buy")
        self.assertEqual(events["items"][0]["quantity"], 5.0)
        self.assertEqual(events["items"][0]["trade_uid"], "pp02-quick:preview-confirm-buy")
        snapshot = self.service.get_portfolio_snapshot(
            account_id=account_id,
            as_of=date(2026, 1, 3),
            include_realtime=False,
        )
        self.assertEqual(snapshot["accounts"][0]["positions"][0]["quantity"], 15.0)

    def test_confirm_rejects_stale_preview_without_writing(self) -> None:
        account_id = self._seed_position()
        preview = self.service.preview_position_adjustment(
            account_id=account_id,
            symbol="600519",
            target_quantity=15,
            trade_date=date(2026, 1, 3),
            price=90,
            preview_uid="preview-stale",
        )
        self.service.record_trade(
            account_id=account_id,
            symbol="600519",
            trade_date=date(2026, 1, 3),
            side="buy",
            quantity=1,
            price=90,
            market="cn",
            currency="CNY",
        )

        with self.assertRaises(PortfolioConflictError):
            self.service.confirm_position_adjustment(
                account_id=account_id,
                symbol="600519",
                target_quantity=15,
                trade_date=date(2026, 1, 3),
                price=90,
                preview_uid=preview["preview_uid"],
                expected_current_quantity=preview["current_quantity"],
            )

        self.assertEqual(self.service.list_trade_events(account_id=account_id)["total"], 2)

    def test_duplicate_confirmation_keeps_official_trade_uid_conflict(self) -> None:
        account_id = self._seed_position()
        preview = self.service.preview_position_adjustment(
            account_id=account_id,
            symbol="600519",
            target_quantity=15,
            trade_date=date(2026, 1, 3),
            price=90,
            preview_uid="preview-duplicate",
        )
        kwargs = {
            "account_id": account_id,
            "symbol": "600519",
            "target_quantity": 15,
            "trade_date": date(2026, 1, 3),
            "price": 90,
            "preview_uid": preview["preview_uid"],
            "expected_current_quantity": preview["current_quantity"],
        }
        self.service.confirm_position_adjustment(**kwargs)

        with self.assertRaises(PortfolioConflictError):
            self.service.confirm_position_adjustment(**kwargs)

        self.assertEqual(self.service.list_trade_events(account_id=account_id)["total"], 2)

    def test_api_requires_preview_then_confirmation(self) -> None:
        account_id = self._seed_position()
        payload = {
            "account_id": account_id,
            "symbol": "600519",
            "target_quantity": 15,
            "trade_date": "2026-01-03",
            "price": 90,
            "fee": 1,
            "tax": 0,
        }

        preview_response = self.client.post(
            "/api/v1/portfolio/positions/quick-adjust/preview",
            json=payload,
        )
        self.assertEqual(preview_response.status_code, 200, preview_response.text)
        preview = preview_response.json()
        self.assertEqual(preview["current_quantity"], 10.0)
        self.assertEqual(
            self.client.get(
                "/api/v1/portfolio/trades",
                params={"account_id": account_id},
            ).json()["total"],
            1,
        )

        confirm_response = self.client.post(
            "/api/v1/portfolio/positions/quick-adjust/confirm",
            json={
                **payload,
                "preview_uid": preview["preview_uid"],
                "expected_current_quantity": preview["current_quantity"],
            },
        )
        self.assertEqual(confirm_response.status_code, 200, confirm_response.text)
        self.assertGreater(confirm_response.json()["trade_id"], 0)
        self.assertEqual(
            self.client.get(
                "/api/v1/portfolio/trades",
                params={"account_id": account_id},
            ).json()["total"],
            2,
        )


if __name__ == "__main__":
    unittest.main()

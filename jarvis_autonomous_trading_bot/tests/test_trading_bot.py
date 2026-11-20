"""Automated tests for JARVIS OS — Autonomous Trading Bot (Paper Only)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from jarvis_autonomous_trading_bot.app import create_app
from jarvis_autonomous_trading_bot.config import TradingBotConfig


class TestAutonomousTradingBot(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp.name) / "paper_trading.db"
        self.config = TradingBotConfig(
            db_path=self.db_path,
            starting_cash_usd=10000.0,
            max_position_pct=25.0,
            max_order_usd=2500.0,
        )
        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_health_ui_and_technical_analysis(self) -> None:
        health = self.client.get("/api/trading-bot/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["mode"], "PAPER_TRADING_ONLY")

        ui = self.client.get("/trading-bot")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("PAPER TRADING ONLY", ui.text)

        ta = self.client.post("/api/trading-bot/analyze", json={"symbol": "BTC-USD", "sample_bars": 120})
        self.assertEqual(ta.status_code, 200)
        body = ta.json()
        self.assertIn(body["signal"], ("BUY", "SELL", "HOLD"))
        self.assertGreaterEqual(body["rsi_14"], 0.0)
        self.assertLessEqual(body["rsi_14"], 100.0)

    def test_backtesting_strategies(self) -> None:
        for strat in ("sma_crossover", "rsi_mean_reversion", "macd_momentum"):
            res = self.client.post(
                "/api/trading-bot/backtest",
                json={"symbol": "ETH-USD", "strategy": strat, "sample_bars": 180},
            )
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["strategy"], strat)
            self.assertEqual(len(body["equity_curve"]), 180)
            self.assertGreater(body["final_equity"], 0.0)

    def test_paper_orders_risk_guardrails_and_estop(self) -> None:
        # 1. Valid BUY within limits ($1000 <= $2500 max order and 10% <= 25% max pos)
        buy = self.client.post(
            "/api/trading-bot/orders",
            json={"symbol": "AAPL", "side": "BUY", "quantity": 5, "price": 200.0},
        )
        self.assertEqual(buy.status_code, 200)
        self.assertEqual(buy.json()["status"], "FILLED")

        # 2. Oversized order rejected by risk manager
        too_big = self.client.post(
            "/api/trading-bot/orders",
            json={"symbol": "AAPL", "side": "BUY", "quantity": 20, "price": 200.0},
        )
        self.assertEqual(too_big.status_code, 200)
        self.assertEqual(too_big.json()["status"], "REJECTED")

        # 3. Engage E-STOP -> blocks even valid SELL orders
        estop = self.client.post("/api/trading-bot/estop", json={"active": True, "reason": "Test E-STOP"})
        self.assertEqual(estop.status_code, 200)
        self.assertTrue(estop.json()["estop_active"])

        blocked = self.client.post(
            "/api/trading-bot/orders",
            json={"symbol": "AAPL", "side": "SELL", "quantity": 2, "price": 220.0},
        )
        self.assertEqual(blocked.json()["status"], "REJECTED")
        self.assertIn("E-STOP", blocked.json()["reason"])

        # 4. Disarm E-STOP -> SELL fills and books realized profit
        self.client.post("/api/trading-bot/estop", json={"active": False, "reason": "Resume"})
        sell = self.client.post(
            "/api/trading-bot/orders",
            json={"symbol": "AAPL", "side": "SELL", "quantity": 5, "price": 220.0},
        )
        self.assertEqual(sell.json()["status"], "FILLED")

        port = self.client.get("/api/trading-bot/portfolio").json()
        self.assertEqual(len(port["positions"]), 0)
        self.assertGreater(port["realized_pnl_usd"], 90.0)


if __name__ == "__main__":
    unittest.main()

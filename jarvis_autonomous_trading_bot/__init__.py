"""JARVIS OS — Autonomous Trading Bot (Additive Feature Module #6, Paper Trading Only).

Simulated paper trading, technical analysis, backtesting engine, and
risk-managed execution models with E-STOP safety guard for Raspberry Pi 5.
"""

from .config import TradingBotConfig
from .router import create_router

__version__ = "1.0.0"
__all__ = ["TradingBotConfig", "create_router", "__version__"]

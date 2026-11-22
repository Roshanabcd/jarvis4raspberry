"""Runnable CLI demonstration for JARVIS Module 28 — AI Data Analyst."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_28_ai_data_analyst.backend.app.config import DataAnalystConfig
from modules.module_28_ai_data_analyst.backend.services.analyst_engine import DataAnalystEngine


def main() -> None:
    sample_csv = """region,revenue,latency_ms
APAC,4200,32
APAC,4800,35
EMEA,3100,41
EMEA,2900,38
NA,6100,29
NA,9800,240
"""
    with tempfile.TemporaryDirectory() as tmp:
        cfg = DataAnalystConfig(db_path=os.path.join(tmp, "demo_m28.db"))
        engine = DataAnalystEngine(config=cfg)

        ds = engine.ingest_csv(name="Regional Q4 Telemetry", csv_text=sample_csv, description="Demo metrics")
        did = ds["dataset_id"]
        agg = engine.aggregate(did, group_by="region", metric="revenue", agg="sum")
        anom = engine.detect_anomalies(did, column="latency_ms", z_threshold=1.8)
        qa = engine.ask_question(did, "What is total revenue by region?")

        print(f"Dataset Created : {did} ({ds['name']}, {ds['row_count']} rows)")
        print(f"Top Region Rev  : {agg['series'][0]}")
        print(f"Latency Outliers: {anom['count']} (mean={anom['mean']}, stdev={anom['stdev']})")
        print(f"NL Q&A Answer   : {qa['answer']}")
        print("\n--- Markdown Report ---\n")
        print(engine.export_markdown_report(did))


if __name__ == "__main__":
    main()

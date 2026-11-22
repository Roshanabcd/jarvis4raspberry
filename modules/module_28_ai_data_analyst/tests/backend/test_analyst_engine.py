"""Unit tests for DataAnalystEngine (Module 28)."""

from __future__ import annotations

import os
import tempfile
import unittest

from modules.module_28_ai_data_analyst.backend.app.config import DataAnalystConfig
from modules.module_28_ai_data_analyst.backend.services.analyst_engine import DataAnalystEngine, DataAnalystError


SAMPLE_CSV = """region,revenue,latency_ms
APAC,4200,32
APAC,4800,35
EMEA,3100,41
EMEA,2900,38
NA,6100,29
NA,9800,240
"""


class TestDataAnalystEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = DataAnalystConfig(db_path=os.path.join(self._tmp.name, "test_m28.db"))
        self.engine = DataAnalystEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_csv_profile_aggregate_anomaly_and_report(self) -> None:
        ds = self.engine.ingest_csv("Q4 Metrics", SAMPLE_CSV, description="Regional metrics")
        did = ds["dataset_id"]
        self.assertEqual(ds["row_count"], 6)
        cols = {c["name"]: c for c in ds["profile"]["columns"]}
        self.assertEqual(cols["region"]["dtype"], "categorical")
        self.assertEqual(cols["revenue"]["dtype"], "numeric")
        self.assertEqual(cols["revenue"]["sum"], 30900.0)

        agg = self.engine.aggregate(did, group_by="region", metric="revenue", agg="sum")
        self.assertEqual(agg["series"][0]["label"], "NA")
        self.assertEqual(agg["series"][0]["value"], 15900.0)

        anom = self.engine.detect_anomalies(did, column="latency_ms", z_threshold=1.8)
        self.assertEqual(anom["count"], 1)
        self.assertEqual(anom["anomalies"][0]["value"], 240.0)

        qa = self.engine.ask_question(did, "What is total revenue by region?")
        self.assertIn("NA", qa["answer"])
        self.assertIsNotNone(qa["chart"])

        md = self.engine.export_markdown_report(did)
        self.assertIn("# Data Analysis Report: Q4 Metrics", md)
        self.assertIn("## Column Profile", md)

    def test_unknown_column_raises_400(self) -> None:
        ds = self.engine.ingest_rows("Small", [{"a": 1, "b": "x"}])
        with self.assertRaises(DataAnalystError) as ctx:
            self.engine.aggregate(ds["dataset_id"], group_by="b", metric="missing_col")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_missing_dataset_raises_404(self) -> None:
        with self.assertRaises(DataAnalystError) as ctx:
            self.engine.ask_question("ds_missing", "total revenue")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()

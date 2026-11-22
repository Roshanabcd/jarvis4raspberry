"""AI Data Analyst Engine (Module 28).

Provides real local computation:
- CSV & JSON tabular dataset ingestion
- Automated schema inference & descriptive statistics (min, max, mean, median, stdev, sum)
- Z-score outlier / anomaly detection
- Group-by aggregations (sum, avg, min, max, count) with chart-ready series
- Deterministic natural-language Q&A over datasets
- Shareable Markdown analytical report export
"""

from __future__ import annotations

import csv
import io
import statistics
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from modules.module_28_ai_data_analyst.backend.adapters.insight_adapter import DataInsightAdapter, LocalDataInsightAdapter
from modules.module_28_ai_data_analyst.backend.app.config import DataAnalystConfig
from modules.module_28_ai_data_analyst.backend.models.database import DataAnalystDB, utc_now_iso


class DataAnalystError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _try_float(val: Any) -> Optional[float]:
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


class DataAnalystEngine:
    def __init__(
        self,
        config: Optional[DataAnalystConfig] = None,
        db: Optional[DataAnalystDB] = None,
        adapter: Optional[DataInsightAdapter] = None,
    ) -> None:
        self.config = config or DataAnalystConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or DataAnalystDB(self.config.db_path)
        self.adapter = adapter or LocalDataInsightAdapter()
        self._started_at = time.monotonic()

    def _require_dataset(self, dataset_id: str, include_rows: bool = True) -> Dict[str, Any]:
        ds = self.db.get_dataset(dataset_id, include_rows=include_rows)
        if not ds:
            raise DataAnalystError("DATASET_NOT_FOUND", f"Dataset '{dataset_id}' not found.", 404)
        return ds

    def _profile_rows(self, columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        col_profiles: List[Dict[str, Any]] = []
        for col in columns:
            raw_vals = [r.get(col) for r in rows]
            non_empty = [v for v in raw_vals if v is not None and str(v).strip() != ""]
            missing = len(raw_vals) - len(non_empty)
            nums = [_try_float(v) for v in non_empty]
            valid_nums = [x for x in nums if x is not None]

            if non_empty and len(valid_nums) == len(non_empty):
                stdev = round(statistics.pstdev(valid_nums), 4) if len(valid_nums) > 1 else 0.0
                col_profiles.append(
                    {
                        "name": col,
                        "dtype": "numeric",
                        "missing": missing,
                        "unique": len(set(valid_nums)),
                        "min": round(min(valid_nums), 4),
                        "max": round(max(valid_nums), 4),
                        "mean": round(statistics.mean(valid_nums), 4),
                        "median": round(statistics.median(valid_nums), 4),
                        "stdev": stdev,
                        "sum": round(sum(valid_nums), 4),
                    }
                )
            else:
                freq: Dict[str, int] = {}
                for v in non_empty:
                    k = str(v)
                    freq[k] = freq.get(k, 0) + 1
                top_val = max(freq.items(), key=lambda kv: kv[1])[0] if freq else None
                col_profiles.append(
                    {
                        "name": col,
                        "dtype": "categorical",
                        "missing": missing,
                        "unique": len(freq),
                        "top_value": top_val,
                    }
                )
        return {"row_count": len(rows), "column_count": len(columns), "columns": col_profiles}

    def ingest_csv(self, name: str, csv_text: str, description: str = "") -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        if not reader.fieldnames:
            raise DataAnalystError("INVALID_CSV", "CSV must include a header row.", 400)
        columns = [c.strip() for c in reader.fieldnames if c and c.strip()]
        rows: List[Dict[str, Any]] = []
        for raw_row in reader:
            cleaned = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw_row.items() if k and k.strip()}
            if any(str(v).strip() for v in cleaned.values() if v is not None):
                rows.append(cleaned)
        if not rows:
            raise DataAnalystError("EMPTY_DATASET", "CSV contains no data rows.", 400)
        return self.ingest_rows(name=name, rows=rows, description=description, columns=columns)

    def ingest_rows(
        self,
        name: str,
        rows: List[Dict[str, Any]],
        description: str = "",
        columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not rows:
            raise DataAnalystError("EMPTY_DATASET", "Dataset must contain at least one row.", 400)
        cols = columns or list(rows[0].keys())
        profile = self._profile_rows(cols, rows)
        return self.db.create_dataset(
            {
                "dataset_id": f"ds_{uuid.uuid4().hex[:10]}",
                "name": name.strip(),
                "description": description.strip(),
                "columns": cols,
                "rows": rows,
                "profile": profile,
                "row_count": len(rows),
                "created_at": utc_now_iso(),
            }
        )

    def aggregate(self, dataset_id: str, group_by: str, metric: str, agg: str = "sum") -> Dict[str, Any]:
        ds = self._require_dataset(dataset_id, include_rows=True)
        if group_by not in ds["columns"]:
            raise DataAnalystError("UNKNOWN_COLUMN", f"Column '{group_by}' not found.", 400)
        if metric not in ds["columns"]:
            raise DataAnalystError("UNKNOWN_COLUMN", f"Column '{metric}' not found.", 400)

        buckets: Dict[str, List[float]] = {}
        for row in ds["rows"]:
            key = str(row.get(group_by, "Unknown"))
            val = _try_float(row.get(metric))
            if agg == "count":
                buckets.setdefault(key, []).append(1.0)
            elif val is not None:
                buckets.setdefault(key, []).append(val)

        series: List[Dict[str, Any]] = []
        for k, vals in buckets.items():
            if not vals:
                continue
            if agg == "sum":
                v = sum(vals)
            elif agg == "avg":
                v = statistics.mean(vals)
            elif agg == "min":
                v = min(vals)
            elif agg == "max":
                v = max(vals)
            else:
                v = float(len(vals))
            series.append({"label": k, "value": round(v, 4), "count": len(vals)})

        series.sort(key=lambda item: item["value"], reverse=True)
        return {
            "dataset_id": dataset_id,
            "group_by": group_by,
            "metric": metric,
            "agg": agg,
            "series": series,
        }

    def detect_anomalies(self, dataset_id: str, column: str, z_threshold: float = 2.0) -> Dict[str, Any]:
        ds = self._require_dataset(dataset_id, include_rows=True)
        if column not in ds["columns"]:
            raise DataAnalystError("UNKNOWN_COLUMN", f"Column '{column}' not found.", 400)

        indexed: List[Tuple[int, float, Dict[str, Any]]] = []
        for idx, row in enumerate(ds["rows"]):
            num = _try_float(row.get(column))
            if num is not None:
                indexed.append((idx, num, row))
        if len(indexed) < 2:
            return {"dataset_id": dataset_id, "column": column, "z_threshold": z_threshold, "anomalies": [], "count": 0}

        vals = [x[1] for x in indexed]
        mean = statistics.mean(vals)
        stdev = statistics.pstdev(vals)
        anomalies: List[Dict[str, Any]] = []
        if stdev > 0:
            for idx, num, row in indexed:
                z = (num - mean) / stdev
                if abs(z) >= z_threshold:
                    anomalies.append(
                        {"row_index": idx, "value": num, "z_score": round(z, 3), "row": row}
                    )
        return {
            "dataset_id": dataset_id,
            "column": column,
            "mean": round(mean, 4),
            "stdev": round(stdev, 4),
            "z_threshold": z_threshold,
            "anomalies": anomalies,
            "count": len(anomalies),
        }

    def ask_question(self, dataset_id: str, question: str) -> Dict[str, Any]:
        ds = self._require_dataset(dataset_id, include_rows=True)
        q_low = question.lower()
        num_cols = [c for c in ds["profile"]["columns"] if c["dtype"] == "numeric"]
        cat_cols = [c for c in ds["profile"]["columns"] if c["dtype"] == "categorical"]

        matched_num = next((c["name"] for c in num_cols if c["name"].lower() in q_low), num_cols[0]["name"] if num_cols else None)
        matched_cat = next((c["name"] for c in cat_cols if c["name"].lower() in q_low), cat_cols[0]["name"] if cat_cols else None)

        chart: Optional[Dict[str, Any]] = None
        if "outlier" in q_low or "anomal" in q_low:
            if not matched_num:
                answer = "No numeric columns available for anomaly detection."
            else:
                res = self.detect_anomalies(dataset_id, matched_num, z_threshold=1.8)
                answer = f"Found {res['count']} anomaly candidate(s) in '{matched_num}' (mean={res.get('mean')}, stdev={res.get('stdev')})."
        elif matched_num and matched_cat and ("by " in q_low or "per " in q_low or "group" in q_low or "top" in q_low):
            agg = "avg" if ("average" in q_low or "avg" in q_low or "mean" in q_low) else "sum"
            res = self.aggregate(dataset_id, matched_cat, matched_num, agg=agg)
            top = res["series"][0] if res["series"] else None
            answer = (
                f"Computed {agg}({matched_num}) by {matched_cat}: top group is '{top['label']}' ({top['value']})."
                if top
                else "No grouped records matched."
            )
            chart = {"title": f"{agg.upper()}({matched_num}) by {matched_cat}", "series": res["series"][:8]}
        elif matched_num:
            col_stat = next(c for c in num_cols if c["name"] == matched_num)
            answer = (
                f"Column '{matched_num}' summary across {ds['row_count']} rows: "
                f"sum={col_stat['sum']}, mean={col_stat['mean']}, median={col_stat['median']}, "
                f"min={col_stat['min']}, max={col_stat['max']}."
            )
        else:
            answer = f"Dataset '{ds['name']}' has {ds['row_count']} rows and {len(ds['columns'])} columns."

        rec = {
            "query_id": f"qry_{uuid.uuid4().hex[:10]}",
            "dataset_id": dataset_id,
            "question": question.strip(),
            "answer": answer,
            "chart": chart,
            "simulated_narrative": self.adapter.is_simulated,
            "created_at": utc_now_iso(),
        }
        self.db.add_query(rec)
        return rec

    def export_markdown_report(self, dataset_id: str) -> str:
        ds = self._require_dataset(dataset_id, include_rows=True)
        num_cols = [c["name"] for c in ds["profile"]["columns"] if c["dtype"] == "numeric"]
        anomalies = self.detect_anomalies(dataset_id, num_cols[0])["anomalies"] if num_cols else []
        narrative = self.adapter.synthesize_narrative(ds["name"], ds["profile"], anomalies)

        lines = [
            f"# Data Analysis Report: {ds['name']}",
            f"- **Dataset ID**: `{ds['dataset_id']}`",
            f"- **Rows**: {ds['row_count']} | **Columns**: {len(ds['columns'])}",
            f"- **Description**: {ds['description'] or 'N/A'}",
            "",
            "## Executive Narrative",
            narrative,
            "",
            "## Column Profile",
            "| Column | Type | Missing | Unique | Summary |",
            "| :--- | :--- | ---: | ---: | :--- |",
        ]
        for c in ds["profile"]["columns"]:
            if c["dtype"] == "numeric":
                summ = f"min={c['min']}, mean={c['mean']}, median={c['median']}, max={c['max']}"
            else:
                summ = f"top='{c.get('top_value')}'"
            lines.append(f"| {c['name']} | {c['dtype']} | {c['missing']} | {c['unique']} | {summ} |")
        return "\n".join(lines) + "\n"

    def get_status(self) -> Dict[str, Any]:
        datasets = self.db.list_datasets()
        queries = self.db.list_queries()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "datasets_count": len(datasets),
            "total_rows_indexed": sum(d["row_count"] for d in datasets),
            "queries_count": len(queries),
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }

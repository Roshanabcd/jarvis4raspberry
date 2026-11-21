"""Runnable CLI demo for JARVIS Module 35 — Visual Workflow Builder."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.module_35_visual_workflow_builder.backend.app.config import WorkflowConfig
from modules.module_35_visual_workflow_builder.backend.services.workflow_engine import WorkflowEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = WorkflowConfig(db_path=str(Path(tmp) / "demo_workflows.db"))
        engine = WorkflowEngine(config=cfg)

        wf = engine.create_workflow(
            {
                "name": "Invoice Discount & Alert",
                "description": "Compute discounted total and emit notice if over threshold",
                "nodes": [
                    {"node_id": "start", "node_type": "trigger", "label": "Incoming Order", "x": 80, "y": 120, "config": {}},
                    {
                        "node_id": "calc",
                        "node_type": "math",
                        "label": "Apply 10% Off",
                        "x": 260,
                        "y": 120,
                        "config": {"operation": "mul", "a_key": "subtotal", "b": 0.9, "output_key": "total"},
                    },
                    {
                        "node_id": "check",
                        "node_type": "condition",
                        "label": "Total >= 100",
                        "x": 440,
                        "y": 120,
                        "config": {"input_key": "total", "operator": ">=", "value": 100},
                    },
                    {
                        "node_id": "alert",
                        "node_type": "notify",
                        "label": "High Value Order",
                        "x": 620,
                        "y": 120,
                        "config": {"message": "Approved high-value total: {total}"},
                    },
                ],
                "edges": [
                    {"source": "start", "target": "calc"},
                    {"source": "calc", "target": "check"},
                    {"source": "check", "target": "alert"},
                ],
            }
        )

        run_pass = engine.execute_workflow(wf["workflow_id"], {"subtotal": 200.0})
        run_skip = engine.execute_workflow(wf["workflow_id"], {"subtotal": 50.0})

        print(
            json.dumps(
                {
                    "simulated": engine.is_simulated,
                    "execution_order": wf["execution_order"],
                    "high_value_notifications": run_pass["final_context"].get("_notifications", []),
                    "low_value_alert_status": run_skip["trace"][-1]["status"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

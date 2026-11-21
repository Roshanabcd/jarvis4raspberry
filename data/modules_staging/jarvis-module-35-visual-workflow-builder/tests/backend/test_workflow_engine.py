"""Unit tests for Module 35 WorkflowEngine (DAG validation, cycle detection & topological execution)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.config import WorkflowConfig
from backend.services.workflow_engine import WorkflowEngine, WorkflowError


def _sample_nodes():
    return [
        {"node_id": "n1", "node_type": "trigger", "label": "Start", "x": 40, "y": 80, "config": {}},
        {
            "node_id": "n2",
            "node_type": "math",
            "label": "Double Load",
            "x": 220,
            "y": 80,
            "config": {"operation": "mul", "a_key": "load", "b": 2, "output_key": "scaled"},
        },
        {
            "node_id": "n3",
            "node_type": "condition",
            "label": "Check Threshold",
            "x": 400,
            "y": 80,
            "config": {"input_key": "scaled", "operator": ">=", "value": 80},
        },
        {
            "node_id": "n4",
            "node_type": "transform",
            "label": "Format Alert",
            "x": 580,
            "y": 80,
            "config": {"operation": "template", "template": "HIGH_LOAD:{scaled}", "output_key": "alert_text"},
        },
        {
            "node_id": "n5",
            "node_type": "notify",
            "label": "Dispatch Alert",
            "x": 760,
            "y": 80,
            "config": {"message": "Alert -> {alert_text}"},
        },
    ]


def _sample_edges():
    return [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"},
        {"source": "n4", "target": "n5"},
    ]


class TestWorkflowEngine(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        cfg = WorkflowConfig(db_path=str(Path(self._tmp.name) / "workflows.db"))
        self.engine = WorkflowEngine(config=cfg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_validate_dag_rejects_cycles_and_invalid_edges(self) -> None:
        cyclic_nodes = [
            {"node_id": "a", "node_type": "trigger", "label": "A", "config": {}},
            {"node_id": "b", "node_type": "transform", "label": "B", "config": {}},
        ]
        cyclic_edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "a"}]
        with self.assertRaises(WorkflowError) as ctx:
            self.engine.validate_dag(cyclic_nodes, cyclic_edges)
        self.assertEqual(ctx.exception.code, "WORKFLOW_CYCLE_DETECTED")
        self.assertEqual(ctx.exception.status_code, 422)

        with self.assertRaises(WorkflowError) as ctx2:
            self.engine.validate_dag(cyclic_nodes, [{"source": "a", "target": "missing"}])
        self.assertEqual(ctx2.exception.code, "INVALID_EDGE_REFERENCE")
        self.assertEqual(ctx2.exception.status_code, 422)

        dup_nodes = [
            {"node_id": "a", "node_type": "trigger", "label": "A1", "config": {}},
            {"node_id": "a", "node_type": "notify", "label": "A2", "config": {}},
        ]
        with self.assertRaises(WorkflowError) as ctx3:
            self.engine.validate_dag(dup_nodes, [])
        self.assertEqual(ctx3.exception.code, "DUPLICATE_NODE_ID")
        self.assertEqual(ctx3.exception.status_code, 422)

    def test_topological_execution_completes_all_nodes_when_condition_passes(self) -> None:
        wf = self.engine.create_workflow(
            {
                "name": "CPU Guard Pipeline",
                "description": "Triggers alert when scaled load >= 80",
                "nodes": _sample_nodes(),
                "edges": _sample_edges(),
            }
        )
        self.assertEqual(wf["execution_order"], ["n1", "n2", "n3", "n4", "n5"])

        run = self.engine.execute_workflow(wf["workflow_id"], {"load": 50})
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["final_context"]["scaled"], 100.0)
        self.assertEqual(run["final_context"]["alert_text"], "HIGH_LOAD:100.0")
        self.assertEqual(run["final_context"]["_notifications"], ["Alert -> HIGH_LOAD:100.0"])
        self.assertTrue(all(step["status"] == "completed" for step in run["trace"]))

    def test_conditional_branch_skips_downstream_nodes_when_false(self) -> None:
        wf = self.engine.create_workflow(
            {
                "name": "Low Load Check",
                "description": "Skips alert when scaled load < 80",
                "nodes": _sample_nodes(),
                "edges": _sample_edges(),
            }
        )
        run = self.engine.execute_workflow(wf["workflow_id"], {"load": 20})
        statuses = {step["node_id"]: step["status"] for step in run["trace"]}
        self.assertEqual(statuses["n1"], "completed")
        self.assertEqual(statuses["n2"], "completed")
        self.assertEqual(statuses["n3"], "completed")
        self.assertEqual(statuses["n4"], "skipped")
        self.assertEqual(statuses["n5"], "skipped")
        self.assertNotIn("_notifications", run["final_context"])
        self.assertFalse(self.engine.get_status()["simulated"])


if __name__ == "__main__":
    unittest.main()

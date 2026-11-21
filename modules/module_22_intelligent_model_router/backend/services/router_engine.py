"""Intelligent AI Model Router Engine (Module 22).

Provides:
- Automatic prompt task classification (coding, reasoning, summarization, vision, general)
- Explainable multi-factor candidate scoring across strategies (balanced, cost_optimized,
  latency_optimized, quality_first, local_only)
- Automatic failover & circuit breaker protection on provider failures
- Daily USD budget guardrails with automatic local-model downgrade
- Deterministic SHA-256 response caching & side-by-side model benchmarking
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional

from modules.module_22_intelligent_model_router.backend.adapters.provider_adapter import (
    ModelProviderAdapter,
    ProviderInvocationError,
    SimulatedModelProviderAdapter,
)
from modules.module_22_intelligent_model_router.backend.app.config import ModelRouterConfig
from modules.module_22_intelligent_model_router.backend.models.database import ModelRouterDB, utc_now_iso

DEFAULT_MODELS: List[Dict[str, Any]] = [
    {
        "model_id": "local-llama3-8b",
        "provider": "ollama_local",
        "display_name": "Llama 3 8B (Local)",
        "capabilities": ["general", "summarization", "fast"],
        "cost_per_1k_input_usd": 0.0,
        "cost_per_1k_output_usd": 0.0,
        "avg_latency_ms": 240,
        "quality_score": 0.78,
        "max_context_tokens": 8192,
        "privacy_tier": "local",
    },
    {
        "model_id": "local-qwen25-coder",
        "provider": "ollama_local",
        "display_name": "Qwen 2.5 Coder 7B (Local)",
        "capabilities": ["coding", "general", "reasoning"],
        "cost_per_1k_input_usd": 0.0,
        "cost_per_1k_output_usd": 0.0,
        "avg_latency_ms": 310,
        "quality_score": 0.84,
        "max_context_tokens": 32768,
        "privacy_tier": "local",
    },
    {
        "model_id": "gemini-2.5-flash",
        "provider": "google_gemini",
        "display_name": "Gemini 2.5 Flash",
        "capabilities": ["general", "coding", "summarization", "vision", "fast"],
        "cost_per_1k_input_usd": 0.00015,
        "cost_per_1k_output_usd": 0.00060,
        "avg_latency_ms": 280,
        "quality_score": 0.90,
        "max_context_tokens": 1048576,
        "privacy_tier": "cloud",
    },
    {
        "model_id": "gemini-2.5-pro",
        "provider": "google_gemini",
        "display_name": "Gemini 2.5 Pro",
        "capabilities": ["general", "coding", "reasoning", "summarization", "vision"],
        "cost_per_1k_input_usd": 0.00125,
        "cost_per_1k_output_usd": 0.00500,
        "avg_latency_ms": 680,
        "quality_score": 0.97,
        "max_context_tokens": 1048576,
        "privacy_tier": "cloud",
    },
    {
        "model_id": "gpt-4o-mini",
        "provider": "openai",
        "display_name": "GPT-4o Mini",
        "capabilities": ["general", "coding", "summarization", "vision", "fast"],
        "cost_per_1k_input_usd": 0.00015,
        "cost_per_1k_output_usd": 0.00060,
        "avg_latency_ms": 320,
        "quality_score": 0.88,
        "max_context_tokens": 128000,
        "privacy_tier": "cloud",
    },
    {
        "model_id": "claude-3-7-sonnet",
        "provider": "anthropic",
        "display_name": "Claude 3.7 Sonnet",
        "capabilities": ["general", "coding", "reasoning", "summarization"],
        "cost_per_1k_input_usd": 0.00300,
        "cost_per_1k_output_usd": 0.01500,
        "avg_latency_ms": 740,
        "quality_score": 0.96,
        "max_context_tokens": 200000,
        "privacy_tier": "cloud",
    },
]


class ModelRouterError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def classify_task(prompt: str) -> str:
    p = prompt.lower()
    if any(k in p for k in ("def ", "class ", "python", "typescript", "sql", "refactor", "bug", "regex", "fastapi", "code")):
        return "coding"
    if any(k in p for k in ("image", "screenshot", "diagram", "photo", "ocr", "visual")):
        return "vision"
    if any(k in p for k in ("summarize", "tldr", "tl;dr", "bullet points", "condense", "digest")):
        return "summarization"
    if any(k in p for k in ("prove", "analyze", "architecture", "tradeoff", "compare", "strategy", "reason")):
        return "reasoning"
    return "general"


class IntelligentModelRouterEngine:
    def __init__(
        self,
        config: Optional[ModelRouterConfig] = None,
        db: Optional[ModelRouterDB] = None,
        adapter: Optional[ModelProviderAdapter] = None,
    ) -> None:
        self.config = config or ModelRouterConfig.from_env()
        self.config.ensure_dirs()
        self.db = db or ModelRouterDB(self.config.db_path)
        self.adapter = adapter or SimulatedModelProviderAdapter()
        self._started_at = time.monotonic()

        if not self.db.list_models():
            for m in DEFAULT_MODELS:
                self.db.upsert_model(m)

        raw_pol = self.db.get_policy_raw("budget_policy")
        if raw_pol:
            self.budget_policy: Dict[str, Any] = json.loads(raw_pol)
        else:
            self.budget_policy = {
                "daily_budget_usd": self.config.default_daily_budget_usd,
                "downgrade_to_local_on_cap": True,
                "enable_cache": self.config.enable_cache,
            }
            self.db.set_policy_raw("budget_policy", json.dumps(self.budget_policy))

    # --- Model Registry & Policy ---
    def register_model(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.db.upsert_model(payload)

    def toggle_model(
        self,
        model_id: str,
        *,
        enabled: Optional[bool] = None,
        simulate_outage: Optional[bool] = None,
        reset_circuit: bool = False,
    ) -> Dict[str, Any]:
        if not self.db.get_model(model_id):
            raise ModelRouterError("MODEL_NOT_FOUND", f"Model '{model_id}' not found.", 404)
        updated = self.db.update_model_state(
            model_id,
            enabled=enabled,
            simulate_outage=simulate_outage,
            circuit_state="closed" if reset_circuit else None,
            failure_count=0 if reset_circuit else None,
        )
        return updated  # type: ignore[return-value]

    def update_budget_policy(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in updates.items():
            if k in self.budget_policy and v is not None:
                self.budget_policy[k] = v
        self.db.set_policy_raw("budget_policy", json.dumps(self.budget_policy))
        return dict(self.budget_policy)

    # --- Scoring & Routing ---
    def _score_candidate(self, model: Dict[str, Any], task_type: str, strategy: str) -> Dict[str, Any]:
        cap_match = 1.0 if task_type in model["capabilities"] else 0.45
        quality = float(model["quality_score"])
        # Normalize cost (0.0 -> 1.0 efficiency, 0.015 -> ~0.1)
        blended_cost = float(model["cost_per_1k_input_usd"]) + float(model["cost_per_1k_output_usd"])
        cost_eff = max(0.05, 1.0 - min(blended_cost / 0.02, 0.95))
        # Normalize latency (100ms -> ~0.95, 1000ms -> ~0.2)
        latency_eff = max(0.05, 1.0 - min(float(model["avg_latency_ms"]) / 1200.0, 0.95))
        local_bonus = 0.25 if model["privacy_tier"] == "local" else 0.0

        if strategy == "cost_optimized":
            score = 0.50 * cost_eff + 0.25 * cap_match + 0.15 * quality + 0.10 * latency_eff
        elif strategy == "latency_optimized":
            score = 0.50 * latency_eff + 0.25 * cap_match + 0.15 * quality + 0.10 * cost_eff
        elif strategy == "quality_first":
            score = 0.55 * quality + 0.30 * cap_match + 0.10 * latency_eff + 0.05 * cost_eff
        elif strategy == "local_only":
            score = 0.40 * cap_match + 0.35 * quality + 0.25 * latency_eff + local_bonus
        else:  # balanced
            score = 0.35 * quality + 0.30 * cap_match + 0.20 * cost_eff + 0.15 * latency_eff

        return {
            "model_id": model["model_id"],
            "provider": model["provider"],
            "privacy_tier": model["privacy_tier"],
            "score": round(score, 4),
            "capability_match": cap_match,
            "quality_score": quality,
            "cost_efficiency": round(cost_eff, 3),
            "latency_efficiency": round(latency_eff, 3),
        }

    def route_request(
        self,
        prompt: str,
        *,
        task_type: str = "auto",
        strategy: str = "balanced",
        max_cost_usd: Optional[float] = None,
        require_local: bool = False,
        use_cache: bool = True,
        preferred_model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        resolved_task = classify_task(prompt) if task_type == "auto" else task_type
        spend = self.db.get_spend_summary()
        budget_cap = float(self.budget_policy.get("daily_budget_usd", 5.0))
        budget_exceeded = spend["total_cost_usd"] >= budget_cap
        local_enforced = require_local or strategy == "local_only" or (
            budget_exceeded and bool(self.budget_policy.get("downgrade_to_local_on_cap", True))
        )

        # Deterministic response cache lookup
        cache_enabled = bool(self.budget_policy.get("enable_cache", True)) and use_cache
        cache_key = hashlib.sha256(
            f"{resolved_task}|{strategy}|{local_enforced}|{preferred_model_id or ''}|{prompt}".encode("utf-8")
        ).hexdigest()

        if cache_enabled:
            cached = self.db.get_cached_response(cache_key)
            if cached:
                req_id = f"rt_{uuid.uuid4().hex[:10]}"
                decision = {
                    "resolved_task_type": resolved_task,
                    "strategy": strategy,
                    "local_enforced": local_enforced,
                    "budget_exceeded": budget_exceeded,
                    "cache_hit": True,
                    "ranked_candidates": [],
                }
                self.db.record_routing_log(
                    {
                        "request_id": req_id,
                        "task_type": resolved_task,
                        "strategy": strategy,
                        "selected_model_id": cached["model_id"],
                        "failover_used": False,
                        "cache_hit": True,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost_usd": 0.0,
                        "latency_ms": 2,
                        "status": "completed",
                        "decision": decision,
                        "created_at": utc_now_iso(),
                    }
                )
                return {
                    "request_id": req_id,
                    "simulated": self.adapter.is_simulated,
                    "selected_model_id": cached["model_id"],
                    "response_text": cached["response_text"],
                    "cache_hit": True,
                    "failover_used": False,
                    "cost_usd": 0.0,
                    "latency_ms": 2,
                    "routing_decision": decision,
                }

        all_models = self.db.list_models()
        candidates: List[Dict[str, Any]] = []
        for m in all_models:
            if not m["enabled"] or m["circuit_state"] == "open":
                continue
            if local_enforced and m["privacy_tier"] != "local":
                continue
            if max_cost_usd is not None:
                est_blended = float(m["cost_per_1k_input_usd"]) + float(m["cost_per_1k_output_usd"])
                if est_blended > max_cost_usd:
                    continue
            candidates.append(m)

        if not candidates:
            raise ModelRouterError(
                "NO_ELIGIBLE_MODELS",
                "No enabled, healthy models satisfy the current routing, privacy, or budget constraints.",
                503,
                {"local_enforced": local_enforced, "budget_exceeded": budget_exceeded},
            )

        scored = [self._score_candidate(m, resolved_task, strategy) for m in candidates]
        if preferred_model_id:
            for s in scored:
                if s["model_id"] == preferred_model_id:
                    s["score"] = round(s["score"] + 1.0, 4)
        scored.sort(key=lambda x: x["score"], reverse=True)
        model_map = {m["model_id"]: m for m in candidates}

        attempts: List[Dict[str, Any]] = []
        selected_result: Optional[Dict[str, Any]] = None
        failover_used = False

        for idx, cand in enumerate(scored):
            m = model_map[cand["model_id"]]
            try:
                res = self.adapter.invoke(m, prompt, resolved_task)
                if m["failure_count"] > 0:
                    self.db.update_model_state(m["model_id"], failure_count=0, circuit_state="closed")
                attempts.append({"model_id": m["model_id"], "status": "ok"})
                selected_result = res
                failover_used = idx > 0
                break
            except ProviderInvocationError as exc:
                new_failures = int(m["failure_count"]) + 1
                new_cb = "open" if new_failures >= self.config.circuit_breaker_threshold else "closed"
                self.db.update_model_state(m["model_id"], failure_count=new_failures, circuit_state=new_cb)
                attempts.append({"model_id": m["model_id"], "status": "failed", "error": str(exc), "circuit_state": new_cb})

        if selected_result is None:
            raise ModelRouterError(
                "ALL_CANDIDATES_FAILED",
                "All eligible model candidates failed during routing and failover.",
                502,
                {"attempts": attempts},
            )

        req_id = f"rt_{uuid.uuid4().hex[:10]}"
        decision = {
            "resolved_task_type": resolved_task,
            "strategy": strategy,
            "local_enforced": local_enforced,
            "budget_exceeded": budget_exceeded,
            "cache_hit": False,
            "attempts": attempts,
            "ranked_candidates": scored[:4],
        }
        self.db.record_routing_log(
            {
                "request_id": req_id,
                "task_type": resolved_task,
                "strategy": strategy,
                "selected_model_id": selected_result["model_id"],
                "failover_used": failover_used,
                "cache_hit": False,
                "input_tokens": selected_result["input_tokens"],
                "output_tokens": selected_result["output_tokens"],
                "cost_usd": selected_result["cost_usd"],
                "latency_ms": selected_result["latency_ms"],
                "status": "completed",
                "decision": decision,
                "created_at": utc_now_iso(),
            }
        )
        if cache_enabled:
            self.db.set_cached_response(cache_key, selected_result["model_id"], selected_result["response_text"], resolved_task)

        return {
            "request_id": req_id,
            "simulated": selected_result["simulated"],
            "selected_model_id": selected_result["model_id"],
            "provider": selected_result["provider"],
            "response_text": selected_result["response_text"],
            "input_tokens": selected_result["input_tokens"],
            "output_tokens": selected_result["output_tokens"],
            "cost_usd": selected_result["cost_usd"],
            "latency_ms": selected_result["latency_ms"],
            "cache_hit": False,
            "failover_used": failover_used,
            "routing_decision": decision,
        }

    def run_benchmark(self, prompt: str, model_ids: List[str], task_type: str = "auto") -> Dict[str, Any]:
        resolved_task = classify_task(prompt) if task_type == "auto" else task_type
        results: List[Dict[str, Any]] = []
        for mid in model_ids:
            m = self.db.get_model(mid)
            if not m:
                results.append({"model_id": mid, "status": "not_found"})
                continue
            try:
                out = self.adapter.invoke(m, prompt, resolved_task)
                results.append({"model_id": mid, "status": "ok", **out})
            except ProviderInvocationError as exc:
                results.append({"model_id": mid, "status": "failed", "error": str(exc)})
        return {"task_type": resolved_task, "simulated": self.adapter.is_simulated, "results": results}

    def get_status(self) -> Dict[str, Any]:
        models = self.db.list_models()
        spend = self.db.get_spend_summary()
        return {
            "adapter": self.adapter.adapter_name,
            "simulated": self.adapter.is_simulated,
            "models_total": len(models),
            "models_healthy": sum(1 for m in models if m["enabled"] and m["circuit_state"] == "closed"),
            "budget_policy": self.budget_policy,
            "spend": spend,
            "uptime_seconds": round(time.monotonic() - self._started_at, 2),
        }

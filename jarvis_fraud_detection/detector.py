"""Statistical anomaly detection + security heuristic scorer for transactions, auth logs, and audit entries."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .config import FraudDetectionConfig

SENSITIVE_AUDIT_KEYWORDS = (
    "disable_mfa",
    "delete_logs",
    "grant_admin",
    "role_change",
    "privilege_escalation",
    "bulk_export",
    "bypass_estop",
    "export_secrets",
    "sudo_nopasswd",
)


def parse_event_time(ts: Optional[str]) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    cleaned = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def score_security_event(
    event: Dict[str, Any],
    actor_history: List[Dict[str, Any]],
    config: FraudDetectionConfig,
) -> Tuple[float, str, str, List[Dict[str, Any]]]:
    """Return (risk_score 0..100, severity, decision, triggered_signals)."""
    signals: List[Dict[str, Any]] = []
    score = 0.0

    stream = event["stream_type"]
    action = str(event["action"]).lower()
    status = str(event["status"]).lower()
    amount = event.get("amount")
    geo = (event.get("geo_country") or "").strip().upper()
    device = (event.get("device_id") or "").strip()
    ip_addr = (event.get("ip_address") or "").strip()
    ev_dt = parse_event_time(event.get("event_time"))

    # Common contextual baselines from actor history
    prior_geos = {(h.get("geo_country") or "").strip().upper() for h in actor_history if h.get("geo_country")}
    prior_devices = {(h.get("device_id") or "").strip() for h in actor_history if h.get("device_id")}
    prior_ips = {(h.get("ip_address") or "").strip() for h in actor_history if h.get("ip_address")}

    # Velocity within sliding window
    recent_in_window = 0
    for h in actor_history:
        h_dt = parse_event_time(h.get("event_time"))
        delta_min = abs((ev_dt - h_dt).total_seconds()) / 60.0
        if delta_min <= config.velocity_window_minutes:
            recent_in_window += 1

    if geo and prior_geos and geo not in prior_geos:
        w = 24.0
        score += w
        signals.append(
            {
                "code": "NEW_GEO_LOCATION",
                "weight": w,
                "detail": f"Unseen country '{geo}' (prior baseline: {sorted(prior_geos)[:3]}).",
            }
        )

    if device and prior_devices and device not in prior_devices:
        w = 16.0
        score += w
        signals.append(
            {
                "code": "NEW_DEVICE_ID",
                "weight": w,
                "detail": f"Unrecognized device '{device}' for actor '{event['actor_id']}'.",
            }
        )

    # Stream-specific anomaly rules
    if stream == "transaction":
        tx_amounts = [
            float(h["amount"])
            for h in actor_history
            if h.get("stream_type") == "transaction" and h.get("amount") is not None
        ]
        if amount is not None:
            if len(tx_amounts) >= 3:
                mean_a = sum(tx_amounts) / len(tx_amounts)
                var_a = sum((x - mean_a) ** 2 for x in tx_amounts) / len(tx_amounts)
                std_a = math.sqrt(var_a) if var_a > 1e-9 else max(mean_a * 0.15, 1.0)
                z_score = (amount - mean_a) / std_a
                if z_score >= 3.0:
                    w = min(48.0, 26.0 + (z_score - 3.0) * 6.0)
                    score += w
                    signals.append(
                        {
                            "code": "AMOUNT_ZSCORE_SPIKE",
                            "weight": round(w, 1),
                            "detail": f"Amount {amount:.2f} is {z_score:.1f}σ above actor mean ({mean_a:.2f}).",
                        }
                    )
            elif amount >= config.high_amount_baseline:
                w = 30.0
                score += w
                signals.append(
                    {
                        "code": "HIGH_VALUE_FIRST_TX",
                        "weight": w,
                        "detail": f"High-value transaction ({amount:.2f}) exceeds baseline ({config.high_amount_baseline:.2f}).",
                    }
                )

        if recent_in_window >= 4:
            w = 22.0
            score += w
            signals.append(
                {
                    "code": "TX_VELOCITY_BURST",
                    "weight": w,
                    "detail": f"{recent_in_window + 1} transactions within {config.velocity_window_minutes} minutes.",
                }
            )

    elif stream == "auth_log":
        recent_failures = sum(
            1
            for h in actor_history[:12]
            if h.get("stream_type") == "auth_log" and str(h.get("status", "")).lower() in {"failed", "denied"}
        )
        if status in {"failed", "denied"} and recent_failures >= 3:
            w = 42.0
            score += w
            signals.append(
                {
                    "code": "BRUTE_FORCE_BURST",
                    "weight": w,
                    "detail": f"{recent_failures + 1} consecutive/recent failed authentication attempts.",
                }
            )
        elif status == "success" and recent_failures >= 3:
            w = 38.0
            score += w
            signals.append(
                {
                    "code": "POST_FAILURE_LOGIN_SUCCESS",
                    "weight": w,
                    "detail": f"Successful login immediately after {recent_failures} failed attempts (possible credential stuffing).",
                }
            )

        if ip_addr and prior_ips and ip_addr not in prior_ips and ev_dt.hour in {0, 1, 2, 3, 4}:
            w = 18.0
            score += w
            signals.append(
                {
                    "code": "OFF_HOURS_NEW_IP",
                    "weight": w,
                    "detail": f"Off-hours authentication ({ev_dt.hour:02d}:00 UTC) from new IP '{ip_addr}'.",
                }
            )

    elif stream == "audit_entry":
        matched_kw = [kw for kw in SENSITIVE_AUDIT_KEYWORDS if kw in action]
        if matched_kw:
            w = 50.0
            score += w
            signals.append(
                {
                    "code": "CRITICAL_AUDIT_ACTION",
                    "weight": w,
                    "detail": f"High-risk administrative action detected: {', '.join(matched_kw)}.",
                }
            )
        if status in {"denied", "failed"}:
            w = 20.0
            score += w
            signals.append(
                {
                    "code": "UNAUTHORIZED_AUDIT_ATTEMPT",
                    "weight": w,
                    "detail": f"Action '{action}' was {status} for actor '{event['actor_id']}'.",
                }
            )
        if recent_in_window >= 6:
            w = 18.0
            score += w
            signals.append(
                {
                    "code": "AUDIT_BURST_ACTIVITY",
                    "weight": w,
                    "detail": f"High audit action velocity ({recent_in_window + 1} events in {config.velocity_window_minutes}m).",
                }
            )

    score = round(max(0.0, min(100.0, score)), 2)

    if score >= config.block_threshold:
        severity = "critical"
        decision = "block"
    elif score >= config.review_threshold:
        severity = "high"
        decision = "review"
    elif score >= 20.0:
        severity = "medium"
        decision = "allow"
    else:
        severity = "low"
        decision = "allow"

    return score, severity, decision, signals

"""Core Fraud Detection service orchestrating event scoring, alert creation, and analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from .config import FraudDetectionConfig
from .detector import score_security_event
from .models import (
    ActorRiskSummary,
    AlertListResponse,
    AlertRecord,
    AlertUpdateRequest,
    AnalyticsSummaryResponse,
    BatchEventsRequest,
    BatchEventsResponse,
    EventListResponse,
    HealthResponse,
    ScoredEventRecord,
    SecurityEventRequest,
    SignalDetail,
    VALID_ALERT_STATUSES,
    VALID_STREAMS,
)
from .storage import FraudStore


class FraudDetectionEngine:
    """Evaluates security events, manages fraud alerts, and computes risk analytics."""

    def __init__(self, config: Optional[FraudDetectionConfig] = None) -> None:
        self.config = config or FraudDetectionConfig()
        self.store = FraudStore(self.config.db_path)

    def health(self) -> HealthResponse:
        s = self.store.summary()
        return HealthResponse(
            total_events=s["total_events"],
            open_alerts=s["open_alerts"],
        )

    def ingest_event(self, req: SecurityEventRequest) -> ScoredEventRecord:
        stream = req.stream_type.strip().lower()
        if stream not in VALID_STREAMS:
            raise ValueError(f"Unsupported stream_type '{stream}'. Choose from: {sorted(VALID_STREAMS)}")

        actor_id = req.actor_id.strip()
        history = self.store.get_actor_history(actor_id=actor_id, limit=100)
        event_time = (req.event_time or datetime.now(timezone.utc).isoformat()).strip()

        payload = {
            "event_time": event_time,
            "stream_type": stream,
            "actor_id": actor_id,
            "action": req.action.strip(),
            "status": req.status.strip().lower(),
            "amount": req.amount,
            "ip_address": req.ip_address.strip() if req.ip_address else None,
            "geo_country": req.geo_country.strip().upper() if req.geo_country else None,
            "device_id": req.device_id.strip() if req.device_id else None,
            "metadata": req.metadata,
        }

        risk_score, severity, decision, signals = score_security_event(
            event=payload,
            actor_history=history,
            config=self.config,
        )
        payload["risk_score"] = risk_score
        payload["severity"] = severity
        payload["decision"] = decision
        payload["signals"] = signals

        create_alert = risk_score >= self.config.review_threshold
        saved = self.store.insert_event_and_optional_alert(payload, create_alert=create_alert)
        saved["signals"] = [SignalDetail(**s) for s in saved["signals"]]
        return ScoredEventRecord(**saved)

    def ingest_batch(self, req: BatchEventsRequest) -> BatchEventsResponse:
        results: List[ScoredEventRecord] = []
        alerts_created = 0
        for ev in req.events:
            rec = self.ingest_event(ev)
            if rec.alert_id is not None:
                alerts_created += 1
            results.append(rec)
        return BatchEventsResponse(
            processed=len(results),
            alerts_created=alerts_created,
            results=results,
        )

    def list_events(self, limit: int = 50, stream_type: Optional[str] = None) -> EventListResponse:
        rows = self.store.list_events(limit=limit, stream_type=stream_type)
        events = []
        for r in rows:
            r["signals"] = [SignalDetail(**s) for s in r["signals"]]
            events.append(ScoredEventRecord(**r))
        return EventListResponse(total=len(events), events=events)

    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> AlertListResponse:
        rows = self.store.list_alerts(status=status, severity=severity, limit=limit)
        alerts = []
        for r in rows:
            r["signals"] = [SignalDetail(**s) for s in r["signals"]]
            alerts.append(AlertRecord(**r))
        return AlertListResponse(total=len(alerts), alerts=alerts)

    def update_alert(self, alert_id: int, req: AlertUpdateRequest) -> AlertRecord:
        st = req.status.strip().lower()
        if st not in VALID_ALERT_STATUSES:
            raise ValueError(f"Invalid alert status '{st}'. Choose from: {sorted(VALID_ALERT_STATUSES)}")
        updated = self.store.update_alert(alert_id=alert_id, status=st, analyst_note=req.analyst_note.strip())
        if updated is None:
            raise KeyError(f"Alert #{alert_id} not found.")
        updated["signals"] = [SignalDetail(**s) for s in updated["signals"]]
        return AlertRecord(**updated)

    def summary(self) -> AnalyticsSummaryResponse:
        s = self.store.summary()
        return AnalyticsSummaryResponse(
            total_events=s["total_events"],
            total_alerts=s["total_alerts"],
            open_alerts=s["open_alerts"],
            by_stream_type=s["by_stream_type"],
            by_severity=s["by_severity"],
            top_risky_actors=[ActorRiskSummary(**a) for a in s["top_risky_actors"]],
        )

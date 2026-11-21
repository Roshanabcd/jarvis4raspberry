"""Shared Event Bus Reference Implementation (Module 42 / JARVIS SDK v1.0.0).

Delivery Semantics: Best-effort in-process async delivery with configurable retries,
dead-letter tracking, and optional persistence callback. Does NOT claim distributed
exactly-once delivery across separate processes.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.contracts import utc_now_iso

EventHandler = Callable[["JarvisEvent"], Awaitable[None]]
PersistCallback = Callable[[Dict[str, Any]], None]


@dataclass
class JarvisEvent:
    event_type: str
    source_module: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    correlation_id: str = field(default_factory=lambda: f"cor_{uuid.uuid4().hex[:10]}")
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "source_module": self.source_module,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class DeliveryReport:
    event_id: str
    event_type: str
    delivered_count: int
    failed_count: int
    failures: List[Dict[str, Any]] = field(default_factory=list)


class EventBus:
    def __init__(
        self,
        max_retries: int = 2,
        retry_delay_seconds: float = 0.02,
        persist_fn: Optional[PersistCallback] = None,
        max_history: int = 500,
    ) -> None:
        self.max_retries = max(0, max_retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        self._persist_fn = persist_fn
        self._max_history = max_history
        self._subscriptions: Dict[str, Dict[str, EventHandler]] = {}
        self._history: List[Dict[str, Any]] = []
        self._dead_letters: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> str:
        sub_id = f"sub_{uuid.uuid4().hex[:10]}"
        self._subscriptions.setdefault(event_type, {})[sub_id] = handler
        return sub_id

    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        subs = self._subscriptions.get(event_type)
        if not subs or subscription_id not in subs:
            return False
        del subs[subscription_id]
        return True

    async def publish(self, event: JarvisEvent) -> DeliveryReport:
        record = event.to_dict()
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]
        if self._persist_fn:
            try:
                self._persist_fn(record)
            except Exception:
                pass

        handlers: List[tuple[str, EventHandler]] = []
        handlers.extend(self._subscriptions.get(event.event_type, {}).items())
        handlers.extend(self._subscriptions.get("*", {}).items())

        delivered = 0
        failures: List[Dict[str, Any]] = []

        for sub_id, handler in handlers:
            last_err: Optional[str] = None
            succeeded = False
            for attempt in range(self.max_retries + 1):
                try:
                    await handler(event)
                    succeeded = True
                    delivered += 1
                    break
                except Exception as exc:
                    last_err = str(exc)
                    if attempt < self.max_retries and self.retry_delay_seconds > 0:
                        await asyncio.sleep(self.retry_delay_seconds)
            if not succeeded:
                failure = {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "subscription_id": sub_id,
                    "attempts": self.max_retries + 1,
                    "error": last_err or "Unknown handler error",
                    "timestamp": utc_now_iso(),
                }
                failures.append(failure)
                self._dead_letters.append(failure)

        return DeliveryReport(
            event_id=event.event_id,
            event_type=event.event_type,
            delivered_count=delivered,
            failed_count=len(failures),
            failures=failures,
        )

    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        items = self._history
        if event_type:
            items = [e for e in items if e["event_type"] == event_type]
        return list(reversed(items[-limit:]))

    def get_dead_letters(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(reversed(self._dead_letters[-limit:]))

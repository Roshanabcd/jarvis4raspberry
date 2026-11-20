"""Lightweight multi-object centroid tracker assigning persistent track IDs and velocity vectors."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class CentroidTracker:
    """Tracks object centroids across consecutive frames per stream."""

    def __init__(self, max_distance: float = 0.18, max_disappeared: int = 12) -> None:
        self.max_distance = max_distance
        self.max_disappeared = max_disappeared
        self._next_id = 1
        # track_id -> {"cx": float, "cy": float, "label": str, "disappeared": int}
        self._tracks: Dict[int, Dict[str, Any]] = {}

    def update(self, raw_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_detections:
            to_drop = []
            for tid, state in self._tracks.items():
                state["disappeared"] += 1
                if state["disappeared"] > self.max_disappeared:
                    to_drop.append(tid)
            for tid in to_drop:
                del self._tracks[tid]
            return []

        assigned_tracks: set[int] = set()
        enriched: List[Dict[str, Any]] = []

        for det in raw_detections:
            cx = (det["x1"] + det["x2"]) / 2.0
            cy = (det["y1"] + det["y2"]) / 2.0
            label = det["label"]

            best_tid = None
            best_dist = self.max_distance
            for tid, state in self._tracks.items():
                if tid in assigned_tracks or state["label"] != label:
                    continue
                dist = math.hypot(cx - state["cx"], cy - state["cy"])
                if dist < best_dist:
                    best_dist = dist
                    best_tid = tid

            if best_tid is not None:
                prev = self._tracks[best_tid]
                vx = round(cx - prev["cx"], 4)
                vy = round(cy - prev["cy"], 4)
                self._tracks[best_tid] = {"cx": cx, "cy": cy, "label": label, "disappeared": 0}
                assigned_tracks.add(best_tid)
                tid = best_tid
            else:
                tid = self._next_id
                self._next_id += 1
                vx, vy = 0.0, 0.0
                self._tracks[tid] = {"cx": cx, "cy": cy, "label": label, "disappeared": 0}
                assigned_tracks.add(tid)

            enriched.append(
                {
                    "track_id": tid,
                    "label": label,
                    "confidence": round(float(det["confidence"]), 4),
                    "x1": round(float(det["x1"]), 4),
                    "y1": round(float(det["y1"]), 4),
                    "x2": round(float(det["x2"]), 4),
                    "y2": round(float(det["y2"]), 4),
                    "centroid_x": round(cx, 4),
                    "centroid_y": round(cy, 4),
                    "velocity_x": vx,
                    "velocity_y": vy,
                }
            )

        # Increment disappeared counter for unmatched existing tracks
        to_drop = []
        for tid, state in self._tracks.items():
            if tid not in assigned_tracks:
                state["disappeared"] += 1
                if state["disappeared"] > self.max_disappeared:
                    to_drop.append(tid)
        for tid in to_drop:
            del self._tracks[tid]

        return enriched

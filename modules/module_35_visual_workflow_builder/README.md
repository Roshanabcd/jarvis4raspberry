# JARVIS OS — Module 35: Visual Workflow Builder (`v1.0.0`)

**Module ID:** `jarvis-module-35-visual-workflow-builder`  
**Default Port:** `8135`  
**UI Route:** `/workflows`  
**API Prefix:** `/api/v1/workflows`  
**WebSocket:** `/api/v1/workflows/ws/runs`

## Overview
JARVIS Module 35 is a **CRITICAL**, local-first **Visual Workflow Builder & DAG Execution Engine (`simulated: false`)**. Design directed acyclic graphs of typed nodes (`trigger`, `transform`, `condition`, `math`, `notify`) with visual `(x, y)` coordinates, validate them using Kahn's topological sort (blocking cycles and dangling edges with `422`), execute pipelines deterministically with conditional branch skipping, and inspect per-node traces in the SVG graph HUD.

## Quickstart
```bash
bash scripts/setup.sh
bash scripts/run.sh
```
Open `http://127.0.0.1:8135/workflows`.

## Testing & Demo
```bash
bash scripts/test.sh
```

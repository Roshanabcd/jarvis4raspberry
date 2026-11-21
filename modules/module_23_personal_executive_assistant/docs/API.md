# API Reference — Module 23: Personal Executive Assistant

Base prefix: `/api/v1/executive-assistant`  
UI route: `/executive-assistant`  
Contract version: `1.0.0`

## Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/executive-assistant/health` | Module health, version, contract version, adapter status |
| `GET` | `/api/v1/executive-assistant/manifest` | Returns `manifest.json` |
| `GET` | `/api/v1/executive-assistant/status` | Counts of goals, open/completed tasks, habits, and open follow-ups |
| `GET` | `/api/v1/executive-assistant/briefing` | Generates the Daily Executive Briefing (optional `?date=YYYY-MM-DD`) |
| `GET` / `POST` | `/api/v1/executive-assistant/goals` | List or create goals/OKRs |
| `PATCH` | `/api/v1/executive-assistant/goals/{goal_id}` | Update goal progress (`0–100%`) and status |
| `GET` / `POST` | `/api/v1/executive-assistant/tasks` | List or create tasks with automatic Eisenhower quadrant tagging |
| `PATCH` | `/api/v1/executive-assistant/tasks/{task_id}` | Update task status (`todo`, `in_progress`, `done`, `deferred`) |
| `GET` / `POST` | `/api/v1/executive-assistant/time-blocks` | List or schedule overlap-checked daily time blocks (`409` on conflict) |
| `POST` | `/api/v1/executive-assistant/plan-day` | Smart Day Auto-Planner placing top unscheduled tasks into open workday slots |
| `GET` / `POST` | `/api/v1/executive-assistant/habits` | List habits with computed streaks or create a new habit |
| `POST` | `/api/v1/executive-assistant/habits/{habit_id}/checkin` | Record a daily check-in and recompute streak |
| `GET` / `POST` | `/api/v1/executive-assistant/followups` | List or create delegation follow-ups |
| `PATCH` | `/api/v1/executive-assistant/followups/{followup_id}` | Update follow-up status (`open`, `completed`, `snoozed`) |
| `WS` | `/api/v1/executive-assistant/ws/events` | Real-time status & heartbeat WebSocket stream |

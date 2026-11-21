# API Reference — JARVIS Module 34: Personal Finance Manager (`v1.0.0`)

**Base URL:** `http://127.0.0.1:8134/api/v1/finance`  
**WebSocket:** `ws://127.0.0.1:8134/api/v1/finance/ws/updates`

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Module health check (`simulated: false`) |
| `GET` | `/manifest` | Returns `manifest.json` |
| `GET` | `/status` | Accounts count, net worth, transactions count, goals count |
| `GET` | `/accounts` | List all accounts and balances |
| `POST` | `/accounts` | Create an account (`checking`, `savings`, `credit`, `cash`, `investment`) |
| `GET` | `/transactions` | List transactions (optional `?month=YYYY-MM&category=<name>`) |
| `POST` | `/transactions` | Record an `income` or `expense` transaction and update account balance |
| `GET` | `/transactions/export.csv` | Download transactions ledger as CSV |
| `POST` | `/budgets` | Create or update a monthly category budget (`YYYY-MM`) |
| `GET` | `/budgets/status` | Evaluate monthly spend vs. budget (`ok`, `warning`, `exceeded`) |
| `GET` | `/goals` | List savings goals with progress % |
| `POST` | `/goals` | Create a savings goal |
| `POST` | `/goals/{goal_id}/contribute` | Add a contribution toward a savings goal |
| `GET` | `/summary` | Monthly net worth, income, expenses, cashflow, savings rate %, and category breakdown |
| `WS` | `/ws/updates` | Real-time connection & heartbeat status stream |

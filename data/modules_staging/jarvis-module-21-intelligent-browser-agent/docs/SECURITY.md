# Security & Policy Model — Module 21: Intelligent Browser Agent

## 1. SSRF & Local Network Protection
Every URL passed to session creation, navigation, or file download is validated before reaching the browser adapter:
- Only `http` and `https` schemes are allowed (`file://`, `javascript:`, `ftp://`, `data:` are rejected with HTTP `403`).
- `localhost`, `*.localhost`, and raw IP addresses in loopback (`127.0.0.0/8`, `::1`), RFC1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local/cloud metadata (`169.254.0.0/16`), multicast, or reserved ranges are blocked unconditionally.

## 2. Domain Allowlist & Denylist Governance
- Default allowlist restricts navigation to local simulated fixtures (`docs.jarvis.local`, `portal.jarvis.local`, `releases.jarvis.local`).
- Blocked domains always take precedence over allowed domains.
- Policy updates are persisted in SQLite (`site_policy`) and logged in `browser_logs`.

## 3. Human-in-the-Loop Form Submission Gates
- `require_approval_for_form_submit` is enabled (`true`) by default.
- Calling `/form/submit` or running a `submit_form` workflow step pauses execution, creates a `pending` record in `submission_approvals`, and waits for explicit operator approval via `/approvals/{id}/decide`.
- Rejecting an approval cancels the submission (and marks any linked workflow `cancelled`).

## 4. Sandboxed Downloads & Audit Trail
- Downloaded filenames are sanitized to safe alphanumeric characters, prefixed with a unique download ID, and constrained inside `JARVIS_M21_DOWNLOAD_DIR` (preventing path traversal).
- Every download records byte size and SHA-256 digest.
- All navigation, policy blocks, form fills, approvals, downloads, and cancellations are recorded in `browser_logs`.

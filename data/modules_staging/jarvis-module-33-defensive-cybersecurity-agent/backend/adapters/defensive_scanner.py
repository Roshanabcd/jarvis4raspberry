"""Real local defensive scanner adapter (simulated=False): secret scanning, SHA-256 FIM, and log anomaly analysis."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any, Dict, List, Tuple

SECRET_RULES: List[Tuple[str, str, re.Pattern[str]]] = [
    ("aws_access_key", "critical", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("openai_api_key", "critical", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_pat", "critical", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("google_api_key", "high", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("private_key_header", "critical", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SSH_FAIL_RE = re.compile(r"Failed password for .*? from ([0-9]{1,3}(?:\.[0-9]{1,3}){3})")
SUDO_FAIL_RE = re.compile(r"sudo:.*?(?:authentication failure|NOT in sudoers)", re.IGNORECASE)
WEB_ATTACK_RE = re.compile(r"(\.\./\.\./|UNION\s+SELECT|<script>|/etc/passwd)", re.IGNORECASE)


def mask_secret(val: str) -> str:
    if len(val) <= 8:
        return "****"
    return f"{val[:4]}...{val[-4:]}"


class LocalDefensiveScanner:
    adapter_name: str = "local_defensive_scanner"
    is_simulated: bool = False

    def scan_directory(self, target_dir: Path, root_dir: Path) -> Tuple[int, List[Dict[str, Any]]]:
        files_scanned = 0
        findings: List[Dict[str, Any]] = []
        for p in sorted(target_dir.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            files_scanned += 1
            rel = p.relative_to(root_dir).as_posix()
            try:
                mode = p.stat().st_mode
                if mode & stat.S_IWOTH:
                    findings.append(
                        {
                            "rule": "world_writable_file",
                            "severity": "medium",
                            "file": rel,
                            "line": 0,
                            "masked_match": oct(stat.S_IMODE(mode)),
                            "remediation": f"Restrict permissions with chmod o-w {rel}.",
                        }
                    )
            except OSError:
                pass

            if p.stat().st_size > 2 * 1024 * 1024:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for lineno, line in enumerate(text.splitlines(), start=1):
                for rule_name, severity, pat in SECRET_RULES:
                    m = pat.search(line)
                    if m:
                        findings.append(
                            {
                                "rule": rule_name,
                                "severity": severity,
                                "file": rel,
                                "line": lineno,
                                "masked_match": mask_secret(m.group(0)),
                                "remediation": "Revoke/rotate credential immediately and move secrets to .env or a secret manager.",
                            }
                        )
        return files_scanned, findings

    def compute_sha256_map(self, target_dir: Path, root_dir: Path) -> Dict[str, str]:
        hashes: Dict[str, str] = {}
        for p in sorted(target_dir.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            hashes[p.relative_to(root_dir).as_posix()] = h.hexdigest()
        return hashes

    def analyze_log_lines(self, source: str, lines: List[str], brute_force_threshold: int = 3) -> List[Dict[str, Any]]:
        anomalies: List[Dict[str, Any]] = []
        ssh_counts: Dict[str, int] = {}

        for idx, line in enumerate(lines, start=1):
            m = SSH_FAIL_RE.search(line)
            if m:
                ip = m.group(1)
                ssh_counts[ip] = ssh_counts.get(ip, 0) + 1
            if SUDO_FAIL_RE.search(line):
                anomalies.append(
                    {
                        "category": "privilege_escalation_attempt",
                        "severity": "high",
                        "title": f"Failed sudo authentication in {source}",
                        "detail": f"Line {idx}: {line[:160]}",
                        "remediation": "Verify user account activity and review /etc/sudoers permissions.",
                    }
                )
            wm = WEB_ATTACK_RE.search(line)
            if wm:
                anomalies.append(
                    {
                        "category": "web_payload_probe",
                        "severity": "high",
                        "title": f"Suspicious web payload ({wm.group(1)}) in {source}",
                        "detail": f"Line {idx}: {line[:160]}",
                        "remediation": "Verify WAF/reverse-proxy rules and ensure parameterized queries and input validation.",
                    }
                )

        for ip, count in ssh_counts.items():
            if count >= brute_force_threshold:
                anomalies.append(
                    {
                        "category": "ssh_brute_force",
                        "severity": "critical",
                        "title": f"SSH brute-force burst from {ip} ({count} failures)",
                        "detail": f"Source {source} recorded {count} failed SSH logins from {ip}.",
                        "remediation": f"Block {ip} via fail2ban/ufw and enforce SSH key-only authentication.",
                    }
                )

        return anomalies

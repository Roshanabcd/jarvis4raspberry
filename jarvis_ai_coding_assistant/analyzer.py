"""Local security & code-quality static analyzer (zero external dependencies)."""

from __future__ import annotations

import ast
import re
from typing import Dict, List, Tuple

from .models import FunctionMetric, StaticFinding

SEVERITY_PENALTY: Dict[str, int] = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
    "INFO": 0,
}

SECRET_PATTERNS: List[Tuple[str, str, str, str]] = [
    (
        "SEC-001",
        "CRITICAL",
        r"""(?i)(api[_-]?key|secret[_-]?key|password|passwd|access[_-]?token|private[_-]?key)\s*=\s*['"][A-Za-z0-9_\-\/+=]{8,}['"]""",
        "Hardcoded credential or API secret detected. Move secrets to environment variables (e.g., os.getenv()).",
    ),
    (
        "SEC-002",
        "CRITICAL",
        r"""(sk-[A-Za-z0-9]{20,}|sk-or-v1-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})""",
        "Known provider API token literal detected in source code. Revoke and load from environment variables.",
    ),
    (
        "SEC-009",
        "MEDIUM",
        r"""verify\s*=\s*False""",
        "TLS/SSL certificate verification is disabled (verify=False). Enable certificate verification.",
    ),
    (
        "SEC-010",
        "LOW",
        r"""['"]0\.0\.0\.0['"]""",
        "Binding to 0.0.0.0 exposes the service on all network interfaces. Prefer 127.0.0.1 unless LAN access is required.",
    ),
]


def _score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _line_snippet(lines: List[str], line_no: int) -> str:
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1].strip()[:140]
    return ""


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Compute McCabe cyclomatic complexity for a function AST node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
                ast.IfExp,
            ),
        ):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(0, len(child.values) - 1)
        elif isinstance(child, ast.comprehension):
            complexity += 1 + len(child.ifs)
    return complexity


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


class StaticCodeAnalyzer:
    """Fast, deterministic security and quality static analyzer for JARVIS workspaces."""

    def analyze(self, code: str, language: str = "python") -> Tuple[int, str, List[StaticFinding], List[FunctionMetric]]:
        lines = code.splitlines()
        findings: List[StaticFinding] = []
        metrics: List[FunctionMetric] = []

        # 1. Multi-language regex security checks
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            for rule_id, severity, pattern, remediation in SECRET_PATTERNS:
                if re.search(pattern, line):
                    findings.append(
                        StaticFinding(
                            rule_id=rule_id,
                            category="security",
                            severity=severity,
                            line=idx,
                            column=0,
                            message=f"Potential security issue matched rule {rule_id}.",
                            snippet=stripped[:140],
                            remediation=remediation,
                        )
                    )

        # 2. Deep Python AST security & quality checks
        if language.lower() in ("python", "py"):
            self._analyze_python_ast(code, lines, findings, metrics)
        elif language.lower() in ("javascript", "typescript", "js", "ts"):
            self._analyze_js_patterns(lines, findings)

        # Deduplicate findings by (rule_id, line)
        seen = set()
        deduped: List[StaticFinding] = []
        for f in findings:
            key = (f.rule_id, f.line)
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        deduped.sort(
            key=lambda f: (
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(f.severity, 5),
                f.line,
            )
        )

        penalty = sum(SEVERITY_PENALTY.get(f.severity, 0) for f in deduped)
        score = max(0, min(100, 100 - penalty))
        return score, _score_to_grade(score), deduped, metrics

    def _analyze_js_patterns(self, lines: List[str], findings: List[StaticFinding]) -> None:
        js_rules = [
            (
                "SEC-JS-001",
                "HIGH",
                r"\beval\s*\(",
                "Avoid eval() in JavaScript/TypeScript due to code injection risks.",
            ),
            (
                "SEC-JS-002",
                "MEDIUM",
                r"\.innerHTML\s*=",
                "Direct innerHTML assignment can introduce XSS; prefer textContent or sanitized DOM nodes.",
            ),
        ]
        for idx, line in enumerate(lines, start=1):
            for rule_id, severity, pattern, remediation in js_rules:
                if re.search(pattern, line):
                    findings.append(
                        StaticFinding(
                            rule_id=rule_id,
                            category="security",
                            severity=severity,
                            line=idx,
                            message=f"Unsafe JS/TS pattern ({rule_id}).",
                            snippet=line.strip()[:140],
                            remediation=remediation,
                        )
                    )

    def _analyze_python_ast(
        self,
        code: str,
        lines: List[str],
        findings: List[StaticFinding],
        metrics: List[FunctionMetric],
    ) -> None:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            findings.append(
                StaticFinding(
                    rule_id="SYN-001",
                    category="syntax",
                    severity="CRITICAL",
                    line=exc.lineno or 1,
                    column=exc.offset or 0,
                    message=f"Python syntax error: {exc.msg}",
                    snippet=_line_snippet(lines, exc.lineno or 1),
                    remediation="Fix the syntax error before running or deploying this module.",
                )
            )
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_call(node, lines, findings)
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append(
                        StaticFinding(
                            rule_id="QUAL-001",
                            category="quality",
                            severity="MEDIUM",
                            line=node.lineno,
                            column=node.col_offset,
                            message="Bare 'except:' catches SystemExit and KeyboardInterrupt.",
                            snippet=_line_snippet(lines, node.lineno),
                            remediation="Catch a specific exception type (e.g., 'except ValueError as exc:').",
                        )
                    )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(node, lines, findings, metrics)

    def _check_call(
        self,
        node: ast.Call,
        lines: List[str],
        findings: List[StaticFinding],
    ) -> None:
        name = _dotted_name(node.func)
        line = getattr(node, "lineno", 1)
        col = getattr(node, "col_offset", 0)
        snip = _line_snippet(lines, line)

        if name in ("eval", "exec"):
            findings.append(
                StaticFinding(
                    rule_id="SEC-003",
                    category="security",
                    severity="CRITICAL",
                    line=line,
                    column=col,
                    message=f"Use of dangerous dynamic execution '{name}()'.",
                    snippet=snip,
                    remediation="Replace eval/exec with ast.literal_eval() or explicit dispatch tables.",
                )
            )
        elif name in ("os.system", "os.popen"):
            findings.append(
                StaticFinding(
                    rule_id="SEC-004",
                    category="security",
                    severity="HIGH",
                    line=line,
                    column=col,
                    message=f"Shell command execution via '{name}()' risks command injection.",
                    snippet=snip,
                    remediation="Use subprocess.run([...], shell=False, check=True) with an argument list.",
                )
            )
        elif name.startswith("subprocess."):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    findings.append(
                        StaticFinding(
                            rule_id="SEC-005",
                            category="security",
                            severity="HIGH",
                            line=line,
                            column=col,
                            message="subprocess call with shell=True enables shell injection.",
                            snippet=snip,
                            remediation="Pass command arguments as a list and set shell=False.",
                        )
                    )
        elif name in ("pickle.loads", "pickle.load", "marshal.loads"):
            findings.append(
                StaticFinding(
                    rule_id="SEC-006",
                    category="security",
                    severity="HIGH",
                    line=line,
                    column=col,
                    message=f"Unsafe deserialization via '{name}()' can execute arbitrary code.",
                    snippet=snip,
                    remediation="Use JSON or Pydantic validation for untrusted data.",
                )
            )
        elif name == "yaml.load":
            has_safe_loader = any(
                kw.arg == "Loader" and "SafeLoader" in _dotted_name(kw.value)
                for kw in node.keywords
            )
            if not has_safe_loader:
                findings.append(
                    StaticFinding(
                        rule_id="SEC-007",
                        category="security",
                        severity="HIGH",
                        line=line,
                        column=col,
                        message="yaml.load() without SafeLoader can instantiate arbitrary Python objects.",
                        snippet=snip,
                        remediation="Use yaml.safe_load() instead.",
                    )
                )
        elif name in ("hashlib.md5", "hashlib.sha1"):
            findings.append(
                StaticFinding(
                    rule_id="SEC-008",
                    category="security",
                    severity="MEDIUM",
                    line=line,
                    column=col,
                    message=f"Weak cryptographic hash '{name}()'.",
                    snippet=snip,
                    remediation="Use hashlib.sha256() or secrets/argon2 for password hashing.",
                )
            )
        elif name.endswith(".execute") and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, (ast.JoinedStr, ast.BinOp)):
                findings.append(
                    StaticFinding(
                        rule_id="SEC-011",
                        category="security",
                        severity="CRITICAL",
                        line=line,
                        column=col,
                        message="Possible SQL injection: dynamically formatted SQL string passed to execute().",
                        snippet=snip,
                        remediation="Use parameterized queries: cursor.execute('SELECT ... WHERE id = ?', (val,)).",
                    )
                )

    def _check_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: List[str],
        findings: List[StaticFinding],
        metrics: List[FunctionMetric],
    ) -> None:
        end_line = getattr(node, "end_lineno", node.lineno) or node.lineno
        length = max(1, end_line - node.lineno + 1)
        complexity = _cyclomatic_complexity(node)

        metrics.append(
            FunctionMetric(
                name=node.name,
                line=node.lineno,
                length_lines=length,
                cyclomatic_complexity=complexity,
                is_async=isinstance(node, ast.AsyncFunctionDef),
            )
        )

        # Mutable default arguments
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                findings.append(
                    StaticFinding(
                        rule_id="QUAL-002",
                        category="quality",
                        severity="MEDIUM",
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Function '{node.name}' uses a mutable default argument (list/dict/set).",
                        snippet=_line_snippet(lines, node.lineno),
                        remediation="Default to None and initialize inside the function body.",
                    )
                )
                break

        if complexity > 10:
            findings.append(
                StaticFinding(
                    rule_id="QUAL-003",
                    category="quality",
                    severity="MEDIUM",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Function '{node.name}' has high cyclomatic complexity ({complexity}).",
                    snippet=_line_snippet(lines, node.lineno),
                    remediation="Split complex branches into smaller, testable helper functions.",
                )
            )

        if length > 60:
            findings.append(
                StaticFinding(
                    rule_id="QUAL-004",
                    category="quality",
                    severity="LOW",
                    line=node.lineno,
                    column=node.col_offset,
                    message=f"Function '{node.name}' is {length} lines long (>60 lines).",
                    snippet=_line_snippet(lines, node.lineno),
                    remediation="Extract cohesive subtasks into dedicated functions.",
                )
            )

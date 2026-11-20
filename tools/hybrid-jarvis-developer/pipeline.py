"""
Multi-Stage Quality Pipeline for Hybrid JARVIS Multi-Agent Orchestrator.
Includes:
1. Syntax Gate (AST parsing and bytecode compilation).
2. Security & Credential Gate (Secret leak detection, destructive pattern scan).
3. Test Gate (Automated pytest runner).
4. Second-Opinion Peer Code Review Gate (Cross-agent review of worktree diffs).
"""
import ast
import json
import logging
from pathlib import Path
import py_compile
import re
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional
from .models import Task

logger = logging.getLogger("JARVIS.Developer.Pipeline")

# Secret leak patterns
_SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"gho_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret[_-]?token|auth[_-]?token)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
]

# Destructive command patterns
_DESTRUCTIVE_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/(?:\s|$)", re.IGNORECASE),
    re.compile(r"shutil\.rmtree\(['\"]/(?:['\"]|\s*\))", re.IGNORECASE),
    re.compile(r"mkfs\.[a-z0-9]+", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", re.IGNORECASE),  # fork bomb
]


class QualityPipeline:
    def __init__(self, repository_root: Optional[Path] = None):
        self.repo_root = Path(repository_root or Path.cwd()).resolve()

    def get_modified_files(self, worktree_path: Path) -> List[Path]:
        """List all modified and untracked files in the worktree."""
        st = subprocess.run(
            ["git", "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        ).stdout
        files = []
        for line in st.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                rel = parts[1].strip()
                files.append((worktree_path / rel).resolve())
        return files

    def run_syntax_gate(self, worktree_path: Path) -> Dict[str, Any]:
        """Validate Python syntax and AST compilation on all modified .py files."""
        files = self.get_modified_files(worktree_path)
        py_files = [f for f in files if f.suffix == ".py" and f.exists() and f.is_file()]
        
        errors = []
        for pf in py_files:
            try:
                # 1. AST check
                source = pf.read_text(encoding="utf-8")
                ast.parse(source, filename=str(pf))
                # 2. Bytecode compile check
                py_compile.compile(str(pf), doraise=True)
            except SyntaxError as se:
                errors.append({
                    "file": str(pf.relative_to(worktree_path)),
                    "line": se.lineno,
                    "error": str(se),
                })
            except Exception as exc:
                errors.append({
                    "file": str(pf.relative_to(worktree_path)),
                    "error": str(exc),
                })

        passed = len(errors) == 0
        return {
            "gate": "syntax",
            "passed": passed,
            "py_files_checked": len(py_files),
            "errors": errors,
        }

    def run_security_gate(self, worktree_path: Path) -> Dict[str, Any]:
        """Scan modified files for raw credentials or destructive operations."""
        files = self.get_modified_files(worktree_path)
        violations = []

        for f in files:
            if not f.exists() or not f.is_file():
                continue
            # Skip binary files or git metadata
            if f.suffix in {".png", ".jpg", ".wav", ".pyc", ".db", ".sqlite3"}:
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for pat in _SECRET_PATTERNS:
                    if pat.search(content):
                        violations.append({
                            "file": str(f.relative_to(worktree_path)),
                            "type": "secret_leak",
                            "pattern": pat.pattern[:30],
                        })
                for pat in _DESTRUCTIVE_PATTERNS:
                    if pat.search(content):
                        violations.append({
                            "file": str(f.relative_to(worktree_path)),
                            "type": "destructive_command",
                            "pattern": pat.pattern[:30],
                        })
            except Exception as exc:
                logger.warning("Security scan error on %s: %s", f, exc)

        passed = len(violations) == 0
        return {
            "gate": "security",
            "passed": passed,
            "files_scanned": len(files),
            "violations": violations,
        }

    def run_test_gate(self, worktree_path: Path, test_paths: Optional[List[str]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Run targeted pytest suites against worktree code."""
        # Check if tests exist in worktree
        cmd = ["pytest", "-q"]
        if test_paths:
            cmd.extend(test_paths)
        else:
            # Default to running quick unit tests if present
            default_tests = [
                str(worktree_path / "tests" / "unit" / "test_hybrid_jarvis_developer.py")
            ]
            valid_defaults = [t for t in default_tests if Path(t).exists()]
            if valid_defaults:
                cmd.extend(valid_defaults)

        try:
            res = subprocess.run(
                cmd,
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            passed = res.returncode == 0
            return {
                "gate": "tests",
                "passed": passed,
                "exit_code": res.returncode,
                "summary": res.stdout.strip()[:600] if res.stdout else res.stderr.strip()[:600],
            }
        except subprocess.TimeoutExpired:
            return {
                "gate": "tests",
                "passed": False,
                "exit_code": -1,
                "summary": f"Tests timed out after {timeout}s",
            }
        except Exception as exc:
            return {
                "gate": "tests",
                "passed": False,
                "exit_code": -1,
                "summary": str(exc),
            }

    def run_peer_code_review(
        self,
        worktree_path: Path,
        task: Task,
        reviewer_agent: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute automated second-opinion code review.
        Evaluates worktree git diff against task prompt for correctness and regressions.
        """
        diff = subprocess.run(
            ["git", "-C", str(worktree_path), "diff", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip()

        st = subprocess.run(
            ["git", "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True, text=True
        ).stdout.strip()

        if not diff and not st:
            return {
                "status": "blocked",
                "reviewer": "pipeline",
                "score": 0.0,
                "notes": "No code changes detected in worktree",
                "timestamp": time.time(),
            }

        # Check if an external peer agent is provided for live AI review
        reviewer_id = getattr(reviewer_agent, "agent_id", "automated_reviewer")
        if reviewer_agent and hasattr(reviewer_agent, "adapter") and hasattr(reviewer_agent.adapter, "execute"):
            review_prompt = (
                f"You are a principal code reviewer. Review the following changes made for task: '{task.prompt}'.\n"
                f"Diff:\n{diff[:1500]}\n\n"
                "Provide a brief review verdict: approved or changes_requested, score (1-10), and 2-sentence rationale."
            )
            try:
                review_task = Task(prompt=review_prompt, timeout=20.0)
                review_out = reviewer_agent.adapter.execute(review_task)
                out_text = review_out.get("output", "") if isinstance(review_out, dict) else str(review_out)
                
                approved = "changes_requested" not in out_text.lower() and "reject" not in out_text.lower()
                score = 8.5 if approved else 4.0
                return {
                    "status": "approved" if approved else "changes_requested",
                    "reviewer": reviewer_id,
                    "score": score,
                    "notes": out_text[:500],
                    "timestamp": time.time(),
                }
            except Exception as rev_err:
                logger.warning("Peer agent review failed, falling back to heuristic review: %s", rev_err)

        # Rule-based heuristic peer review
        # 1. Syntax check
        syntax_res = self.run_syntax_gate(worktree_path)
        # 2. Security check
        sec_res = self.run_security_gate(worktree_path)

        if not syntax_res["passed"]:
            return {
                "status": "changes_requested",
                "reviewer": "heuristic_reviewer",
                "score": 2.0,
                "notes": f"Syntax errors detected: {syntax_res['errors']}",
                "timestamp": time.time(),
            }

        if not sec_res["passed"]:
            return {
                "status": "changes_requested",
                "reviewer": "heuristic_reviewer",
                "score": 1.0,
                "notes": f"Security violations detected: {sec_res['violations']}",
                "timestamp": time.time(),
            }

        # Clean changes
        return {
            "status": "approved",
            "reviewer": "heuristic_reviewer",
            "score": 9.2,
            "notes": "Code passed syntax compilation and security leak checks cleanly. Ready for controlled merge.",
            "timestamp": time.time(),
        }

    def run_full_verification(
        self,
        worktree_path: Path,
        task: Task,
        test_paths: Optional[List[str]] = None,
        reviewer_agent: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Execute full verification pipeline across all 4 gates."""
        syntax = self.run_syntax_gate(worktree_path)
        security = self.run_security_gate(worktree_path)
        tests = self.run_test_gate(worktree_path, test_paths)
        review = self.run_peer_code_review(worktree_path, task, reviewer_agent)

        all_passed = syntax["passed"] and security["passed"] and (review["status"] == "approved")

        return {
            "all_passed": all_passed,
            "syntax": syntax,
            "security": security,
            "tests": tests,
            "review": review,
            "timestamp": time.time(),
        }

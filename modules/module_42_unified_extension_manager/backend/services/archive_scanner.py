"""Safe Module Archive Scanner for JARVIS Module 42.

Inspects ZIP archives strictly in-memory without extracting or executing packaged code.
Enforces safeguards against path traversal, unsafe symlinks, zip bombs (compression ratio
and uncompressed size limits), file count limits, and corrupt ZIP structures.
"""

from __future__ import annotations

import json
import posixpath
import re
import stat
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules.module_42_unified_extension_manager.backend.app.config import ExtensionManagerConfig
from modules.module_42_unified_extension_manager.sdk.jarvis_sdk.contracts import utc_now_iso

MANDATORY_FILES = ["manifest.json", "README.md"]
ENV_KEY_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=")
ROUTE_PREFIX_RE = re.compile(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']')
WS_ROUTE_RE = re.compile(r'@\w+\.websocket\(\s*["\']([^"\']+)["\']')


def _is_unsafe_path(member_name: str) -> Optional[str]:
    if "\x00" in member_name:
        return "Null byte in archive member path"
    normalized = member_name.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return f"Absolute or drive-qualified path rejected: {member_name}"
    parts = [p for p in normalized.split("/") if p]
    if ".." in parts:
        return f"Path traversal ('..') rejected: {member_name}"
    collapsed = posixpath.normpath(normalized)
    if collapsed.startswith("../") or collapsed == "..":
        return f"Normalized path escapes root: {member_name}"
    return None


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def _strip_common_root(paths: List[str]) -> Tuple[str, Dict[str, str]]:
    """Support flat, single-wrapper-dir, and nested archive layouts."""
    file_paths = [p for p in paths if not p.endswith("/")]
    if not file_paths:
        return "", {}
    first_segments = {p.split("/")[0] for p in file_paths if "/" in p}
    has_root_files = any("/" not in p for p in file_paths)
    if not has_root_files and len(first_segments) == 1:
        prefix = next(iter(first_segments)) + "/"
        return prefix, {p: p[len(prefix) :] for p in file_paths}
    return "", {p: p for p in file_paths}


def _read_text_limited(zf: zipfile.ZipFile, member: str, max_bytes: int = 262144) -> str:
    with zf.open(member, "r") as fh:
        raw = fh.read(max_bytes)
    return raw.decode("utf-8", errors="replace")


class ModuleArchiveScanner:
    def __init__(self, config: Optional[ExtensionManagerConfig] = None) -> None:
        self.config = config or ExtensionManagerConfig.from_env()

    def scan_archive(self, archive_path: Path) -> Dict[str, Any]:
        archive_path = Path(archive_path)
        result: Dict[str, Any] = {
            "archive_name": archive_path.name,
            "archive_path": str(archive_path),
            "scanned_at": utc_now_iso(),
            "valid": False,
            "layout_root": "",
            "file_count": 0,
            "compressed_bytes": 0,
            "uncompressed_bytes": 0,
            "security_violations": [],
            "integrity_errors": [],
            "missing_mandatory_files": [],
            "manifest": None,
            "manifest_path": None,
            "backend_entrypoints": [],
            "frontend_entrypoints": [],
            "python_dependencies": [],
            "node_dependencies": {},
            "env_variables": [],
            "test_directories": [],
            "api_docs": [],
            "detected_api_prefixes": [],
            "detected_ws_routes": [],
            "directory_summary": [],
        }

        if not archive_path.is_file():
            result["integrity_errors"].append("Archive file does not exist.")
            return result

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                infos = zf.infolist()
                if len(infos) > self.config.max_archive_files:
                    result["security_violations"].append(
                        f"Archive contains {len(infos)} entries, exceeding max_archive_files={self.config.max_archive_files}."
                    )
                    return result

                total_uncompressed = 0
                total_compressed = 0
                all_names: List[str] = []

                for info in infos:
                    unsafe = _is_unsafe_path(info.filename)
                    if unsafe:
                        result["security_violations"].append(unsafe)
                    if _is_symlink(info):
                        result["security_violations"].append(f"Unsafe symlink entry rejected: {info.filename}")

                    total_uncompressed += info.file_size
                    total_compressed += info.compress_size
                    if info.compress_size > 0 and info.file_size > 65536:
                        ratio = info.file_size / info.compress_size
                        if ratio > self.config.max_compression_ratio:
                            result["security_violations"].append(
                                f"Suspicious compression ratio ({ratio:.1f}x > {self.config.max_compression_ratio}x) in {info.filename}"
                            )
                    all_names.append(info.filename)

                result["file_count"] = sum(1 for i in infos if not i.is_dir())
                result["compressed_bytes"] = total_compressed
                result["uncompressed_bytes"] = total_uncompressed

                if total_uncompressed > self.config.max_uncompressed_bytes:
                    result["security_violations"].append(
                        f"Uncompressed size {total_uncompressed} bytes exceeds limit of {self.config.max_uncompressed_bytes} bytes."
                    )

                if result["security_violations"]:
                    return result

                # Verify ZIP CRC integrity
                corrupt_member = zf.testzip()
                if corrupt_member is not None:
                    result["integrity_errors"].append(f"CRC integrity failure in member: {corrupt_member}")
                    return result

                layout_root, rel_map = _strip_common_root(all_names)
                result["layout_root"] = layout_root
                rel_to_orig = {rel: orig for orig, rel in rel_map.items()}
                rel_paths = sorted(rel_to_orig.keys())

                top_dirs = sorted({p.split("/")[0] for p in rel_paths if "/" in p})
                result["directory_summary"] = top_dirs

                # Locate manifest.json anywhere in archive (prefer shallowest)
                manifest_candidates = sorted(
                    [r for r in rel_paths if posixpath.basename(r) == "manifest.json"],
                    key=lambda p: (p.count("/"), len(p)),
                )
                if manifest_candidates:
                    m_rel = manifest_candidates[0]
                    result["manifest_path"] = m_rel
                    try:
                        result["manifest"] = json.loads(_read_text_limited(zf, rel_to_orig[m_rel]))
                    except json.JSONDecodeError as exc:
                        result["integrity_errors"].append(f"Invalid JSON in {m_rel}: {exc}")
                else:
                    result["missing_mandatory_files"].append("manifest.json")

                # Check README
                if not any(posixpath.basename(r).lower() == "readme.md" for r in rel_paths):
                    result["missing_mandatory_files"].append("README.md")

                # Entrypoints, tests, docs, configs
                env_vars: set[str] = set()
                api_prefixes: set[str] = set()
                ws_routes: set[str] = set()
                test_dirs: set[str] = set()

                for rel in rel_paths:
                    orig = rel_to_orig[rel]
                    base = posixpath.basename(rel)
                    lower = rel.lower()

                    if base in {"main.py", "app.py", "server.py"} and "test" not in lower:
                        result["backend_entrypoints"].append(rel)
                    if base in {"main.tsx", "main.ts", "App.tsx", "index.html"} and ("frontend/" in lower or "static/" in lower or rel == "index.html"):
                        result["frontend_entrypoints"].append(rel)
                    if lower.startswith("tests/") or "/tests/" in lower:
                        parts = rel.split("/")
                        idx = [i for i, seg in enumerate(parts) if seg.lower() == "tests"][0]
                        test_dirs.add("/".join(parts[: idx + 2]) if len(parts) > idx + 2 else "/".join(parts[: idx + 1]))
                    if base.upper() in {"API.MD", "INTEGRATION.MD", "OPENAPI.JSON", "OPENAPI.YAML"}:
                        result["api_docs"].append(rel)

                    if base == "requirements.txt":
                        for line in _read_text_limited(zf, orig).splitlines():
                            cleaned = line.split("#", 1)[0].strip()
                            if cleaned:
                                result["python_dependencies"].append(cleaned)
                    elif base == "package.json":
                        try:
                            pkg = json.loads(_read_text_limited(zf, orig))
                            deps = dict(pkg.get("dependencies") or {})
                            dev_deps = dict(pkg.get("devDependencies") or {})
                            result["node_dependencies"] = {"dependencies": deps, "devDependencies": dev_deps}
                        except json.JSONDecodeError:
                            result["integrity_errors"].append(f"Invalid JSON in {rel}")
                    elif base in {".env.example", ".env.sample"}:
                        for line in _read_text_limited(zf, orig).splitlines():
                            m = ENV_KEY_RE.match(line)
                            if m:
                                env_vars.add(m.group(1))
                    elif rel.endswith(".py") and "test" not in lower and len(api_prefixes) < 20:
                        src = _read_text_limited(zf, orig, max_bytes=65536)
                        for m in ROUTE_PREFIX_RE.finditer(src):
                            api_prefixes.add(m.group(1))
                        for m in WS_ROUTE_RE.finditer(src):
                            ws_routes.add(m.group(1))

                if isinstance(result["manifest"], dict):
                    cfg_schema = result["manifest"].get("configuration_schema") or {}
                    for k in cfg_schema.keys():
                        env_vars.add(str(k))
                    ep = result["manifest"].get("entrypoints") or {}
                    if isinstance(ep, dict):
                        if ep.get("api_prefix"):
                            api_prefixes.add(str(ep["api_prefix"]))
                        if ep.get("ws_endpoint"):
                            ws_routes.add(str(ep["ws_endpoint"]))

                result["env_variables"] = sorted(env_vars)
                result["detected_api_prefixes"] = sorted(api_prefixes)
                result["detected_ws_routes"] = sorted(ws_routes)
                result["test_directories"] = sorted(test_dirs)
                result["valid"] = len(result["integrity_errors"]) == 0 and len(result["security_violations"]) == 0
                return result
        except zipfile.BadZipFile:
            result["integrity_errors"].append("File is not a valid ZIP archive (BadZipFile).")
            return result
        except Exception as exc:
            result["integrity_errors"].append(f"Failed to inspect archive: {exc}")
            return result

    def scan_folder(self, folder_path: str) -> Dict[str, Any]:
        root = Path(folder_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return {
                "folder_path": str(root),
                "exists": False,
                "scanned_at": utc_now_iso(),
                "archive_count": 0,
                "archives": [],
                "error": f"Folder not found or not a directory: {root}",
            }
        zips = sorted(root.glob("*.zip"))
        scanned = [self.scan_archive(z) for z in zips]
        return {
            "folder_path": str(root),
            "exists": True,
            "scanned_at": utc_now_iso(),
            "archive_count": len(scanned),
            "valid_count": sum(1 for a in scanned if a["valid"]),
            "rejected_count": sum(1 for a in scanned if not a["valid"]),
            "archives": scanned,
        }

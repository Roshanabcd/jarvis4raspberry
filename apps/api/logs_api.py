"""JARVIS Logs API — GET /api/logs"""
import os, logging
from fastapi import APIRouter, HTTPException
from tools.shell.command_runner import SecureCommandRunner

logger = logging.getLogger("JARVIS.API.Logs")
logs_router = APIRouter(prefix="/logs", tags=["logs"])
runner = SecureCommandRunner()

@logs_router.get("")
def get_audit_log(lines: int = 100):
    path = os.environ.get("JARVIS_AUDIT_LOG", "jarvis_audit.log")
    if not os.path.exists(path):
        return {"lines": [], "source": path, "error": "Log file not found"}
    try:
        with open(path) as f:
            all_lines = f.readlines()
        return {"lines": all_lines[-lines:], "source": path, "total": len(all_lines)}
    except Exception as e:
        return {"lines": [], "error": str(e)}

@logs_router.get("/service/{service_name}")
def get_service_log(service_name: str, n: int = 50):
    safe_services = {"jarvis-core", "jarvis-voice", "jarvis-api", "jarvis-dashboard", "jarvis-vision"}
    if service_name not in safe_services:
        raise HTTPException(status_code=403, detail="Service not permitted.")
    result = runner.execute("journalctl", ["-u", service_name, "-n", str(n), "--no-pager"])
    return {"service": service_name, "lines": result["stdout"].splitlines(), "error": result.get("error")}

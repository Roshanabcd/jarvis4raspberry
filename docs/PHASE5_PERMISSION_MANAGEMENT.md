# JARVIS OS — Phase 5 Permission Management Specification
## Security Profiles, Hard-Deny Boundaries, Interactive Approval & Audit Logging

---

# 1. Permission Architecture Overview

The **Agent Permission Manager** (`tools/agents/permission_manager.py`) is the centralized policy enforcement point in JARVIS OS. No AI coding agent is permitted direct, unrestricted access to the Linux system. Every filesystem mutation, package installation, and shell execution is audited and vetted against active policy rules.

---

# 2. Operational Profiles

| Profile Name | Safe File Read | Workspace File Edit | External File Edit | Package Install (`pip`/`npm`) | Shell Execution | Destructive Commands |
|---|---|---|---|---|---|---|
| **`SAFE_AUTO`** *(Default)* | **Auto-Approved** | **Auto-Approved** *(with pre-backup)* | **Pending Approval** | **Pending Approval** | **Vetted Auto** *(read/test)* | **HARD DENIED** |
| **`SUPERVISED_AUTO`** | **Auto-Approved** | **Pending Approval** | **Pending Approval** | **Pending Approval** | **Pending Approval** | **HARD DENIED** |
| **`MANUAL`** | **Pending Approval** | **Pending Approval** | **Pending Approval** | **Pending Approval** | **Pending Approval** | **HARD DENIED** |

---

# 3. Bypass-Proof Hard-Deny Boundaries

Certain actions present catastrophic risks to hardware, operating system integrity, or security credentials. These actions are evaluated **first** and are **immediately rejected with status `HARD_DENIED`**, regardless of active profile or user prompt:

1. **Destructive Deletion:**
   - Patterns: `rm -rf /`, `rm -rf ~`, `rm -rf *`, `rm -fr /`
   - Mitigates accidental mass data loss.
2. **Disk Formatting & Partition Destruction:**
   - Patterns: `mkfs`, `fdisk`, `parted`, `sfdisk`, `dd if=... of=/dev/...`
   - Protects NVMe SSD, SD cards, and root partitions.
3. **Privilege Escalation:**
   - Patterns: `sudo su`, `sudo -i`, `sudo bash`, `sudo sh`
   - Prevents AI agents from acquiring uncontained root shells.
4. **Credential & Secret Probing:**
   - Patterns: Reading `.env`, `.env.production`, `.ssh/id_rsa`, `credentials.json`
   - Redacted before reaching agent context.
5. **Microcontroller Firmware Flashing:**
   - Patterns: `esptool`, `avrdude`, `flashrom`, `firmware_flash`
   - Protects ESP32 motor microcontrollers from accidental flashing or bricking.
6. **Robot Actuators & Motor Movement:**
   - Patterns: `robot_arm`, `robot_move`, `servo_set`, `enable_motors`
   - Prevents AI agents from moving physical hardware without explicit human confirmation.
7. **Piping Internet Content to Shell:**
   - Patterns: `curl ... | bash`, `wget ... | sh`

---

# 4. Interactive Approval Workflow

When an operation requires authorization (e.g. installing a new python dependency or modifying files under `SUPERVISED_AUTO` mode):
1. The request is assigned a unique UUID and staged in the `_pending_requests` queue with status `PENDING`.
2. A WebSocket event and REST API notice notifies the Web Dashboard and Chat interface.
3. The user can choose:
   - **`Approve Once`:** Allows the specific staged operation to proceed.
   - **`Always For Project`:** Creates a persistent rule in `data/agents/permissions.json` allowing identical operations within the active project.
   - **`Deny`:** Rejects the operation and returns an error to the calling agent.

---

# 5. Audit Logging & Secret Redaction

Every permission decision (approved, auto-approved, pending, or denied) is appended to `data/agents/permission_audit.jsonl`:

```json
{
  "timestamp": 1794234338.2,
  "request_id": "4b6e51e1-3829-4c8d-8a1a-3e5f29c01824",
  "agent_id": "codex",
  "operation": "file_write",
  "target_path": "/home/roshan/.gemini/antigravity/scratch/jarvis-os/data/temp.py",
  "status": "AUTO_APPROVED",
  "risk_level": "LOW",
  "decision_reason": "Workspace code modification auto-approved with pre-backup in SAFE_AUTO mode."
}
```

Any secrets in command lines or file paths are scrubbed with `[REDACTED_SECRET]` before writing to disk.

# JARVIS OS — Phase 1 System Telemetry Repair & Hardware Specifications

## 1. Problem Diagnosis: The 0.0GB / 0.0GB & Uptime N/A Defect

In earlier releases, system queries returned the following broken telemetry:

```text
CPU: 37.8%
RAM: 47.5% used (0.0GB / 0.0GB)
CPU Temp: 50.7°C
Disk: 38.6% used
Uptime: N/A
Robot: UNKNOWN
```

### Root Cause Analysis:
1. **Key Naming Disconnect:** In `hardware/raspberry_pi/rpi_info.py`, `get_system_status()` calculated values as `ram_total_mb`, `ram_used_mb`, and `uptime_s`. It never computed or returned the keys `ram_total_gb`, `ram_used_gb`, `ram_avail_gb`, or `uptime_str`.
2. **Formatter Missing Fallback:** In `ai/local_engine.py:698`, `_format_system()` queried `data.get('ram_used_gb', 0)` and `data.get('uptime_str', 'N/A')`. Missing keys defaulted to `0.0GB / 0.0GB` and `N/A`.
3. **Robot State Ambiguity:** The robot controller state defaulted to `UNKNOWN` without inspecting whether the controller was running in simulation or connected to physical I2C PCA9685 / TB6612 motor driver hardware.

---

## 2. Repairs Applied

### A. Accurate RAM and Swap GB Calculations
In `hardware/raspberry_pi/rpi_info.py`, memory calculations strictly adhere to binary gigabytes (`bytes / (1024**3)`):
```python
ram_total_gb = round(mem.total / (1024**3), 2)
ram_used_gb = round(mem.used / (1024**3), 2)
ram_avail_gb = round(mem.available / (1024**3), 2)
swap_total_gb = round(swap.total / (1024**3), 2)
swap_used_gb = round(swap.used / (1024**3), 2)
```

### B. Linux OS Uptime Formatting
Uptime is read directly from the Linux kernel `/proc/uptime` with fallback to `psutil.boot_time()`:
```python
def get_uptime_seconds() -> float:
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return float(time.time() - psutil.boot_time())

def format_uptime(uptime_s: float) -> str:
    total_sec = max(0, int(uptime_s))
    days = total_sec // 86400
    hours = (total_sec % 86400) // 3600
    minutes = (total_sec % 3600) // 60
    seconds = total_sec % 60
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0 or days > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return ", ".join(parts)
```

### C. Explicit Robot State Differentiation
The robot state cannot silently convert into a positive operational state:
- `SIMULATION`: Active simulation mode (`robot.simulated == True`). Physical motors will not actuate.
- `CONNECTED`: Physical TB6612FNG and PCA9685 HAT detected and initialized.
- `DISCONNECTED`: Hardware configured but devices not detected on I2C bus 1.
- `UNKNOWN`: Uninitialized or controller error.

---

## 3. Verified Live Telemetry Output

Captured directly from the running JARVIS system on Raspberry Pi 5:

```text
💻 System Status:
  🔲 CPU: 5.0%
  💾 RAM: 51.6% used (4.01 GB / 7.76 GB, Available: 3.76 GB)
  🌡️  CPU Temp: 55.1°C
  💿 Disk: 38.6% used (86.6 GB / 234.2 GB)
  ⏱️  Uptime: 2 hours, 26 minutes, 38 seconds
  🤖 Robot: SIMULATION
```
All measurements match real Linux operating system metrics verified via `free -m`, `df -h`, and `/proc/uptime`.

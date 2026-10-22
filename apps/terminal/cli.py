"""
JARVIS OS — Interactive Terminal CLI and Command Line Interface
Provides an interactive shell (REPL) and direct CLI command runner for JARVIS OS.
"""

import os
import sys
import argparse
import logging
import readline
import atexit
from typing import Optional, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.config_manager import config
from ai.brain import get_brain

# Setup logger to suppress debug logs during terminal interaction unless requested
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

HISTORY_FILE = os.path.expanduser("~/.jarvis_terminal_history")

# ANSI color codes
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    banner = rf"""{CYAN}{BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║      _   _   ___  ______  _   _  _____  _____  _____              ║
    ║     | | / \ | _ \|_   _ \/ \ | |/ ___/ / ___ \/  ___/             ║
    ║     | |/ _ \|   /  | |  \ \ \| |\_ \  | |   | |\___ \             ║
    ║  \__| / ___ \ |\ \ _| |_  \ \ \ \ __) | | |___| | ___) |          ║
    ║   \__/_/   \_\_| \_|_____|  \_|_//____/ \_____/\_/____/           ║
    ║                                                                   ║
    ║            Just A Rather Very Intelligent System                  ║
    ║                     Raspberry Pi 5 OS                             ║
    ╚═══════════════════════════════════════════════════════════════════╝{RESET}
    {DIM}Type your query, or {CYAN}/help{DIM} for special commands. Press {CYAN}Ctrl+C{DIM} or type {CYAN}/exit{DIM} to quit.{RESET}
    """
    print(banner)


def setup_readline():
    """Setup readline history persistence."""
    try:
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)
        atexit.register(readline.write_history_file, HISTORY_FILE)
    except Exception:
        pass


def execute_query(query: str, verbose: bool = False) -> str:
    """Send query to JARVIS brain and format the output."""
    brain = get_brain()
    try:
        res = brain.chat(query)
        response_text = res.get("response", "")
        provider = res.get("provider", "local")
        model = res.get("model", "")
        tools = res.get("tools_used", [])

        if tools:
            tool_names = ", ".join(t.get("tool", "") for t in tools if isinstance(t, dict))
            print(f"{YELLOW}⚙ Executed tools: {tool_names}{RESET}")

        if verbose:
            print(f"{DIM}[Provider: {provider} | Model: {model}]{RESET}")

        return response_text
    except Exception as e:
        return f"{RED}Error executing command: {e}{RESET}"


def cmd_status():
    """Display quick status of system and AI brain."""
    brain = get_brain()
    status_info = brain.status()
    print(f"\n{CYAN}{BOLD}=== JARVIS System & AI Status ==={RESET}")
    print(f"{BOLD}Active AI Provider:{RESET} {GREEN}{status_info.get('active', 'None')}{RESET}")
    print(f"{BOLD}Providers:{RESET}")
    for name, p in status_info.items():
        if name == "active":
            continue
        avail = p.get("available", False)
        status_str = f"{GREEN}Available{RESET}" if avail else f"{DIM}Unavailable{RESET}"
        print(f"  • {BOLD}{name}{RESET} ({p.get('model', '')}): {status_str}")

    try:
        from hardware.raspberry_pi.rpi_info import get_system_status
        sys_stat = get_system_status()
        print(f"\n{BOLD}Hardware Diagnostics:{RESET}")
        print(f"  • CPU Usage: {sys_stat.get('cpu_usage_pct', 0)}%")
        print(f"  • CPU Temp:  {sys_stat.get('cpu_temp_c', 0):.1f}°C")
        print(f"  • RAM Used:  {sys_stat.get('memory_used_mb', 0):.0f}MB / {sys_stat.get('memory_total_mb', 0):.0f}MB")
        print(f"  • Disk Used: {sys_stat.get('disk_used_percent', 0)}%")
    except Exception as e:
        print(f"  {RED}Hardware status error: {e}{RESET}")
    print()


def cmd_sensors():
    """Read environmental sensors."""
    try:
        from hardware.sensors.sensor_manager import sensor_manager
        readings = sensor_manager.read_all()
        print(f"\n{CYAN}{BOLD}=== Environmental Sensors ==={RESET}")
        for s_name, data in readings.items():
            print(f"  • {BOLD}{s_name}{RESET}: {data}")
        print()
    except Exception as e:
        print(f"{RED}Failed to read sensors: {e}{RESET}")


def cmd_estop():
    """Trigger emergency stop."""
    try:
        from tools.robotics.controller import robot
        robot.emergency_stop()
        print(f"\n{RED}{BOLD}🚨 EMERGENCY STOP ACTIVATED: All motors halted.{RESET}\n")
    except Exception as e:
        print(f"{RED}Failed to emergency stop: {e}{RESET}")


def cmd_help():
    """Print available commands."""
    print(f"""
{CYAN}{BOLD}JARVIS Terminal Commands:{RESET}
  {BOLD}/help{RESET}             Show this help screen
  {BOLD}/status{RESET}           Show AI provider and system diagnostics
  {BOLD}/sensors{RESET}          Read all hardware sensors
  {BOLD}/estop{RESET}            Emergency stop all robot movement
  {BOLD}/clear{RESET}            Clear terminal screen
  {BOLD}/exit, /quit{RESET}      Exit JARVIS terminal

{CYAN}{BOLD}Natural Language Examples:{RESET}
  • "open vs code"
  • "write a python program for a calculator, open it in vs code and run it"
  • "what is the system temperature and memory usage?"
  • "robot move forward at speed 50"
  • "store memory: my favorite color is navy blue"
  • "search memory for favorite color"
    """)


def repl(verbose: bool = False):
    """Run the interactive REPL."""
    print_banner()
    setup_readline()

    while True:
        try:
            prompt_str = f"{BLUE}{BOLD}JARVIS{RESET} > "
            user_input = input(prompt_str).strip()
            if not user_input:
                continue

            # Command handling
            if user_input in ("/exit", "/quit", "exit", "quit"):
                print(f"{CYAN}Good day, Sir. Standing by.{RESET}")
                break
            elif user_input == "/help":
                cmd_help()
            elif user_input == "/status":
                cmd_status()
            elif user_input == "/sensors":
                cmd_sensors()
            elif user_input == "/estop":
                cmd_estop()
            elif user_input in ("/clear", "clear"):
                os.system("clear")
            else:
                # Normal AI Brain interaction
                resp = execute_query(user_input, verbose=verbose)
                print(f"\n{GREEN}{BOLD}JARVIS:{RESET}\n{resp}\n")

        except KeyboardInterrupt:
            print(f"\n{DIM}(Interrupted — type /exit to leave){RESET}")
            continue
        except EOFError:
            print(f"\n{CYAN}Session terminated. Goodbye.{RESET}")
            break


def main():
    parser = argparse.ArgumentParser(description="JARVIS OS Interactive CLI & Runner")
    parser.add_argument("command", nargs="*", help="Direct command to execute (non-interactive)")
    parser.add_argument("-c", "--query", type=str, help="Single query to send to JARVIS")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show provider and diagnostic details")
    parser.add_argument("--status", action="store_true", help="Display system & AI status")
    parser.add_argument("--sensors", action="store_true", help="Read environmental sensors")
    parser.add_argument("--estop", action="store_true", help="Emergency stop all motors")

    args = parser.parse_args()

    if args.status:
        cmd_status()
        return

    if args.sensors:
        cmd_sensors()
        return

    if args.estop:
        cmd_estop()
        return

    # Handle direct one-off query
    direct_query = args.query or (" ".join(args.command) if args.command else None)
    if direct_query:
        resp = execute_query(direct_query, verbose=args.verbose)
        print(resp)
        return

    # Otherwise launch interactive REPL
    repl(verbose=args.verbose)


if __name__ == "__main__":
    main()

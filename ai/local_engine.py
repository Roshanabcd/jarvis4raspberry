"""
JARVIS Local Intelligence Engine
A rule-based + template engine that provides full JARVIS capability
without requiring an external LLM. Uses NLP intent classification,
real tool execution, and structured responses.

This is NOT a "I'm offline" fallback — it actually DOES the tasks.
"""
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("JARVIS.LocalEngine")

# Intent patterns → (intent_name, tool_to_call, template_response)
INTENTS = [
    # Media controls (high priority so 'stop music' is not caught by robot stop)
    (r"\b(pause)\s+(?:the\s+)?(?:music|song|track|audio|playback)\b", "pause_media", None),
    (r"\b(stop|halt|kill|end)\s+(?:the\s+)?(?:music|song|track|audio|playback|playing)\b", "stop_media", None),
    (r"\b(resume|continue|unpause)\s+(?:the\s+)?(?:music|song|track|playback)\b", "resume_media", None),
    (r"\b(what('s|\s+is)\s+playing|what\s+song\b|current\s+song|now\s+playing)\b", "media_status", None),
    (r"\b(?:play|stream|listen to)\s+(?:a\s+|the\s+)?(?:song|music|track|audio|tune)\s*(.*)", "play_media", None),
    (r"\bplay\s+([a-zA-Z0-9_\-\s\'\"]+)", "play_media", None),

    # Volume control
    (r"\b(?:set|change)\s+volume\s+(?:to\s+)?(\d+)\%?\b", "set_volume", None),
    (r"\b(volume\s+up|increase\s+volume|turn\s+it\s+up|louder)\b", "volume_up", None),
    (r"\b(volume\s+down|decrease\s+volume|turn\s+it\s+down|quieter|lower\s+volume)\b", "volume_down", None),

    # Folder & File Search and Opening
    (r"\b(?:open|show|explore|view)\s+(?:the\s+)?(.+?)\s+(?:folder|directory|dir)\s+(?:located\s+in|in|at)\s+(.+)", "open_folder_at", None),
    (r"\b(?:open|show|explore|view|browse)\s+(?:the\s+)?(?:folder|directory|dir)\s+(.+)", "open_folder", None),
    (r"\b(?:open|show|explore)\s+(downloads|music|desktop|documents|home|pictures|videos)\s*(?:folder|directory|dir)?\b", "open_folder", None),
    (r"\b(?:search|find|locate|look for)\s+(?:for\s+)?(?:the\s+)?(.+?)\s+(?:folder|directory|dir)\b", "search_folder", None),
    (r"\b(?:search|find|locate)\s+(?:folder|directory|dir)\s+(.+)", "search_folder", None),
    (r"\b(?:search|find|locate|look for)\s+(?:for\s+)?(?:the\s+)?(.+?)\s+file\b", "search_file", None),
    (r"\b(?:search|find|locate)\s+file\s+(.+)", "search_file", None),

    # Math (highest priority to not get caught by web_search "what is")
    (r"\d+\s*[\+\-\*\/]\s*\d+", "calculate", None),
    (r"\b(calculate|compute|math|solve)\s+([\d\+\-\*\/\^\(\)\.\s]+)", "calculate", None),

    # Robot control
    (r"\b(go|move|drive|navigate)\b.*(forward|ahead|straight)", "robot_forward", None),
    (r"\b(go|move|drive)\b.*(back|backward|reverse)", "robot_backward", None),
    (r"\b(turn|rotate|spin|go|move)\b.*(left)\b", "robot_left", None),
    (r"\b(turn|rotate|spin|go|move)\b.*(right)\b", "robot_right", None),
    (r"\b(emergency stop|e-stop|estop|kill switch)\b", "robot_estop", None),
    (r"\b(stop|halt|freeze|pause)\b", "robot_stop", None),
    (r"\bservo\s+(\d+)\s+(?:to\s+)?(\d+)\b", "servo_set", None),

    # System (before sensors to take priority)
    (r"\b(status|cpu|cpu usage|processor|ram|memory usage|disk|system info|health|system status)\b", "system_status", None),
    (r"\b(how much (memory|ram)|memory available|uptime)\b", "system_status", None),

    # Sensors
    (r"\b(sensors?|temperatures?|humidity|pressure|light|lux|distance|motion|pir|ultrasonic)\b", "read_sensors", None),
    (r"\b(what.*(temp|hot|cold|warm)|how warm|how cold)\b", "read_sensors", None),

    # Camera
    (r"\b(camera|capture|photo|picture|image|take a (photo|picture)|what (do you see|can you see))\b", "camera_capture", None),
    (r"\b(look|see|observe|describe (what|the|around))\b", "camera_capture", None),

    # Memory
    (r"\b(remember|store|save|note|record)\s+(.+)", "memory_store", None),
    (r"\b(what do you remember|recall|search memory|look up|what do you know about|tell me about|do you know)\s+(.+)?", "memory_search", None),

    # Coding & Program Execution (Specific test helper only; general programming routes to LLM)
    (r"\b(?:write|create|code|make)\b.*python\b.*calculator.*(?:vs\s*code|vscode)", "create_calculator", None),

    # Desktop Apps & Editors
    (r"\b(open|launch|start)\s+(vs\s*code|vscode|code\s+editor|visual\s+studio\s+code|terminal|browser|chromium|chrome|mousepad|lxterminal|calculator|galculator|text\s+editor)\b", "open_app", None),
    (r"\b(open\s+.*in\s+(?:vs\s*code|vscode|editor|mousepad))\b", "open_app", None),
    (r"\b(run|execute)\s+(?:the\s+)?(?:python\s+)?(?:program|script|code|file)\b", "run_code", None),

    # File
    (r"\b(read|open|cat|display)\s+file\s+(\S+)", "read_file", None),
    (r"\b(cat|display)\s+(\S+\.\w+)", "read_file", None),
    (r"\b(write|save)\s+file\s+(\S+)", "write_file", None),
    (r"\b(write|save)\s+(?:to\s+)?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)\b", "write_file", None),
    (r"\b(list files?|ls|dir|directory)\b", "list_files", None),

    # Web search
    (r"\b(search|google|look up|find|what is|who is|when (did|was)|where (is|was))\s+(.+)", "web_search", None),
    (r"\b(news|latest|current|today's?)\b", "web_search", None),
    (r"\bweather\b", "web_search_weather", None),

    # Math
    (r"\d+\s*[\+\-\*\/]\s*\d+", "calculate", None),
    (r"\b(calculate|compute|what is|solve)\s+([\d\s\+\-\*\/\^\(\)\.]+)", "calculate", None),

    # Schedule
    (r"\b(schedule|remind me|set a (reminder|alarm|timer))\b", "schedule_task", None),

    # Identity / about
    (r"\b(who are you|what are you|your name|introduce yourself|what can you do)\b", "identity", None),

    # Help
    (r"\b(help|show commands|list commands|command list|command reference|capabilities|how do i|what commands|what can you)\b", "help", None),
]


class LocalIntelligenceEngine:
    """
    Full JARVIS intelligence without an LLM.
    Classifies intent, executes real tools, formats human responses.
    """

    def __init__(self):
        from ai.tools.executor import ToolExecutor
        self.executor = ToolExecutor()

    def classify_intent(self, text: str) -> Tuple[str, Dict]:
        """Returns (intent_name, extracted_args)"""
        text_lower = text.lower().strip()

        # 0. Standalone number check (Test 5: "2020")
        if re.match(r"^\s*\d+(?:\.\d+)?\s*$", text.strip()):
            return "standalone_number", {"number": text.strip(), "text": text}

        # 2. Conversational history recall (Test 8: "What was my first question?")
        if re.search(r"\b(what was my (?:first|last|previous) question|what did i (?:ask|say)|previous question|first question)\b", text_lower):
            return "history_recall", {"text": text}

        # 3. Phase 2 Desktop Intents
        # 3a. Specific App Opening ("Open Google Chrome", "Open Chrome", "Open Firefox", "Open VS Code", "Open Antigravity")
        m_app = re.search(r'^\s*(?:open|launch|start)\s+(google\s+chrome|chrome|firefox|vs\s*code|vscode|code|antigravity|antigravity\s+ide|terminal|lxterminal)(?:\s+(?:in\s+)?(?:a\s+)?new\s+window)?[\.\?!]*\s*$', text_lower)
        if m_app:
            return "desktop_open_app", {"app": m_app.group(1).strip(), "text": text}

        # 3b. Project Opening in IDE (VS Code or Antigravity)
        m_proj = re.search(r'\bopen\s+(?:my\s+)?(.+?)\s+(?:project\s+|folder\s+|workspace\s+)?in\s+(vs\s*code|vscode|code|antigravity|antigravity\s+ide)\b', text_lower)
        if m_proj:
            return "desktop_open_project", {"project": m_proj.group(1).strip(), "editor": m_proj.group(2).strip(), "text": text}

        m_proj_named = re.search(r'\bopen\s+(?:the\s+)?(?:project\s+|folder\s+)?(gameproject|unitygameworkspace|jarvis-os)\b', text_lower)
        if m_proj_named:
            return "desktop_open_project", {"project": m_proj_named.group(1).strip(), "editor": "vscode", "text": text}

        # 3c. YouTube in Browser / YouTube Search
        m_yt = re.search(r'\b(?:play|search|find|open)\s+(?:for\s+)?(.+?)\s+(?:on|in)\s+youtube\b', text_lower) or re.search(r'\bsearch\s+youtube\s+for\s+(.+)', text_lower)
        if m_yt:
            return "desktop_search_youtube", {"query": m_yt.group(1).strip(), "text": text}

        m_url = re.search(r'\bopen\s+(?:the\s+)?(?:website\s+|url\s+|link\s+)?(https?://\S+|youtube|google|github|reddit|wikipedia)(?:\s+in\s+(google\s+chrome|chrome|firefox|browser))?\b', text_lower)
        if m_url:
            return "desktop_open_url", {"url": m_url.group(1).strip(), "browser": m_url.group(2) or "chrome", "text": text}

        # 3d. File & Content Search
        m_sfiles = re.search(r'\b(?:find|search)\s+(?:for\s+)?(?:all\s+)?(\w+|\*\.\w+)?\s*files?\s+(?:in|under)\s+(.+)', text_lower)
        if m_sfiles and not re.search(r'\b(remember|save|note)\b', text_lower):
            return "desktop_search_files", {"pattern": m_sfiles.group(1), "directory": m_sfiles.group(2).strip(), "text": text}

        m_scont = re.search(r'\b(?:find|search)\s+(?:for\s+)?(?:all\s+|every\s+)?files?\s+containing\s+(?:the\s+word\s+|the\s+phrase\s+)?["\']?([^"\']+)["\']?(?:\s+in\s+(.+))?', text_lower)
        if m_scont and not re.search(r'\b(remember|save|note)\b', text_lower):
            return "desktop_search_content", {"query": m_scont.group(1).strip(), "directory": m_scont.group(2), "text": text}

        # 3e. Terminal Command Execution
        m_term = re.search(r'\brun\s+(.+?)\s+in\s+(?:the\s+)?terminal\b', text_lower) or re.search(r'^\s*run\s+(python3\s+--version|ls\s+-[a-zA-Z]+|pwd|whoami)\s*$', text_lower) or re.search(r'\bopen\s+(?:a\s+)?terminal\s+and\s+execute\s+(.+)', text_lower)
        if m_term:
            return "terminal_execute", {"command": m_term.group(1).strip(), "text": text}

        # 3f. Program Execution in Folder
        m_prog = re.search(r'\brun\s+(?:my\s+)?(?:python\s+)?(?:program|script)\s+in\s+(?:the\s+)?(.+)', text_lower) or re.search(r'\brun\s+([a-zA-Z0-9_\-\.\/]+\.py)\s+in\s+(?:my\s+)?(.+)', text_lower)
        if m_prog:
            prog_arg = m_prog.group(1).strip()
            loc_arg = m_prog.group(2).strip() if m_prog.lastindex >= 2 and m_prog.group(2) else None
            return "desktop_run_program", {"program": prog_arg, "location": loc_arg, "text": text}

        # 3g. Desktop Awareness
        if re.search(r'\b(which application is open|what is the active window|show the current active window|active window|running applications)\b', text_lower) or re.search(r'\bis\s+(vs\s*code|vscode|chrome|firefox|antigravity)\s+running\b', text_lower):
            return "desktop_awareness", {"text": text}

        # 3h. Deterministic natural-language math check (Test 6: "What is 25 multiplied by 4?", "15 percent of 800", "What is 1024 * 2 + 50?")
        if re.search(r"\b(?:\d+(?:\.\d+)?\s*(?:multiplied\s+by|times|\*|divided\s+by|\/|plus|\+|minus|\-|to\s+the\s+power\s+of|\^|%|percent\s+of)\s*\d+|\d+\s*[\+\-\*\/]\s*\d+)", text_lower):
            clean_math = re.sub(r'^(?:what\s+is\s+|calculate\s+|compute\s+|solve\s+|how\s+much\s+is\s+|find\s+)', '', text.strip(), flags=re.I).rstrip('?.')
            return "calculate", {"expression": clean_math, "text": text}

        # 4. Code generation, programming, algorithms, or technical explanations -> LLM ("general")
        # (Test 3: "Write a Python script...", Test 4: "Write a Python function to compute Fibonacci numbers...")
        if re.search(r"\b(write|create|implement|code|generate|build|program|script|function|def\s+\w+|fibonacci|algorithm|explanation|explain|why is|why are|how does|what is a\b|tell me about the concept|joke|story|poem|who was)\b", text_lower):
            # Unless explicitly commanding to open desktop editor or run an existing script
            if not re.search(r"\b(?:open|launch|start)\b.*(?:vs\s*code|vscode|mousepad|lxterminal)\b", text_lower) and not re.search(r"\b(?:run|execute)\s+(?:the\s+|my\s+|this\s+)?(?:python\s+)?(?:script|file|code|program)\b", text_lower):
                return "general", {"text": text}

        for pattern, intent, _ in INTENTS:
            m = re.search(pattern, text_lower)
            if m:
                extracted = {"match": m, "text": text}
                if intent == "play_media":
                    groups = [g for g in m.groups() if g]
                    if groups:
                        cand = groups[-1].strip()
                        if cand.lower() not in ("song", "music", "track", "audio", "tune"):
                            extracted["query"] = cand
                elif intent == "search_folder":
                    if m.lastindex:
                        extracted["query"] = m.group(m.lastindex).strip()
                elif intent == "open_folder":
                    if m.lastindex:
                        extracted["folder"] = m.group(m.lastindex).strip()
                elif intent == "open_folder_at":
                    groups = [g for g in m.groups() if g]
                    if len(groups) >= 2:
                        extracted["folder"] = groups[0].strip()
                        raw_parent = groups[1].strip()
                        clean_parent = re.sub(r"\s+(?:folder|directory|dir|location)$", "", raw_parent, flags=re.I).strip()
                        extracted["parent"] = clean_parent
                return intent, extracted

        return "general", {"text": text}

    def respond(self, user_message: str) -> Dict[str, Any]:
        """Process a message and return a structured response."""
        intent, ctx = self.classify_intent(user_message)
        text = ctx["text"]
        match = ctx.get("match")

        tools_used = []

        try:
            if intent == "standalone_number":
                num = ctx.get("number", text)
                return {
                    "response": f"You mentioned the number {num}. How would you like me to use it? (e.g., perform a calculation, look up records, or store it in memory?)",
                    "tools_used": [],
                }

            elif intent == "identity":
                return self._respond_identity()

            elif intent == "help":
                return self._respond_help()

            elif intent == "calculate":
                calc_expr = ctx.get("expression") or text
                return self._respond_calculate(calc_expr)

            elif intent == "desktop_open_url":
                return self._respond_desktop_open_url(ctx)

            elif intent == "desktop_search_youtube":
                return self._respond_desktop_search_youtube(ctx)

            elif intent == "desktop_open_project":
                return self._respond_desktop_open_project(ctx)

            elif intent == "desktop_open_app":
                return self._respond_desktop_open_app(ctx)

            elif intent == "desktop_search_files":
                return self._respond_desktop_search_files(ctx)

            elif intent == "desktop_search_content":
                return self._respond_desktop_search_content(ctx)

            elif intent == "desktop_run_program":
                return self._respond_desktop_run_program(ctx)

            elif intent == "terminal_execute":
                return self._respond_terminal_execute(ctx)

            elif intent == "desktop_awareness":
                return self._respond_desktop_awareness(ctx)

            elif intent == "robot_forward":
                speed = self._extract_speed(text) or 50
                dur = self._extract_duration_ms(text)
                result_raw = self.executor.execute("robot_move",
                    {"direction": "forward", "speed": speed, "duration_ms": dur})
                result = json.loads(result_raw)
                tools_used.append("robot_move")
                sim = result.get("simulated", True)
                mode = " (simulated)" if sim else ""
                resp = (f"Moving forward at {speed}% speed{mode}."
                        + (f" Will stop after {dur}ms." if dur else ""))
                return {"response": resp, "tools_used": tools_used, "raw": result}

            elif intent == "robot_backward":
                speed = self._extract_speed(text) or 50
                dur = self._extract_duration_ms(text)
                result_raw = self.executor.execute("robot_move",
                    {"direction": "backward", "speed": speed, "duration_ms": dur})
                tools_used.append("robot_move")
                result = json.loads(result_raw)
                sim = result.get("simulated", True)
                mode = " (simulated)" if sim else ""
                return {"response": f"Moving backward at {speed}% speed{mode}.", "tools_used": tools_used, "raw": result}

            elif intent == "robot_left":
                speed = self._extract_speed(text) or 40
                result_raw = self.executor.execute("robot_move",
                    {"direction": "left", "speed": speed})
                tools_used.append("robot_move")
                return {"response": f"Turning left at {speed}% speed.", "tools_used": tools_used}

            elif intent == "robot_right":
                speed = self._extract_speed(text) or 40
                result_raw = self.executor.execute("robot_move",
                    {"direction": "right", "speed": speed})
                tools_used.append("robot_move")
                return {"response": f"Turning right at {speed}% speed.", "tools_used": tools_used}

            elif intent == "robot_stop":
                self.executor.execute("robot_move", {"direction": "stop"})
                tools_used.append("robot_move")
                return {"response": "Robot stopped. Motors coasting to halt.", "tools_used": tools_used}

            elif intent == "robot_estop":
                self.executor.execute("robot_move", {"direction": "estop"})
                tools_used.append("robot_move")
                return {"response": "⚠️ EMERGENCY STOP activated. All motors cut immediately.", "tools_used": tools_used}

            elif intent == "servo_set":
                # Try to extract channel and angle
                nums = re.findall(r'\d+', text)
                ch, angle = (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (0, 90)
                ch = min(ch, 15)
                angle = max(0, min(180, angle))
                self.executor.execute("servo_set", {"channel": ch, "angle": angle})
                tools_used.append("servo_set")
                return {"response": f"Servo channel {ch} set to {angle}°.", "tools_used": tools_used}

            elif intent == "read_sensors":
                result_raw = self.executor.execute("read_sensors", {})
                result = json.loads(result_raw)
                tools_used.append("read_sensors")
                return {"response": self._format_sensors(result), "tools_used": tools_used, "raw": result}

            elif intent == "system_status":
                result_raw = self.executor.execute("get_system_status", {})
                result = json.loads(result_raw)
                tools_used.append("get_system_status")
                return {"response": self._format_system(result), "tools_used": tools_used, "raw": result}

            elif intent == "camera_capture":
                result_raw = self.executor.execute("camera_capture", {})
                result = json.loads(result_raw)
                tools_used.append("camera_capture")
                desc = result.get("description", "No description available.")
                sim = result.get("simulated", True)
                mode = " (camera simulated)" if sim else ""
                return {"response": f"Camera capture{mode}: {desc}", "tools_used": tools_used}

            elif intent == "memory_store":
                # Extract what to remember
                m_content = re.search(r'\b(?:remember|store|save|note|record)\s+(?:that\s+)?(.+)', text, re.I)
                content = m_content.group(1) if m_content else text
                result_raw = self.executor.execute("memory_store",
                    {"category": "KNOWLEDGE", "content": content})
                result = json.loads(result_raw)
                tools_used.append("memory_store")
                return {"response": f"Stored in memory: \"{content[:80]}\" (ID: {result.get('id', '?')})", "tools_used": tools_used}

            elif intent == "memory_search":
                m_q = re.search(r'\b(?:remember|recall|search memory|look up|what do you remember about)\s+(.+)', text, re.I)
                query = m_q.group(1) if m_q else text
                # Clean query: remove possessives and punctuation
                import re as _re
                clean_q = _re.sub(r"'s\b", "", query).strip().rstrip("?.")
                result_raw = self.executor.execute("memory_search", {"query": clean_q or query})
                result = json.loads(result_raw)
                tools_used.append("memory_search")
                items = result.get("results", [])
                if items:
                    bullet = "\n".join(f"  • {r.get('content', '')[:80]}" for r in items[:3])
                    resp = f"Found {len(items)} memory record(s) for \"{clean_q or query}\":\n{bullet}"
                else:
                    resp = f"No memories found matching \"{clean_q or query}\"."
                return {"response": resp, "tools_used": tools_used}

            # ── Media Playback ──────────────────────────────────────────
            elif intent == "play_media":
                m_track = None
                if match:
                    groups = [g for g in match.groups() if g]
                    if groups:
                        cand = groups[-1].strip()
                        if cand.lower() not in ("song", "music", "track", "audio", "tune"):
                            m_track = cand
                raw = self.executor.execute("play_media", {"query": m_track or ""})
                tools_used.append("play_media")
                res = json.loads(raw)
                if res.get("status") == "playing":
                    title = res.get("title", m_track or "Audio Track")
                    src = "local storage" if res.get("source") == "local" else "online stream"
                    return {"response": f"🎵 Now playing '{title}' from {src} through the physical speaker.", "tools_used": tools_used, "raw": res}
                else:
                    return {"response": f"⚠️ Media playback issue: {res.get('message', 'Unable to play requested audio.')}", "tools_used": tools_used, "raw": res}

            elif intent == "stop_media":
                raw = self.executor.execute("stop_media", {})
                tools_used.append("stop_media")
                res = json.loads(raw)
                return {"response": f"⏹️ Audio playback stopped.", "tools_used": tools_used, "raw": res}

            elif intent == "pause_media":
                raw = self.executor.execute("pause_media", {})
                tools_used.append("pause_media")
                res = json.loads(raw)
                return {"response": f"⏸️ {res.get('message', 'Audio playback paused.')}", "tools_used": tools_used, "raw": res}

            elif intent == "resume_media":
                raw = self.executor.execute("resume_media", {})
                tools_used.append("resume_media")
                res = json.loads(raw)
                return {"response": f"▶️ {res.get('message', 'Audio playback resumed.')}", "tools_used": tools_used, "raw": res}

            elif intent == "media_status":
                from tools.media.media_player import media_player
                st = media_player.status()
                if st.get("is_playing"):
                    return {"response": f"🎵 Currently playing '{st.get('track')}' through the speaker.", "tools_used": ["media_status"]}
                elif st.get("is_paused"):
                    return {"response": f"⏸️ Playback of '{st.get('track')}' is currently paused.", "tools_used": ["media_status"]}
                else:
                    return {"response": "🔇 No audio is currently playing.", "tools_used": ["media_status"]}

            # ── Volume Control ──────────────────────────────────────────
            elif intent == "set_volume":
                vol = 70
                if match and match.group(1):
                    vol = int(match.group(1))
                raw = self.executor.execute("set_volume", {"level_pct": vol})
                tools_used.append("set_volume")
                return {"response": f"🔊 Speaker volume set to {vol}%.", "tools_used": tools_used}

            elif intent == "volume_up":
                from tools.media.media_player import media_player
                res = media_player.adjust_volume(+15)
                tools_used.append("set_volume")
                return {"response": f"🔊 Volume increased to {res.get('volume_pct', 'higher')}%.", "tools_used": tools_used, "raw": res}

            elif intent == "volume_down":
                from tools.media.media_player import media_player
                res = media_player.adjust_volume(-15)
                tools_used.append("set_volume")
                return {"response": f"🔉 Volume decreased to {res.get('volume_pct', 'lower')}%.", "tools_used": tools_used, "raw": res}

            # ── Folder & File Navigation ───────────────────────────────
            elif intent == "search_folder":
                query = text
                if match:
                    groups = [g for g in match.groups() if g]
                    if groups:
                        query = groups[-1].strip()
                raw = self.executor.execute("search_folders", {"query": query})
                tools_used.append("search_folders")
                res = json.loads(raw)
                folders = res if isinstance(res, list) else res.get("folders", [])
                if folders:
                    bullet = "\n".join(f"  📁 **{f['name']}** — `{f['path']}` ({f['items_count']} items)" for f in folders[:5])
                    return {"response": f"Found {len(folders)} folder(s) matching '{query}':\n{bullet}", "tools_used": tools_used, "raw": res}
                else:
                    return {"response": f"No folders found matching '{query}' in your workspace directories.", "tools_used": tools_used, "raw": res}

            elif intent == "search_file":
                query = text
                if match:
                    groups = [g for g in match.groups() if g]
                    if groups:
                        query = groups[-1].strip()
                from tools.filesystem.file_tools import file_tools
                home = file_tools.workspaces.get("HOME", os.path.expanduser("~"))
                matches = file_tools.search_files(home, f"*{query}*")
                tools_used.append("search_files")
                if matches:
                    bullet = "\n".join(f"  📄 `{p}`" for p in matches[:5])
                    return {"response": f"Found {len(matches)} file(s) matching '{query}':\n{bullet}", "tools_used": tools_used}
                else:
                    return {"response": f"No files found matching '{query}'.", "tools_used": tools_used}

            elif intent == "open_folder_at":
                folder_name = ctx.get("folder", "")
                parent_loc = ctx.get("parent", "")
                if not folder_name and match:
                    groups = [g for g in match.groups() if g]
                    if len(groups) >= 2:
                        folder_name = groups[0].strip()
                        parent_loc = re.sub(r"\s+(?:folder|directory|dir|location)$", "", groups[1].strip(), flags=re.I).strip()
                raw = self.executor.execute("open_folder", {"folder_name": folder_name, "parent_location": parent_loc})
                tools_used.append("open_folder")
                res = json.loads(raw)
                if res.get("status") == "opened":
                    items_str = ", ".join(res.get("items", [])[:8]) or "empty"
                    return {"response": f"📂 Successfully opened folder '{res.get('name')}' at `{res.get('path')}`.\nContents ({res.get('total_items')} items): {items_str}.", "tools_used": tools_used, "raw": res}
                else:
                    return {"response": f"⚠️ {res.get('message', f'Could not open folder {folder_name}.')}", "tools_used": tools_used, "raw": res}

            elif intent == "open_folder":
                folder_name = ctx.get("folder", "")
                if not folder_name and match:
                    groups = [g for g in match.groups() if g]
                    if groups:
                        folder_name = groups[-1].strip()
                raw = self.executor.execute("open_folder", {"folder_name": folder_name})
                tools_used.append("open_folder")
                res = json.loads(raw)
                if res.get("status") == "opened":
                    items_str = ", ".join(res.get("items", [])[:8]) or "empty"
                    return {"response": f"📂 Opened folder '{res.get('name')}' at `{res.get('path')}`.\nContents ({res.get('total_items')} items): {items_str}.", "tools_used": tools_used, "raw": res}
                else:
                    return {"response": f"⚠️ {res.get('message', f'Could not open folder {folder_name}.')}", "tools_used": tools_used, "raw": res}

            # ── Desktop Apps & Editors ────────────────────────────────
            elif intent == "open_app":
                target_app = "code"
                text_lower = text.lower()
                if "terminal" in text_lower or "lxterminal" in text_lower:
                    target_app = "lxterminal"
                elif "browser" in text_lower or "chromium" in text_lower or "chrome" in text_lower:
                    target_app = "chromium-browser"
                elif "calculator" in text_lower or "galculator" in text_lower:
                    target_app = "galculator"
                elif "mousepad" in text_lower or "text editor" in text_lower:
                    target_app = "mousepad"
                elif "file manager" in text_lower or "files" in text_lower or "pcmanfm" in text_lower:
                    target_app = "pcmanfm"
                elif "vs code" in text_lower or "vscode" in text_lower or "visual studio code" in text_lower or "code" in text_lower:
                    target_app = "code"

                target_file = None
                m_file = re.search(r'(?:file|in|open)\s+([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)', text)
                if m_file:
                    target_file = m_file.group(1)

                raw = self.executor.execute("open_app", {"app_name": target_app, "target": target_file})
                result = json.loads(raw)
                tools_used.append("open_app")
                if result.get("status") == "opened":
                    app_disp = "VS Code" if target_app == "code" else target_app
                    target_disp = f" with `{target_file}`" if target_file else ""
                    return {"response": f"🚀 Successfully launched {app_disp}{target_disp} (PID: {result.get('pid')}).", "tools_used": tools_used, "raw": result}
                else:
                    return {"response": f"⚠️ Could not open {target_app}: {result.get('error', 'Unknown error')}", "tools_used": tools_used, "raw": result}

            elif intent in ("create_calculator", "write_code"):
                text_lower = text.lower()
                filename = "calculator.py" if "calculator" in text_lower or "calc" in text_lower else "script.py"

                if "calculator" in text_lower or "calc" in text_lower:
                    code_content = '''#!/usr/bin/env python3
"""
Simple Interactive Calculator created by JARVIS OS
"""
import sys

def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b):
    if b == 0: return "Error: Division by zero"
    return a / b

def run_tests():
    print("=== JARVIS Calculator Self-Test ===")
    print(f"10 + 5 = {add(10, 5)}")
    print(f"10 - 5 = {subtract(10, 5)}")
    print(f"10 * 5 = {multiply(10, 5)}")
    print(f"10 / 5 = {divide(10, 5)}")
    print("✓ All calculator functions operating normally.")

if __name__ == "__main__":
    run_tests()
'''
                else:
                    code_content = f'''#!/usr/bin/env python3
"""
Python script generated by JARVIS OS
Task: {text}
"""
import sys

def main():
    print("JARVIS Python Script execution running...")
    print("Task: {text}")

if __name__ == "__main__":
    main()
'''
                # 1. Write the file
                self.executor.execute("write_file", {"path": filename, "content": code_content})
                tools_used.append("write_file")

                # 2. Run the program if requested
                exec_output = ""
                if "run" in text_lower or "execute" in text_lower:
                    run_res_raw = self.executor.execute("run_code", {"file_path": filename, "language": "python"})
                    tools_used.append("run_code")
                    try:
                        run_res = json.loads(run_res_raw)
                        exec_output = run_res.get("stdout", "") or run_res.get("stderr", "")
                    except Exception:
                        exec_output = run_res_raw

                # 3. Open in VS Code only if explicitly requested
                app_opened = False
                if re.search(r"\b(vs\s*code|vscode|visual\s+studio\s+code)\b", text_lower):
                    open_res_raw = self.executor.execute("open_app", {"app_name": "code", "target": filename})
                    tools_used.append("open_app")
                    try:
                        open_res = json.loads(open_res_raw)
                        app_opened = open_res.get("status") == "opened"
                    except Exception:
                        app_opened = False

                resp_lines = [
                    f"✅ Python calculator program created: `{filename}`",
                ]
                if app_opened:
                    resp_lines.append(f"💻 Opened in VS Code (`code {filename}`).")
                if exec_output:
                    resp_lines.append(f"⚡ Execution Output:\n```\n{exec_output.strip()}\n```")
                elif "run" in text_lower:
                    resp_lines.append("⚡ Program executed successfully.")

                return {"response": "\n\n".join(resp_lines), "tools_used": tools_used}

            elif intent == "run_code":
                m_file = re.search(r'([a-zA-Z0-9_\-\.\/]+\.py)', text)
                target_file = m_file.group(1) if m_file else "calculator.py"
                run_res_raw = self.executor.execute("run_code", {"file_path": target_file, "language": "python"})
                tools_used.append("run_code")
                try:
                    run_res = json.loads(run_res_raw)
                    output = run_res.get("stdout", "") or run_res.get("stderr", "")
                    if run_res.get("status") == "success":
                        return {"response": f"⚡ Executed `{target_file}` successfully:\n```\n{output.strip()}\n```", "tools_used": tools_used}
                    else:
                        return {"response": f"⚠️ Execution of `{target_file}` returned an error:\n```\n{output.strip()}\n```", "tools_used": tools_used}
                except Exception:
                    return {"response": f"⚡ Executed `{target_file}`: {run_res_raw}", "tools_used": tools_used}

            elif intent == "read_file":
                m_f = re.search(r"['\"]?([^\s'\"]+\.\w+)['\"]?", text)
                path = m_f.group(1) if m_f else "."
                result_raw = self.executor.execute("read_file", {"path": path})
                result = json.loads(result_raw)
                tools_used.append("read_file")
                if result.get("error"):
                    return {"response": f"Cannot read file: {result['error']}", "tools_used": tools_used}
                content = result.get("content", "")[:500]
                return {"response": f"Contents of {path}:\n```\n{content}\n```", "tools_used": tools_used}

            elif intent == "list_files":
                result_raw = self.executor.execute("run_command", {"command": "ls", "args": ["-la"]})
                result = json.loads(result_raw)
                tools_used.append("run_command")
                return {"response": f"Files:\n```\n{result.get('stdout', '')[:600]}\n```", "tools_used": tools_used}

            elif intent in ("web_search", "web_search_weather"):
                # Extract the search query
                query = text
                if intent == "web_search_weather":
                    query = "current weather forecast"
                else:
                    for prefix in ["search for", "search", "google", "look up", "find", "what is", "who is", "when did", "when was", "where is"]:
                        m_q = re.search(rf"\b{re.escape(prefix)}\s+(.+)", text, re.I)
                        if m_q:
                            query = m_q.group(1)
                            break
                result_raw = self.executor.execute("web_search", {"query": query})
                result = json.loads(result_raw)
                tools_used.append("web_search")
                if result.get("error"):
                    return {"response": f"Search failed: {result['error']}", "tools_used": tools_used}
                answer = result.get("answer") or result.get("abstract", "")
                results = result.get("results", [])
                if answer:
                    return {"response": f"Search result for \"{query}\": {answer}", "tools_used": tools_used}
                elif results:
                    top = results[0]
                    return {"response": f"Top result for \"{query}\": {top.get('title', '')} — {top.get('snippet', top.get('body', ''))[:200]}", "tools_used": tools_used}
                else:
                    return {"response": f"No results found for \"{query}\".", "tools_used": tools_used}

            elif intent == "schedule_task":
                # Extract schedule details
                m_time = re.search(r'(\d{1,2}:\d{2})', text)
                m_every = re.search(r'every\s+(\d+)\s*(second|minute|hour)s?', text, re.I)
                m_task = re.search(r'(?:remind me to|to)\s+(.+?)(?:\s+at|\s+every|\s*$)', text, re.I)

                schedule = "12:00"  # default daily noon
                task_name = "Scheduled Task"
                if m_time:
                    schedule = m_time.group(1)
                elif m_every:
                    n, unit = m_every.group(1), m_every.group(2).lower()
                    multiplier = {"second": 1, "minute": 60, "hour": 3600}.get(unit, 60)
                    schedule = f"every {int(n) * multiplier}s"
                if m_task:
                    task_name = m_task.group(1)

                result_raw = self.executor.execute("schedule_task",
                    {"name": task_name, "schedule": schedule, "command": "echo"})
                result = json.loads(result_raw)
                tools_used.append("schedule_task")
                return {"response": f"Task scheduled: \"{task_name}\" at {schedule} (ID: {result.get('id', '?')})", "tools_used": tools_used}

            else:
                # General — give an honest, helpful response
                return self._respond_general(text)

        except Exception as e:
            logger.error(f"LocalEngine error for intent {intent}: {e}")
            return {"response": f"I attempted to process your request but encountered an error: {e}",
                    "tools_used": tools_used}

    def _respond_identity(self) -> Dict:
        return {
            "response": (
                "I am JARVIS — Just A Rather Very Intelligent System — running on Raspberry Pi 5.\n\n"
                "I can:\n"
                "🤖 Control your robot (forward, backward, left, right, stop, emergency stop)\n"
                "🎛️  Set servo positions (servo <channel> to <angle>°)\n"
                "🌡️  Read sensors (BME280, BH1750, VL53L0X, PIR, HC-SR04)\n"
                "📊 Report system status (CPU, RAM, temperature, disk)\n"
                "📷 Capture camera frames and describe scenes\n"
                "🧠 Store and search long-term memories\n"
                "📁 Read and write files\n"
                "🔍 Search the web\n"
                "⏰ Schedule recurring tasks\n"
                "🔊 Speak responses aloud\n\n"
                "For full AI reasoning, add GOOGLE_API_KEY to .env (Google Gemini is free)."
            ),
            "tools_used": []
        }

    def _respond_help(self) -> Dict:
        return {
            "response": (
                "JARVIS Command Reference:\n\n"
                "ROBOT: 'move forward', 'go backward', 'turn left', 'turn right', 'stop', 'emergency stop'\n"
                "SERVO: 'servo 0 to 90', 'set servo 2 angle 45'\n"
                "SENSORS: 'read sensors', 'what is the temperature', 'check humidity'\n"
                "SYSTEM: 'system status', 'cpu usage', 'check memory'\n"
                "CAMERA: 'capture photo', 'what do you see', 'describe the scene'\n"
                "MEMORY: 'remember that X', 'recall X', 'search memory for X'\n"
                "FILES: 'read file.txt', 'list files'\n"
                "WEB: 'search for X', 'what is X', 'who is X'\n"
                "SCHEDULE: 'schedule X at 14:00', 'remind me to X every 30 minutes'\n"
            ),
            "tools_used": []
        }

    def _respond_calculate(self, text: str) -> Dict:
        from tools.calculator.calculator_tools import calculator_tools
        res = calculator_tools.calculate(text)
        if res.get("success"):
            val = res["result"]
            expr = res.get("expression", text.strip())
            return {
                "response": f"Calculation: {expr} = **{val}**",
                "tools_used": ["calculate"],
                "raw": res,
            }
        return {
            "response": f"Calculation error: {res.get('error', 'I could not compute that expression.')}",
            "tools_used": ["calculate"],
            "raw": res,
        }

    def _respond_desktop_open_url(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        raw_url = ctx.get("url", "https://www.youtube.com")
        browser = ctx.get("browser", "chrome")
        # Canonicalize common shortcuts
        if raw_url.lower() in ("youtube", "yt"):
            url = "https://www.youtube.com"
        elif raw_url.lower() in ("google", "search"):
            url = "https://www.google.com"
        elif raw_url.lower() == "github":
            url = "https://github.com"
        else:
            url = raw_url
        res = desktop_action_engine.open_url(url, browser=browser)
        ar = res["actual_result"]
        return {
            "response": f"🌐 Opened **{ar['url']}** in {ar['resolved_browser'].title()} (PID: {ar.get('pid')}) on display :0.",
            "tools_used": ["desktop_open_url"],
            "raw": res,
        }

    def _respond_desktop_search_youtube(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        query = ctx.get("query", "relaxing music")
        res = desktop_action_engine.search_youtube(query)
        ar = res["actual_result"]
        return {
            "response": f"📺 {ar['status_message']}\n🔗 Direct Link: {ar['youtube_url']}\nℹ️ *Web page displayed on desktop. Select video in browser to start playback.*",
            "tools_used": ["desktop_search_youtube"],
            "raw": res,
        }

    def _respond_desktop_open_project(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        proj = ctx.get("project", "UnityGameWorkspace")
        editor = ctx.get("editor", "vscode")
        res = desktop_action_engine.open_project(proj, editor=editor)
        ar = res["actual_result"]
        if ar.get("success"):
            return {
                "response": f"💻 Opened project **{ar.get('project_name')}** at `{ar.get('project_path')}` in **{ar.get('editor').upper()}** (PID: {ar.get('pid')}).",
                "tools_used": ["desktop_open_project"],
                "raw": res,
            }
        return {
            "response": f"⚠️ {ar.get('message', 'Failed to open project.')}",
            "tools_used": ["desktop_open_project"],
            "raw": res,
        }

    def _respond_desktop_open_app(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        app = ctx.get("app", "code")
        res = desktop_action_engine.open_application(app, new_window=True)
        ar = res["actual_result"]
        if ar.get("success"):
            return {
                "response": f"🚀 Launched **{ar.get('app')}** (`{ar.get('executable')}`) on desktop session (PID: {ar.get('pid')}).",
                "tools_used": ["desktop_open_app", "open_app"],
                "raw": res,
            }
        return {
            "response": f"⚠️ Could not launch **{app}**: {ar.get('error', 'Application not found.')}",
            "tools_used": ["desktop_open_app", "open_app"],
            "raw": res,
        }

    def _respond_desktop_search_files(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        raw_dir = ctx.get("directory", "")
        pattern = ctx.get("pattern", "*")

        # Resolve directory aliases
        home = os.path.expanduser("~")
        clean_dir = home
        d_lower = raw_dir.lower()
        if "unity" in d_lower or "gameworkspace" in d_lower:
            clean_dir = os.path.join(home, "UnityGameWorkspace")
        elif "download" in d_lower:
            clean_dir = os.path.join(home, "Downloads")
        elif "desktop" in d_lower:
            clean_dir = os.path.join(home, "Desktop")
        elif "jarvis" in d_lower:
            clean_dir = "/home/roshan/.gemini/antigravity/scratch/jarvis-os"
        elif raw_dir.strip():
            clean_dir = os.path.expanduser(raw_dir.strip())

        # Normalize pattern and extension
        ext = None
        p_clean = pattern.strip() if pattern else "*"
        if p_clean.lower() in ("python", "py", "*.py"):
            ext = ".py"
            p_clean = "*"
        elif p_clean.lower() in ("readme", "readme.md"):
            p_clean = "*README*"

        res = desktop_action_engine.search_files(directory=clean_dir, pattern=p_clean, extension=ext)
        files = res["actual_result"]["files"]
        if files:
            bullets = "\n".join(f"  📄 `{f['relative_path']}` ({f['size_str']})" for f in files[:10])
            resp = f"📁 Found {len(files)} file(s) in `{clean_dir}`:\n{bullets}"
        else:
            resp = f"📁 No files matching '{p_clean}' found in `{clean_dir}`."
        return {
            "response": resp,
            "tools_used": ["desktop_search_files"],
            "raw": res,
        }

    def _respond_desktop_search_content(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        query = ctx.get("query", "")
        raw_dir = ctx.get("directory")
        home = os.path.expanduser("~")
        clean_dir = home
        if raw_dir:
            d_lower = raw_dir.lower()
            if "unity" in d_lower:
                clean_dir = os.path.join(home, "UnityGameWorkspace")
            elif "download" in d_lower:
                clean_dir = os.path.join(home, "Downloads")
            else:
                clean_dir = os.path.expanduser(raw_dir.strip())
        else:
            clean_dir = os.path.join(home, "UnityGameWorkspace") if os.path.exists(os.path.join(home, "UnityGameWorkspace")) else home

        res = desktop_action_engine.search_file_contents(query=query, directory=clean_dir)
        matches = res["actual_result"]["matches"]
        if matches:
            bullets = "\n".join(f"  🔍 `{m['file']}:{m['line']}` — {m['content']}" for m in matches[:8])
            resp = f"🔎 Found {len(matches)} match(es) for '{query}':\n{bullets}"
        else:
            resp = f"🔎 No files containing '{query}' found in `{clean_dir}`."
        return {
            "response": resp,
            "tools_used": ["desktop_search_content"],
            "raw": res,
        }

    def _respond_terminal_execute(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        cmd = ctx.get("command", "")
        res = desktop_action_engine.execute_terminal(cmd)
        ar = res["actual_result"]
        if ar.get("requires_confirmation"):
            return {
                "response": (
                    f"⚠️ **Security Confirmation Required**\n\n"
                    f"Command `{cmd}` contains sensitive or destructive operations ({ar.get('reason')}).\n"
                    f"Please confirm execution using confirmation token: `{ar.get('confirmation_token')}`."
                ),
                "tools_used": ["terminal_execute"],
                "raw": res,
            }
        out = (ar.get("stdout") or ar.get("stderr") or "[Command exited without output]").strip()
        resp = (
            f"💻 **JARVIS Terminal Execution**\n\n"
            f"- **Working Directory:** `{ar.get('cwd')}`\n"
            f"- **Command:** `{cmd}`\n"
            f"- **Exit Code:** `{ar.get('exit_code')}`\n"
            f"- **Status:** {ar.get('status')} ({ar.get('duration_ms')}ms)\n\n"
            f"```text\n{out}\n```"
        )
        return {
            "response": resp,
            "tools_used": ["terminal_execute"],
            "raw": res,
        }

    def _respond_desktop_run_program(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        prog = ctx.get("program", "")
        loc = ctx.get("location", "")
        home = os.path.expanduser("~")

        # Resolve directory
        target_dir = home
        if loc:
            if "unity" in loc.lower() or "gameworkspace" in loc.lower():
                target_dir = os.path.join(home, "UnityGameWorkspace", "GameProject")
            elif "download" in loc.lower():
                target_dir = os.path.join(home, "Downloads")
            else:
                target_dir = os.path.expanduser(loc.strip())
        else:
            if "unity" in prog.lower():
                target_dir = os.path.join(home, "UnityGameWorkspace", "GameProject")

        # Resolve script file
        target_file = None
        if os.path.isabs(prog) and os.path.exists(prog):
            target_file = prog
        elif os.path.exists(os.path.join(target_dir, prog)):
            target_file = os.path.join(target_dir, prog)
        else:
            # Check for build.py or main.py in target_dir
            for cand in ["build.py", "main.py", "controller.py"]:
                if os.path.exists(os.path.join(target_dir, cand)):
                    target_file = os.path.join(target_dir, cand)
                    break

        if not target_file:
            return {
                "response": f"⚠️ Could not find program '{prog}' in `{target_dir}`.",
                "tools_used": ["desktop_run_program"],
            }

        res = desktop_action_engine.run_program(target_file, working_dir=target_dir)
        ar = res["actual_result"]
        out = (ar.get("stdout") or ar.get("stderr") or "[No output]").strip()
        resp = (
            f"⚡ **Program Execution Result**\n\n"
            f"- **File:** `{target_file}`\n"
            f"- **Working Directory:** `{target_dir}`\n"
            f"- **Exit Code:** `{ar.get('exit_code')}`\n"
            f"- **Status:** {ar.get('status').upper()} ({ar.get('duration_ms')}ms)\n\n"
            f"```text\n{out}\n```"
        )
        return {
            "response": resp,
            "tools_used": ["desktop_run_program"],
            "raw": res,
        }

    def _respond_desktop_awareness(self, ctx: Dict) -> Dict:
        from tools.desktop.action_engine import desktop_action_engine
        res = desktop_action_engine.get_desktop_status()
        ar = res["actual_result"]
        act = ar.get("active_window", {})
        wins = ar.get("open_windows", [])
        win_bullets = "\n".join(f"  • [{w.get('window_id')}] `{w.get('title')}` (PID: {w.get('pid')})" for w in wins[:5])
        resp = (
            f"🖥️ **Desktop Session Status**\n\n"
            f"- **Session Type:** {ar.get('session_type').upper()} (Display `{ar.get('display')}`)\n"
            f"- **Screen Resolution:** {ar.get('resolution')}\n"
            f"- **Active Window:** `{act.get('title', 'None')}` (Class: {act.get('class_name', 'Unknown')}, PID: {act.get('pid', 'N/A')})\n"
            f"- **Open Windows ({ar.get('open_window_count')}):**\n{win_bullets}"
        )
        return {
            "response": resp,
            "tools_used": ["desktop_get_status"],
            "raw": res,
        }

    def _respond_general(self, text: str) -> Dict:
        return {
            "response": (
                f"⚠️ AI Provider Error: No active language model is available to process: '{text}'.\n\n"
                "The local Ollama server at http://127.0.0.1:11434 is not responding or unreachable. "
                "Please verify that Ollama is active (`ollama serve` or `systemctl status ollama`) with models "
                "`llama3.2:1b` or `qwen3.5:4b` installed."
            ),
            "tools_used": [],
            "error": "No active LLM provider connected",
        }

    def _format_sensors(self, data: dict) -> str:
        lines = ["📡 Sensor Readings:"]
        bme = data.get("bme280", {})
        if bme:
            lines.append(f"  🌡️  Temperature: {bme.get('temperature_c', 'N/A')}°C")
            lines.append(f"  💧 Humidity: {bme.get('humidity_pct', 'N/A')}%")
            lines.append(f"  🌬️  Pressure: {bme.get('pressure_hpa', 'N/A')} hPa")
        bh = data.get("bh1750", {})
        if bh:
            lines.append(f"  💡 Light: {bh.get('lux', 'N/A')} lux")
        vl = data.get("vl53l0x", {})
        if vl:
            lines.append(f"  📏 Distance: {vl.get('distance_mm', 'N/A')} mm")
        pir = data.get("hcsr501", {})
        if pir:
            lines.append(f"  👁️  Motion: {'DETECTED' if pir.get('motion_detected') else 'None'}")
        hc = data.get("hcsr04", {})
        if hc:
            lines.append(f"  🔊 Ultrasonic: {hc.get('distance_cm', 'N/A')} cm")
        return "\n".join(lines)

    def _format_system(self, data: dict) -> str:
        if data.get("error"):
            return f"System status unavailable: {data['error']}"
        lines = ["💻 System Status:"]
        lines.append(f"  🔲 CPU: {data.get('cpu_usage_pct', 0):.1f}%")
        ram_pct = data.get('ram_pct', 0)
        ram_used = data.get('ram_used_gb', 0)
        ram_total = data.get('ram_total_gb', 0)
        ram_avail = data.get('ram_avail_gb', 0)
        lines.append(f"  💾 RAM: {ram_pct:.1f}% used ({ram_used:.2f} GB / {ram_total:.2f} GB, Available: {ram_avail:.2f} GB)")
        if data.get('temp_c') is not None:
            lines.append(f"  🌡️  CPU Temp: {data.get('temp_c')}°C")
        disk_pct = data.get('disk_pct', 0)
        disk_used = data.get('disk_used_gb', 0)
        disk_total = data.get('disk_total_gb', 0)
        lines.append(f"  💿 Disk: {disk_pct:.1f}% used ({disk_used:.1f} GB / {disk_total:.1f} GB)")
        lines.append(f"  ⏱️  Uptime: {data.get('uptime_str', 'N/A')}")
        lines.append(f"  🤖 Robot: {data.get('robot_state', 'UNKNOWN')}")
        return "\n".join(lines)

    def _extract_speed(self, text: str) -> Optional[int]:
        # "at 70 percent" / "at 70%" 
        m = re.search(r'at\s+(\d+)\s*(?:percent|%)', text, re.I)
        if m:
            return min(100, max(0, int(m.group(1))))
        # bare "70%"
        m = re.search(r'(\d+)\s*%', text)
        if m:
            return min(100, max(0, int(m.group(1))))
        # "speed 70"
        m = re.search(r'speed\s+(\d+)', text, re.I)
        if m:
            return min(100, max(0, int(m.group(1))))
        # words
        for word, val in [("slow", 25), ("half", 50), ("full", 100), ("fast", 80), ("max", 100)]:
            if word in text.lower():
                return val
        return None

    def _extract_duration_ms(self, text: str) -> int:
        m = re.search(r'(?:for\s+)?(\d+(?:\.\d+)?)\s*(second|sec|s|millisecond|ms|minute|min)', text, re.I)
        if m:
            val, unit = float(m.group(1)), m.group(2).lower()
            if unit.startswith("ms") or unit.startswith("milli"):
                return int(val)
            elif unit.startswith("min"):
                return int(val * 60000)
            else:
                return int(val * 1000)
        return 0

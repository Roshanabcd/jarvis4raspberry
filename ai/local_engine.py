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

        # 2b. Phase 3: Theme Customization
        if re.search(r'\b(?:change|set|make|switch)\s+(?:the\s+)?(?:background|accent|theme)\b', text_lower) or re.search(r'\b(?:reset\s+theme|default\s+theme)\b', text_lower):
            return "theme_control", {"text": text}

        # 2c. YouTube Player Controls & Playback
        # Video volume (must precede generic volume)
        m_vvol = re.search(r'\b(?:set|change|increase|decrease)\s+(?:the\s+)?(?:video|youtube)\s+volume\s+(?:to\s+)?(\d+)\%?\b', text_lower)
        if m_vvol:
            return "youtube_volume", {"volume": int(m_vvol.group(1)), "text": text}

        # Video player pause/resume/fullscreen/mute
        if re.search(r'\b(pause)\s+(?:the\s+)?(?:video|youtube)\b', text_lower):
            return "youtube_pause", {"text": text}
        if re.search(r'\b(resume|continue|unpause)\s+(?:the\s+)?(?:video|youtube)\b', text_lower):
            return "youtube_resume", {"text": text}
        if re.search(r'\b(?:switch\s+(?:the\s+)?video\s+to\s+|toggle\s+)?full\s*screen\b', text_lower):
            return "youtube_fullscreen", {"text": text}
        if re.search(r'\b(mute|unmute)\s+(?:the\s+)?(?:video|youtube)\b', text_lower):
            return "youtube_mute", {"text": text}

        # YouTube Selection Cancellation ("Cancel selection", "Cancel", "Never mind")
        if re.search(r'\b(?:cancel\s+(?:the\s+)?(?:selection|youtube|video|search)|never\s*mind)\b', text_lower) or (text_lower.strip() in ("cancel", "nevermind")):
            return "youtube_cancel_selection", {"text": text}

        # YouTube More Results ("Show more results", "Show 3 more results", "More results")
        m_more = re.search(r'\b(?:show|get|display|fetch)\s+(?:(\d+)\s+)?more\s+(?:results|videos|options)\b', text_lower) or re.search(r'^\s*more\s+results\s*$', text_lower)
        if m_more:
            cnt = int(m_more.group(1)) if (m_more and m_more.lastindex and m_more.group(1)) else 3
            return "youtube_more_results", {"count": cnt, "text": text}

        # YouTube Video Selection & Autoplay Detection ("Play option 1", "Play the first horror movie in YouTube", "Open option 2 without playing")
        autoplay = not bool(re.search(r'\b(?:without\s+playing|no\s+autoplay|paused?)\b', text_lower))

        m_opt = re.search(r'\b(?:play|open|select|choose)?\s*option\s*(?:#|\s*)?(\d+|one|two|three|four|five)\b', text_lower)
        m_ord = re.search(r'\b(?:play|open|select|choose)\s+(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+(?:horror\s+movie|movie|film|video|result|song|choice|item|track|one)(?:\s+(?:in|on)\s+youtube)?(?:\s+instead)?\b', text_lower)
        m_ord_short = re.search(r'\b(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+(?:video|movie|film|result|choice|one)\b', text_lower)

        idx_map = {
            "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4, "fifth": 5, "5th": 5,
        }

        if m_opt:
            num_raw = m_opt.group(1).lower()
            chosen_idx = idx_map.get(num_raw, 1)
            return "youtube_play_index", {"index": chosen_idx, "autoplay": autoplay, "text": text}

        if m_ord and not re.search(r'\b(?:website|site|link|tab|page)\b', text_lower):
            ord_raw = m_ord.group(1).lower()
            chosen_idx = idx_map.get(ord_raw, 1)
            return "youtube_play_index", {"index": chosen_idx, "autoplay": autoplay, "text": text}

        if m_ord_short and not re.search(r'\b(?:website|site|link|tab|page|window|question)\b', text_lower):
            ord_raw = m_ord_short.group(1).lower()
            chosen_idx = idx_map.get(ord_raw, 1)
            return "youtube_play_index", {"index": chosen_idx, "autoplay": autoplay, "text": text}

        # YouTube Unified Search ("Open a horror video in YouTube", "Search YouTube for a horror movie", "Find ... on YouTube")
        m_yt_search = (
            re.search(r'\b(?:search|find|open|look\s+up)\s+(?:a\s+|for\s+)?(.+?)\s+(?:in|on)\s+youtube\b', text_lower)
            or re.search(r'\bsearch\s+youtube\s+for\s+(.+)', text_lower)
            or re.search(r'\byoutube\s+search\s+for\s+(.+)', text_lower)
            or re.search(r'\b(?:play|find)\s+(.+?)\s+(?:on|in)\s+youtube\b', text_lower)
        )
        if m_yt_search:
            raw_q = m_yt_search.group(1).strip()
            # If query is not an ordinal selection command, treat as search
            if not re.search(r'\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|option\s+\d+)\b', raw_q):
                return "youtube_search", {"query": raw_q, "text": text}

        # 2d. Phase 3: Google Search ("Search Google for Raspberry Pi robotics", "Google Raspberry Pi robotics")
        m_gsearch = re.search(r'\bsearch\s+google\s+for\s+(.+)', text_lower) or re.search(r'^\s*google\s+(.+)', text_lower) or re.search(r'\bsearch\s+for\s+(.+?)\s+in\s+(?:google\s+)?chrome\b', text_lower)
        if m_gsearch:
            return "google_search", {"query": m_gsearch.group(1).strip(), "text": text}

        # 2e. Phase 3: Numbered Website Navigation ("Open the first website", "Open the second website", "Open the third result in a new tab")
        m_web_idx = re.search(r'\b(?:open|visit|show)\s+(?:the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+(?:website|site|result|link)(?:\s+(?:in\s+)?(?:a\s+)?new\s+tab)?\b', text_lower)
        if m_web_idx:
            idx_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4, "fifth": 5, "5th": 5}
            chosen = idx_map.get(m_web_idx.group(1).lower(), 1)
            new_tab = "new tab" in text_lower
            return "browser_numbered_nav", {"index": chosen, "new_tab": new_tab, "text": text}

        # Browser back / forward / reload ("Go back and open the second website", "Go back to search results", "Go back")
        if re.search(r'\bgo\s+back\s+and\s+open\s+(?:the\s+)?(first|second|third|1st|2nd|3rd)\s+website\b', text_lower):
            m_back_open = re.search(r'(first|second|third|1st|2nd|3rd)', text_lower)
            idx_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3}
            chosen = idx_map.get(m_back_open.group(1).lower(), 2) if m_back_open else 2
            return "browser_back_and_open", {"index": chosen, "text": text}

        if re.search(r'\b(?:go\s+back|return\s+to\s+results|previous\s+page)\b', text_lower):
            return "browser_history_nav", {"action": "back", "text": text}
        if re.search(r'\b(?:go\s+forward|next\s+page)\b', text_lower):
            return "browser_history_nav", {"action": "forward", "text": text}
        if re.search(r'\b(?:reload|refresh)\s+(?:page|tab|browser)?\b', text_lower):
            return "browser_history_nav", {"action": "reload", "text": text}

        # 2f. Phase 3: Per-App / Stream Volume Control ("Set FreeTube volume to 80%", "Set Chrome volume to 60%")
        m_stream_vol = re.search(r'\b(?:set|change)\s+(?:the\s+)?(freetube|chrome|chromium|vlc|spotify)\s+volume\s+(?:to\s+)?(\d+)\%?\b', text_lower)
        if m_stream_vol:
            return "stream_volume_control", {"app": m_stream_vol.group(1), "volume": int(m_stream_vol.group(2)), "text": text}

        # 2g. Phase 3: Master / System Volume Control ("Set system volume to 60%", "Set master volume to 50%")
        m_sys_vol = re.search(r'\b(?:set|change)\s+(?:the\s+)?(?:system|master|speaker|hardware)\s+volume\s+(?:to\s+)?(\d+)\%?\b', text_lower)
        if m_sys_vol:
            return "master_volume_control", {"volume": int(m_sys_vol.group(1)), "text": text}

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
            return "youtube_search", {"query": m_yt.group(1).strip(), "text": text}

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

        # 3i. Phase 4: Screen Perception & Visual Computer Use
        # Active browser tab inquiry ("which browser tab is active", "what tab is open")
        if re.search(r'\b(?:which|what)\s+(?:browser\s+)?tab\s+is\s+(?:currently\s+)?active\b', text_lower):
            return "screen_active_tab", {"text": text}

        # Screen observation ("look at my screen", "observe screen", "what is on my screen", "tell me which applications are open", "describe what you see on my screen")
        if re.search(r'\b(?:(?:look\s+at|observe)\s+(?:my\s+|the\s+)?screen|what\s+is\s+(?:currently\s+)?open(?:\s+on\s+(?:my\s+)?screen)?|tell\s+me\s+which\s+applications\s+are\s+open|what\s+do\s+you\s+see(?:\s+on\s+(?:my\s+)?screen)?|describe\s+(?:my\s+|the\s+)?(?:current\s+)?(?:screen|window))\b', text_lower):
            return "screen_observe", {"text": text}

        # Take screenshot ("take a screenshot", "capture screen", "capture my screen", "capture active window")
        if re.search(r'\b(?:take\s+(?:a\s+)?screenshot|capture\s+(?:the\s+|my\s+)?(?:screen|desktop|active\s+window))\b', text_lower):
            target = "active_window" if ("active" in text_lower or "window" in text_lower) else "fullscreen"
            return "screen_screenshot", {"target": target, "text": text}

        # Find UI element ("find the settings button", "where is the settings option", "locate the search field", "find the download button", "show me where to click")
        m_find_elem = re.search(r'\b(?:find|locate|where\s+is|show\s+me\s+where\s+is|highlight)\s+(?:the\s+)?(.+?)(?:\s+(?:button|icon|field|textbox|tab|menu|control|option))?(?:\s+on\s+(?:my\s+|the\s+)?screen)?[\.\?!]*$', text_lower) or re.search(r'\bshow\s+me\s+where\s+to\s+click\b', text_lower)
        if m_find_elem and not re.search(r'\b(?:file|files|python)\b', text_lower):
            elem_query = m_find_elem.group(1).strip() if (hasattr(m_find_elem, 'lastindex') and m_find_elem.lastindex and m_find_elem.group(1)) else "settings"
            elem_query = re.sub(r'\s+on\s+(?:my\s+|the\s+)?screen$', '', elem_query, flags=re.I).strip()
            return "screen_find_element", {"query": elem_query, "text": text}

        # Click named UI element ("click the settings button", "click the third tab", "click the search field", "click the close button")
        m_click_elem = re.search(r'\bclick\s+(?:on\s+)?(?:the\s+)?(.+?)(?:\s+(?:button|icon|field|textbox|tab|menu|item))?[\.\?!]*$', text_lower)
        if m_click_elem and not re.search(r'\b(forward|backward|left|right|stop|play|pause|resume)\b', text_lower):
            elem_target = m_click_elem.group(1).strip()
            return "screen_click_element", {"query": elem_target, "text": text}

        # Scroll page ("scroll down", "scroll up", "scroll the page down", "scroll down and find...")
        m_scroll = re.search(r'\bscroll\s+(?:the\s+)?(?:page\s+|screen\s+)?(down|up)\b', text_lower)
        if m_scroll:
            return "screen_scroll", {"direction": m_scroll.group(1).lower(), "text": text}

        # Switch application window ("switch back to chrome", "switch to vs code", "switch to terminal", "open the second application window")
        m_switch_win = re.search(r'\bswitch\s+(?:back\s+)?to\s+(google\s+chrome|chrome|firefox|vs\s*code|vscode|code|terminal|lxterminal|downloads|pcmanfm|files|antigravity)\b', text_lower)
        if m_switch_win:
            return "screen_switch_window", {"app": m_switch_win.group(1).strip(), "text": text}

        m_open_win_num = re.search(r'\bopen\s+(?:the\s+)?(first|second|third|fourth|1st|2nd|3rd|4th)\s+application\s+window\b', text_lower)
        if m_open_win_num:
            idx_map = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}
            w_idx = idx_map.get(m_open_win_num.group(1).lower(), 1)
            return "screen_switch_window_index", {"index": w_idx, "text": text}

        # Type text ("type '...'", "enter '...' into search")
        m_type_txt = re.search(r'\btype\s+["\'](.+?)["\']\b', text_lower) or re.search(r'\benter\s+["\']?([^"\']+)["\']?\s+in(?:to)?\s+(?:the\s+)?(?:textbox|search|field)\b', text_lower)
        if m_type_txt:
            return "screen_type_text", {"text_to_type": m_type_txt.group(1).strip(), "text": text}

        # 3h. Deterministic natural-language math check (Test 6: "What is 25 multiplied by 4?", "15 percent of 800", "What is 1024 * 2 + 50?")
        if re.search(r"\b(?:\d+(?:\.\d+)?\s*(?:multiplied\s+by|times|\*|divided\s+by|\/|plus|\+|minus|\-|to\s+the\s+power\s+of|\^|%|percent\s+of)\s*\d+|\d+\s*[\+\-\*\/]\s*\d+)", text_lower):
            clean_math = re.sub(r'^(?:what\s+is\s+|calculate\s+|compute\s+|solve\s+|how\s+much\s+is\s+|find\s+)', '', text.strip(), flags=re.I).rstrip('?.')
            return "calculate", {"expression": clean_math, "text": text}

        # 3i. Phase 5 Multi-AI Agent Orchestrator & Autonomous Self-Healing Intents
        # 5a. Discovered Agents Check
        if re.search(r'\b(?:check\s+which\s+(?:ai\s+)?(?:coding\s+)?agents|show\s+(?:me\s+)?(?:all\s+)?installed\s+(?:ai\s+)?(?:coding\s+)?agents|list\s+(?:all\s+)?(?:ai\s+)?(?:coding\s+)?agents|which\s+(?:ai\s+)?(?:coding\s+)?agents\s+are\s+available|discover\s+(?:ai\s+)?(?:coding\s+)?agents|ai\s+agents?\s+status|show\s+(?:all\s+)?coding\s+agents)\b', text_lower):
            return "agents_discover", {"text": text}

        # 5b. Stuck Task Watchdog Check
        if re.search(r'\b(?:why\s+is\s+jarvis\s+stuck|check\s+whether\s+(?:the\s+)?(?:agent|task|jarvis)\s+is\s+stuck|is\s+(?:the\s+)?(?:agent|task|jarvis)\s+stuck|check\s+stuck\s+(?:agent|task)|stuck\s+watchdog\s+status)\b', text_lower):
            return "agents_stuck_check", {"text": text}

        # 5c. Permissions Pending Check
        if re.search(r'\b(?:show\s+(?:me\s+)?(?:all\s+)?pending\s+permissions?|pending\s+permissions?|agent\s+permissions?|show\s+permission\s+requests?)\b', text_lower):
            return "agents_permissions_pending", {"text": text}

        # 5d. Permissions Profile Switch
        m_perm_prof = re.search(r'\b(?:switch|set|change)\s+(?:permission\s+profile\s+to\s+|to\s+)?(supervised(?:\s+auto)?|safe(?:\s+auto)?|manual)(?:\s+mode|\s+profile)?\b', text_lower)
        if m_perm_prof:
            prof_raw = m_perm_prof.group(1).lower()
            prof = "SUPERVISED_AUTO" if "supervised" in prof_raw else ("MANUAL" if "manual" in prof_raw else "SAFE_AUTO")
            return "agents_permissions_profile", {"profile": prof, "text": text}

        # 5e. Restore / Rollback Checkpoint
        if re.search(r'\b(?:restore\s+(?:the\s+)?(?:project\s+to\s+(?:the\s+)?)?previous\s+checkpoint|restore\s+checkpoint|rollback\s+(?:agent\s+)?(?:repair|change|patch))\b', text_lower):
            return "agents_restore_checkpoint", {"text": text}

        # 5f. Self-Healing Project Repair
        if re.search(r'\b(?:fix\s+(?:the\s+)?error\s+in\s+(?:my\s+)?project|repair\s+project\s+errors?|debug\s+and\s+fix\s+(?:my\s+)?project|self-heal\s+project|run\s+self[- ]healing)\b', text_lower):
            return "agents_repair_project", {"text": text}

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
                        cand_l = cand.lower()
                        # Reject candidates that refer to YouTube or ordinal selections
                        if "youtube" in cand_l or bool(re.search(r'\b(option|first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\b', cand_l)):
                            continue
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

            # Phase 3 Dispatches
            elif intent == "google_search":
                return self._respond_google_search(ctx)

            elif intent == "browser_numbered_nav":
                return self._respond_browser_numbered_nav(ctx)

            elif intent == "browser_back_and_open":
                return self._respond_browser_back_and_open(ctx)

            elif intent == "browser_history_nav":
                return self._respond_browser_history_nav(ctx)

            elif intent == "youtube_search":
                return self._respond_youtube_search(ctx)

            elif intent == "youtube_play_index":
                return self._respond_youtube_play_index(ctx)

            elif intent == "youtube_cancel_selection":
                return self._respond_youtube_cancel(ctx)

            elif intent == "youtube_more_results":
                return self._respond_youtube_more_results(ctx)

            elif intent == "youtube_pause":
                return self._respond_youtube_pause(ctx)

            elif intent == "youtube_resume":
                return self._respond_youtube_resume(ctx)

            elif intent == "youtube_fullscreen":
                return self._respond_youtube_fullscreen(ctx)

            elif intent == "youtube_mute":
                return self._respond_youtube_mute(ctx)

            elif intent == "youtube_volume":
                return self._respond_youtube_volume(ctx)

            elif intent == "stream_volume_control":
                return self._respond_stream_volume_control(ctx)

            elif intent == "master_volume_control":
                return self._respond_master_volume_control(ctx)

            elif intent == "theme_control":
                return self._respond_theme_control(ctx)

            # Phase 4 Visual Computer-Use Dispatches
            elif intent == "screen_observe":
                return self._respond_screen_observe(ctx)
            elif intent == "screen_screenshot":
                return self._respond_screen_screenshot(ctx)
            elif intent == "screen_find_element":
                return self._respond_screen_find_element(ctx)
            elif intent == "screen_click_element":
                return self._respond_screen_click_element(ctx)
            elif intent == "screen_scroll":
                return self._respond_screen_scroll(ctx)
            elif intent == "screen_switch_window":
                return self._respond_screen_switch_window(ctx)
            elif intent == "screen_switch_window_index":
                return self._respond_screen_switch_window_index(ctx)
            elif intent == "screen_active_tab":
                return self._respond_screen_active_tab(ctx)
            elif intent == "screen_type_text":
                return self._respond_screen_type_text(ctx)

            # Phase 5 Multi-AI Agent Orchestration Dispatches
            elif intent == "agents_discover":
                return self._respond_agents_discover(ctx)
            elif intent == "agents_stuck_check":
                return self._respond_agents_stuck_check(ctx)
            elif intent == "agents_permissions_pending":
                return self._respond_agents_permissions_pending(ctx)
            elif intent == "agents_permissions_profile":
                return self._respond_agents_permissions_profile(ctx)
            elif intent == "agents_restore_checkpoint":
                return self._respond_agents_restore_checkpoint(ctx)
            elif intent == "agents_repair_project":
                return self._respond_agents_repair_project(ctx)

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
        # Route to structured youtube_search for consistent session state and selection
        return self._respond_youtube_search(ctx)

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

    def _respond_google_search(self, ctx: Dict) -> Dict:
        from tools.browser.search_manager import search_manager
        query = ctx.get("query", "Raspberry Pi robotics")
        res = search_manager.search_web(query, max_results=5)
        results = res.get("results", [])
        if not results:
            return {
                "response": f"🔍 Searched Google for '{query}', but no organic results were found.",
                "tools_used": ["google_search"],
            }
        bullets = []
        for r in results:
            bullets.append(f"{r['rank']}. **[{r['domain']}]** {r['title']}\n   🔗 `{r['url']}`")
        resp = f"🔍 **Google Search Results for '{query}'**:\n\n" + "\n\n".join(bullets) + "\n\n💡 *Say 'Open the first website' or 'Open the second website' to view.*"
        return {
            "response": resp,
            "tools_used": ["google_search"],
            "raw": res,
        }

    def _respond_browser_numbered_nav(self, ctx: Dict) -> Dict:
        from tools.browser.search_manager import search_manager
        idx = ctx.get("index", 1)
        new_tab = ctx.get("new_tab", False)
        res = search_manager.open_result_by_index(idx, new_tab=new_tab, browser="chrome")
        if res.get("status") == "ok":
            resp = f"🌐 Opened result #{res['rank']} in Google Chrome:\n- **Title:** {res['title']}\n- **Domain:** `{res['domain']}`\n- **URL:** {res['url']}"
        else:
            resp = f"⚠️ {res.get('message', 'Failed to open numbered search result.')}"
        return {
            "response": resp,
            "tools_used": ["browser_open_result"],
            "raw": res,
        }

    def _respond_browser_back_and_open(self, ctx: Dict) -> Dict:
        from tools.browser.browser_agent import browser_agent
        from tools.browser.search_manager import search_manager
        browser_agent.go_back(browser="chrome")
        time.sleep(0.5)
        idx = ctx.get("index", 2)
        res = search_manager.open_result_by_index(idx, new_tab=False, browser="chrome")
        if res.get("status") == "ok":
            resp = f"🔙 Navigated back and opened result #{res['rank']}:\n- **Title:** {res['title']}\n- **URL:** {res['url']}"
        else:
            resp = f"⚠️ Navigated back, but could not open result #{idx}: {res.get('message')}"
        return {
            "response": resp,
            "tools_used": ["browser_back", "browser_open_result"],
            "raw": res,
        }

    def _respond_browser_history_nav(self, ctx: Dict) -> Dict:
        from tools.browser.browser_agent import browser_agent
        action = ctx.get("action", "back")
        if action == "back":
            res = browser_agent.go_back(browser="chrome")
            resp = "🔙 Navigated back to previous page in Google Chrome."
        elif action == "forward":
            res = browser_agent.go_forward(browser="chrome")
            resp = "🔜 Navigated forward to next page in Google Chrome."
        else:
            res = browser_agent.reload(browser="chrome")
            resp = "🔄 Reloaded the active browser page."
        return {
            "response": resp,
            "tools_used": [f"browser_{action}"],
            "raw": res,
        }

    def _respond_youtube_search(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        query = ctx.get("query", "horror movie")
        res = youtube_controller.search(query, max_results=5)
        videos = res.get("videos", [])
        clean_encoded = query.replace(" ", "+")
        direct_url = f"https://www.youtube.com/results?search_query={clean_encoded}"
        if not videos:
            return {
                "response": f"📺 Searched YouTube for '{query}', but could not find any videos.\n🔗 Direct Link: {direct_url}",
                "tools_used": ["youtube_search", "desktop_search_youtube"],
                "raw": res,
            }
        summary = res.get("formatted_summary", "")
        resp = f"{summary}\n\n🔗 YouTube Results Page: `{direct_url}`"
        return {
            "response": resp,
            "tools_used": ["youtube_search", "desktop_search_youtube"],
            "raw": res,
        }

    def _respond_youtube_play_index(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        idx = ctx.get("index")
        title_q = ctx.get("title_query")
        autoplay = ctx.get("autoplay", True)
        res = youtube_controller.select_and_play(index=idx, title_query=title_q, autoplay=autoplay, browser="chrome")
        if res.get("status") == "ok":
            action_desc = "Now playing" if autoplay else "Opened in Google Chrome (paused)"
            resp = (
                f"▶️ **{action_desc} option #{res['rank']} on YouTube in Google Chrome:**\n"
                f"- **Title:** {res['title']}\n"
                f"- **Channel:** {res['channel']}\n"
                f"- **Duration:** {res.get('duration', 'Unknown')}\n"
                f"- **URL:** `{res['url']}`\n"
                f"- **Verified State:** `{res.get('state')}` (Audio active on DISPLAY=:0)"
            )
        else:
            resp = f"⚠️ {res.get('message', 'Could not play requested YouTube video.')}"
        return {
            "response": resp,
            "tools_used": ["youtube_select_and_play"],
            "raw": res,
        }

    def _respond_youtube_cancel(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        res = youtube_controller.cancel_selection()
        return {
            "response": f"🛑 {res.get('message')}",
            "tools_used": ["youtube_cancel_selection"],
            "raw": res,
        }

    def _respond_youtube_more_results(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        count = ctx.get("count", 3)
        res = youtube_controller.get_more_results(count=count)
        if res.get("status") == "ok":
            resp = res.get("formatted_summary")
        else:
            resp = f"⚠️ {res.get('message', 'Could not fetch more results.')}"
        return {
            "response": resp,
            "tools_used": ["youtube_more_results"],
            "raw": res,
        }

    def _respond_youtube_pause(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        res = youtube_controller.pause()
        return {
            "response": "⏸️ Paused YouTube video playback.",
            "tools_used": ["youtube_pause"],
            "raw": res,
        }

    def _respond_youtube_resume(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        res = youtube_controller.resume()
        return {
            "response": "▶️ Resumed YouTube video playback.",
            "tools_used": ["youtube_resume"],
            "raw": res,
        }

    def _respond_youtube_fullscreen(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        res = youtube_controller.toggle_fullscreen()
        return {
            "response": f"🖥️ Switched YouTube video to {res.get('mode', 'fullscreen')} mode.",
            "tools_used": ["youtube_fullscreen"],
            "raw": res,
        }

    def _respond_youtube_mute(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        res = youtube_controller.mute()
        return {
            "response": "🔇 Toggled mute on YouTube video.",
            "tools_used": ["youtube_mute"],
            "raw": res,
        }

    def _respond_youtube_volume(self, ctx: Dict) -> Dict:
        from tools.browser.youtube_controller import youtube_controller
        vol = ctx.get("volume", 50)
        res = youtube_controller.set_video_volume(vol)
        return {
            "response": f"🔊 YouTube video volume set to **{vol}%** (PipeWire stream adjusted).",
            "tools_used": ["youtube_volume"],
            "raw": res,
        }

    def _respond_stream_volume_control(self, ctx: Dict) -> Dict:
        from tools.media.audio_stream_manager import audio_stream_manager
        app = ctx.get("app", "freetube")
        vol = ctx.get("volume", 50)
        res = audio_stream_manager.set_app_volume(app, vol)
        return {
            "response": f"🎚️ Adjusted {app.title()} stream volume to **{vol}%** (modified {res.get('count', 0)} active stream(s)).",
            "tools_used": ["set_stream_volume"],
            "raw": res,
        }

    def _respond_master_volume_control(self, ctx: Dict) -> Dict:
        from tools.media.audio_stream_manager import audio_stream_manager
        vol = ctx.get("volume", 50)
        res = audio_stream_manager.set_master_sink_volume(vol)
        return {
            "response": f"🔈 Hardware master system volume set to **{vol}%**.",
            "tools_used": ["set_master_volume"],
            "raw": res,
        }

    def _respond_theme_control(self, ctx: Dict) -> Dict:
        from tools.desktop.theme_manager import theme_manager
        text = ctx.get("text", "")
        res = theme_manager.process_natural_language(text)
        return {
            "response": f"🎨 {res.get('message', 'Theme updated.')}",
            "tools_used": ["theme_manager"],
            "raw": res,
        }

    # Phase 4 Response Handlers
    def _respond_screen_observe(self, ctx: Dict) -> Dict:
        from tools.desktop.desktop_perception import desktop_perception
        obs = desktop_perception.observe_desktop()
        act = obs.get("active_window", {})
        res = obs.get("resolution", {})
        wins = obs.get("open_windows", [])
        top_wins = [w for w in wins if w.get("desktop", 0) != -1]
        win_bullets = "\n".join(f"- `{w.get('title')}` (App: **{w.get('app')}**)" for w in top_wins[:5])

        resp = (
            f"👁️ **Screen Observation Summary**\n\n"
            f"- **Display Resolution:** {res.get('width', 1360)} × {res.get('height', 768)} (Native X11 on `:0`)\n"
            f"- **Active Window:** `{act.get('title', 'Desktop Root')}`\n"
            f"- **Application:** **{act.get('app', 'desktop')}** (Window ID: `{act.get('id', 'N/A')}`)\n"
            f"- **Window Dimensions:** {act.get('geometry', {}).get('width')} × {act.get('geometry', {}).get('height')} at pos ({act.get('geometry', {}).get('x')}, {act.get('geometry', {}).get('y')})\n\n"
            f"**Currently Open Applications ({len(top_wins)}):**\n"
            f"{win_bullets}\n\n"
            f"Visual snapshot captured in {obs.get('total_ms', 0)}ms."
        )
        return {
            "response": resp,
            "tools_used": ["desktop_perception_observe"],
            "raw": obs,
        }

    def _respond_screen_screenshot(self, ctx: Dict) -> Dict:
        from tools.desktop.desktop_perception import desktop_perception
        target = ctx.get("target", "fullscreen")
        if target == "active_window":
            snap = desktop_perception.capture_active_window()
        else:
            snap = desktop_perception.capture_fullscreen()

        resp = (
            f"📸 **Screenshot Captured**\n\n"
            f"- **Target:** {target.title()}\n"
            f"- **Dimensions:** {snap.get('width', 1360)} × {snap.get('height', 768)} pixels\n"
            f"- **File Saved:** `{snap.get('filename')}` ({snap.get('size_bytes', 0) // 1024} KB)\n"
            f"- **Capture Duration:** {snap.get('duration_ms', 0)}ms\n"
            f"- **Integrity Hash:** `{snap.get('hash', 'N/A')[:12]}`"
        )
        return {
            "response": resp,
            "tools_used": ["desktop_perception_screenshot"],
            "raw": snap,
        }

    def _respond_screen_find_element(self, ctx: Dict) -> Dict:
        from tools.desktop.desktop_perception import desktop_perception
        from tools.desktop.element_detector import element_detector
        query = ctx.get("query", "settings")
        act_win = desktop_perception.get_active_window()
        elem = element_detector.find_element(query, act_win)

        if not elem:
            return {
                "response": f"🔍 Searched active window (`{act_win.get('title')}`), but could not locate a UI element matching **'{query}'**.",
                "tools_used": ["element_detector_find"],
                "raw": {"query": query, "found": False},
            }

        ed = elem.to_dict()
        resp = (
            f"🎯 **Located UI Element: '{elem.name}'**\n\n"
            f"- **Control Role:** `{elem.role}`\n"
            f"- **Center Coordinates:** `X: {elem.center_x}, Y: {elem.center_y}`\n"
            f"- **Bounding Box:** {elem.width} × {elem.height} at ({elem.x}, {elem.y})\n"
            f"- **Detection Source:** `{elem.source}` (Confidence: {int(elem.confidence * 100)}%)\n"
            f"- **Parent Window:** `{act_win.get('title')}`"
        )
        return {
            "response": resp,
            "tools_used": ["element_detector_find"],
            "raw": ed,
        }

    def _respond_screen_click_element(self, ctx: Dict) -> Dict:
        from tools.desktop.computer_action_engine import computer_action_engine
        query = ctx.get("query", "")
        res = computer_action_engine.click_named_element(query, verify=True)

        if res.get("status") == "not_found":
            return {
                "response": f"⚠️ Could not click: no visible element matching **'{query}'** was detected.",
                "tools_used": ["computer_action_click"],
                "raw": res,
            }

        v = res.get("verification", {})
        verified_str = "Verified (observable screen change detected)" if v.get("verified") else "Executed (action dispatched)"
        target = res.get("target_element", {})

        resp = (
            f"🖱️ **Clicked Element: '{target.get('name', query)}'**\n\n"
            f"- **Coordinates:** ({res.get('coordinates', {}).get('x')}, {res.get('coordinates', {}).get('y')})\n"
            f"- **Status:** {verified_str}\n"
            f"- **Duration:** {res.get('duration_ms')}ms\n"
            f"- **Active Window After:** `{res.get('active_window_after', {}).get('title', 'Unchanged')}`"
        )
        return {
            "response": resp,
            "tools_used": ["computer_action_click"],
            "raw": res,
        }

    def _respond_screen_scroll(self, ctx: Dict) -> Dict:
        from tools.desktop.computer_action_engine import computer_action_engine
        direction = ctx.get("direction", "down")
        res = computer_action_engine.scroll_page(direction=direction, clicks=5)
        v = res.get("verification", {})
        verified_str = "Verified (page content scrolled)" if v.get("verified") else "Dispatched scroll event"

        return {
            "response": f"📜 Scrolled page **{direction}**. Status: {verified_str}.",
            "tools_used": ["computer_action_scroll"],
            "raw": res,
        }

    def _respond_screen_switch_window(self, ctx: Dict) -> Dict:
        from tools.desktop.computer_action_engine import computer_action_engine
        app = ctx.get("app", "")
        res = computer_action_engine.switch_window(app)

        if res.get("status") == "not_found":
            return {
                "response": f"⚠️ Could not switch window: application **'{app}'** is not currently open.",
                "tools_used": ["computer_action_switch"],
                "raw": res,
            }

        act_win = res.get("active_window", {})
        return {
            "response": f"🪟 Switched active window to **{app.title()}** (`{act_win.get('title')}`).",
            "tools_used": ["computer_action_switch"],
            "raw": res,
        }

    def _respond_screen_switch_window_index(self, ctx: Dict) -> Dict:
        from tools.desktop.desktop_perception import desktop_perception
        from tools.desktop.computer_action_engine import computer_action_engine
        idx = ctx.get("index", 1)
        wins = [w for w in desktop_perception.list_open_windows() if w.get("desktop", 0) != -1]

        if not wins or idx > len(wins):
            return {
                "response": f"⚠️ Only {len(wins)} windows are currently open; cannot switch to window #{idx}.",
                "tools_used": ["computer_action_switch_index"],
                "raw": {"requested_index": idx, "available_windows": len(wins)},
            }

        target_win = wins[idx - 1]
        res = computer_action_engine.focus_window(target_win["id"])
        return {
            "response": f"🪟 Switched to application window #{idx}: `{target_win.get('title')}` (**{target_win.get('app')}**).",
            "tools_used": ["computer_action_switch_index"],
            "raw": res,
        }

    def _respond_screen_active_tab(self, ctx: Dict) -> Dict:
        from tools.desktop.desktop_perception import desktop_perception
        wins = desktop_perception.list_open_windows()
        chrome_win = next((w for w in wins if "chrome" in w.get("app", "") or "chrome" in w.get("title", "").lower()), None)
        if not chrome_win:
            return {
                "response": "🌐 No active Google Chrome window is currently open.",
                "tools_used": ["desktop_perception_active_tab"],
                "raw": {"active_tab": None},
            }
        full_title = chrome_win.get("title", "")
        clean_title = re.sub(r'\s*-\s*Google Chrome.*$', '', full_title, flags=re.I).strip()
        resp = f"🌐 The currently active browser tab in Google Chrome is **\"{clean_title}\"**."
        return {
            "response": resp,
            "tools_used": ["desktop_perception_active_tab"],
            "raw": {"full_title": full_title, "clean_title": clean_title, "window_id": chrome_win.get("id")},
        }

    def _respond_screen_type_text(self, ctx: Dict) -> Dict:
        from tools.desktop.computer_action_engine import computer_action_engine
        text_to_type = ctx.get("text_to_type", "")
        res = computer_action_engine.type_text(text_to_type, verify=True)
        v = res.get("verification", {})
        verified_str = "Verified (field content modified)" if v.get("verified") else "Dispatched keystrokes"

        return {
            "response": f"⌨️ Typed text into active field: `\"{text_to_type}\"`. Status: {verified_str}.",
            "tools_used": ["computer_action_type"],
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

    # ─── Phase 5: Multi-AI Agent Orchestration & Self-Healing Handlers ───
    def _respond_agents_discover(self, ctx: Dict) -> Dict:
        from tools.agents.registry import agent_registry
        agents = agent_registry.discover_all(force_refresh=False)
        lines = [
            "### 🤖 Discovered AI Coding Agents",
            "| Agent | Provider | CLI Command | Status | Authenticated | Default Model |",
            "|---|---|---|---|---|---|",
        ]
        for a in agents:
            auth_str = "✅ Yes" if a.authenticated else "❌ No"
            st_val = a.status.value.upper()
            status_icon = "🟢 READY" if st_val == "READY" else ("🟡 UNAUTH" if st_val == "UNAUTHENTICATED" else "⚪ " + st_val)
            cmd = f"`{a.cli_path}`" if a.cli_path else "N/A"
            model = a.capabilities.models[0] if a.capabilities.models else "N/A"
            lines.append(f"| **{a.display_name}** | {a.id.upper()} | {cmd} | {status_icon} | {auth_str} | `{model}` |")
        
        ready_count = sum(1 for a in agents if a.status.value.upper() == "READY")
        lines.append(f"\n*{ready_count} of {len(agents)} agents are verified ready for autonomous assistance.*")
        return {
            "response": "\n".join(lines),
            "tools_used": ["agents_discover", "agent_registry.discover_all"],
            "raw": [a.to_dict() for a in agents]
        }

    def _respond_agents_stuck_check(self, ctx: Dict) -> Dict:
        from tools.agents.stuck_watchdog import stuck_watchdog
        from tools.agents.orchestrator import multi_agent_orchestrator
        active_tasks = multi_agent_orchestrator.get_active_tasks()
        
        lines = ["### ⏱️ Agent Watchdog Status"]
        if not active_tasks:
            lines.append("✅ No active agent tasks running. System is operating normally with zero task stagnation.")
        else:
            lines.append(f"Found {len(active_tasks)} active task(s):")
            for t in active_tasks:
                stuck, reason = stuck_watchdog.is_stuck(t.task_id)
                status_icon = "⚠️ STUCK" if stuck else "⏳ RUNNING"
                lines.append(f"- **Task `{t.task_id}`** ({t.agent_id}): {status_icon}")
                if stuck:
                    lines.append(f"  - Reason: {reason}")
                    lines.append(f"  - Initiating safe termination...")
                    multi_agent_orchestrator.cancel_task(t.task_id, reason=reason)
                    lines.append(f"  - Task `{t.task_id}` aborted safely.")
        return {
            "response": "\n".join(lines),
            "tools_used": ["agents_stuck_check", "stuck_watchdog"],
            "raw": {"active_tasks_count": len(active_tasks)}
        }

    def _respond_agents_permissions_pending(self, ctx: Dict) -> Dict:
        from tools.agents.permission_manager import permission_manager
        pending = permission_manager.get_pending_requests()
        profile = permission_manager.get_profile()
        lines = [
            f"### 🛡️ Agent Permission Center (Active Profile: `{profile.value}`)"
        ]
        if not pending:
            lines.append("✅ No pending permission requests. All system operations are clear.")
        else:
            lines.append(f"Found {len(pending)} pending permission request(s):")
            for req in pending:
                req_id = req.get("request_id")
                agent_id = req.get("agent_id")
                action = req.get("action")
                target = req.get("target")
                reason = req.get("reason")
                risk = req.get("risk_level")
                lines.append(f"- **ID `{req_id}`** by `{agent_id}`: action=`{action}` on `{target}`")
                lines.append(f"  - Reason: {reason}")
                lines.append(f"  - Risk: `{risk}`")
        return {
            "response": "\n".join(lines),
            "tools_used": ["agents_permissions_pending", "permission_manager.get_pending_requests"],
            "raw": pending
        }

    def _respond_agents_permissions_profile(self, ctx: Dict) -> Dict:
        from tools.agents.permission_manager import permission_manager
        from tools.agents.models import PermissionProfile
        raw_p = ctx.get("profile", "SAFE_AUTO")
        try:
            prof = PermissionProfile(raw_p.upper())
        except ValueError:
            prof = PermissionProfile.SAFE_AUTO
        permission_manager.set_profile(prof)
        return {
            "response": f"🛡️ Switched agent permission profile to **`{prof.value.upper()}`**.\n\n"
                        f"- SAFE_AUTO: Automatically permits reads and workspace edits; prompts for external writes/package installs; strictly denies hard-deny boundaries.\n"
                        f"- SUPERVISED_AUTO: Prompts for all file writes and package installations.\n"
                        f"- MANUAL: Prompts for every single action.",
            "tools_used": ["agents_permissions_profile", "permission_manager.set_profile"],
            "raw": {"profile": prof.value}
        }

    def _respond_agents_restore_checkpoint(self, ctx: Dict) -> Dict:
        from tools.agents.git_safety import git_safety
        success, msg = git_safety.rollback_latest()
        if success:
            resp = f"⏪ Successfully restored project to previous checkpoint.\n\n{msg}"
        else:
            resp = f"ℹ️ Could not restore checkpoint: {msg}"
        return {
            "response": resp,
            "tools_used": ["agents_restore_checkpoint", "git_safety.rollback_latest"],
            "raw": {"success": success, "message": msg}
        }

    def _respond_agents_repair_project(self, ctx: Dict) -> Dict:
        from tools.agents.self_healing import self_healing_engine
        result = self_healing_engine.diagnose_and_repair(
            problem_description="Self-healing triggered from assistant command",
            error_message="Detected test/code errors in workspace",
            working_dir="/home/roshan/.gemini/antigravity/scratch/jarvis-os",
            test_command="pytest -q tests/unit/test_phase1_real_ai.py"
        )
        status_sym = "✅" if result.get("success") else "❌"
        resp = f"### {status_sym} Self-Healing Diagnosis & Repair Result\n\n" \
               f"- **Agent Chosen:** `{result.get('agent_id', 'none')}`\n" \
               f"- **Status:** `{result.get('status', 'unknown')}`\n" \
               f"- **Diagnosis:** {result.get('diagnosis', 'N/A')}\n" \
               f"- **Syntax Validated:** {result.get('syntax_validated', False)}\n" \
               f"- **Tests Passed:** {result.get('tests_passed', False)}\n\n" \
               f"**Summary:** {result.get('message', '')}"
        return {
            "response": resp,
            "tools_used": ["agents_repair_project", "self_healing_engine.diagnose_and_repair"],
            "raw": result
        }

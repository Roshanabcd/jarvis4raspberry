"""
Unit tests for JARVIS media player, folder/desktop tools, intent classification,
and verification that general prompts do not hijack VS Code or calculator.
"""
import os
import pytest
from ai.local_engine import LocalIntelligenceEngine
from tools.media.media_player import MediaPlayer, get_media_player
from tools.filesystem.file_tools import FileTools


def test_media_player_initialization():
    player = get_media_player()
    assert player is not None
    status = player.status()
    assert "status" in status
    assert status["status"] in ("idle", "playing", "paused")


def test_find_local_audio():
    player = get_media_player()
    # /home/roshan/Music/myvoice.mpeg or /home/roshan/Downloads/myvoice.mp3 exist on user system
    found = player.find_local_audio("myvoice")
    assert isinstance(found, list)
    assert len(found) > 0
    assert os.path.exists(found[0]["path"])


def test_media_player_no_deadlock():
    player = get_media_player()
    # Stop when idle should not deadlock with RLock
    res = player.stop()
    assert res.get("status") in ("ok", "stopped", "idle")
    # Status should return cleanly
    st = player.status()
    assert st["status"] == "idle"


def test_file_tools_folder_search_and_open():
    ft = FileTools()
    # Search for Downloads or Music or Desktop in user home
    folders = ft.search_folders("Downloads")
    assert any("Downloads" in f["name"] for f in folders)

    # Open folder info (dry run or pcmanfm invocation)
    res = ft.open_folder("Downloads")
    assert res.get("status") in ("opened", "ok")
    assert "path" in res
    assert "Downloads" in res["path"]


def test_local_engine_media_intents():
    engine = LocalIntelligenceEngine()
    
    intent, entities = engine.classify_intent("play song shape of you")
    assert intent == "play_media"
    assert "shape of you" in entities.get("query", "")

    intent2, _ = engine.classify_intent("stop music")
    assert intent2 == "stop_media"

    intent3, _ = engine.classify_intent("pause song")
    assert intent3 == "pause_media"

    intent4, entities4 = engine.classify_intent("volume up")
    assert intent4 == "volume_up"


def test_local_engine_folder_intents():
    engine = LocalIntelligenceEngine()

    intent, entities = engine.classify_intent("search abc folder")
    assert intent == "search_folder"
    assert entities.get("query") == "abc"

    intent2, entities2 = engine.classify_intent("open downloads folder")
    assert intent2 == "open_folder"
    assert entities2.get("folder") == "downloads"

    intent3, entities3 = engine.classify_intent("open xyz folder located in pqr location")
    assert intent3 == "open_folder_at"
    assert entities3.get("folder") == "xyz"
    assert entities3.get("parent") == "pqr"


def test_no_rogue_calculator_or_vscode_hijacking():
    engine = LocalIntelligenceEngine()

    # User's complaints: "when i give you to prompt for solving or making the jarvis"
    intent, entities = engine.classify_intent("when i give you to prompt for solving or making the jarvis")
    assert intent != "create_calculator"
    assert intent != "open_app"

    # Ordinary coding or conversation questions
    intent2, _ = engine.classify_intent("tell me how to write python code for bubble sort")
    assert intent2 != "create_calculator"

    # Only explicit commands like "write a calculator" should match calculator
    intent3, _ = engine.classify_intent("write a python calculator app")
    assert intent3 == "create_calculator"


def test_engine_respond_play_media():
    engine = LocalIntelligenceEngine()
    # Respond to "stop music" should execute stop_media cleanly
    resp = engine.respond("stop the music")
    text = resp.get("response", "") if isinstance(resp, dict) else str(resp)
    assert "music" in text.lower() or "audio" in text.lower() or "stopped" in text.lower()

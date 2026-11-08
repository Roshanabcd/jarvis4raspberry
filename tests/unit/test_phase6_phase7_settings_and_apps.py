"""Phase 6 & 7 Test Suite — 14-App Suite Backend and Interactive Settings Center Categories A–P."""
import os
import pytest
from fastapi.testclient import TestClient

from apps.core.main import app
from config.config_manager import config


class TestPhase6Phase7SettingsCenter:
    """Test suite verifying Settings Center Categories A-P and 14-App API endpoints."""

    def test_settings_all_categories_present(self):
        client = TestClient(app)
        res = client.get("/api/settings")
        assert res.status_code == 200
        data = res.json()

        # Verify all Categories A through P exist
        expected_cats = [
            "category_a", "category_b", "category_c", "category_d",
            "category_e", "category_f", "category_g", "category_h",
            "category_i", "category_j", "category_k", "category_l",
            "category_m", "category_n", "category_o", "category_p",
        ]
        for cat in expected_cats:
            assert cat in data, f"Missing {cat} in /api/settings"
            assert "name" in data[cat]

    def test_get_single_category(self):
        client = TestClient(app)
        res = client.get("/api/settings/category_a")
        assert res.status_code == 200
        assert res.json()["name"] == "System & SBC Info"

        res_b = client.get("/api/settings/category_b")
        assert res_b.status_code == 200
        assert "active_provider" in res_b.json()

        res_d = client.get("/api/settings/category_d")
        assert res_d.status_code == 200
        assert "reference_audio_path" in res_d.json()

    def test_update_category_settings_persistence(self, tmp_path):
        client = TestClient(app)

        # Update category_c (Voice & Wake Word)
        res = client.post("/api/settings/category_c", json={
            "settings": {"wake_word": "jarvis"}
        })
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
        assert res.json()["saved_config"] is True
        assert config.get("wake_word") == "jarvis"

        # Update category_g (Robot speed)
        res_g = client.post("/api/settings/category_g", json={
            "settings": {"robot": {"default_speed": 55, "max_speed": 100}}
        })
        assert res_g.status_code == 200
        assert config.get("robot", {}).get("default_speed") == 55

    def test_component_diagnostics(self):
        client = TestClient(app)

        # Test speaker synthesis test
        res_spk = client.post("/api/settings/test/speaker")
        assert res_spk.status_code == 200
        assert res_spk.json()["status"] == "ok"

        # Test camera diagnostics test
        res_cam = client.post("/api/settings/test/camera")
        assert res_cam.status_code == 200
        assert res_cam.json()["status"] == "ok"

        # Test robot diagnostics test
        res_rob = client.post("/api/settings/test/robot")
        assert res_rob.status_code == 200
        assert res_rob.json()["status"] == "ok"

    def test_export_backup_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/settings/export/backup")
        assert res.status_code == 200
        data = res.json()
        assert "config" in data
        assert "timestamp" in data

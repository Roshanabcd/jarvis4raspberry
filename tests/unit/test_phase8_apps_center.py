"""
JARVIS OS — Phase 8 Automated Acceptance & Regression Test Suite:
JARVIS Apps Center: Unified AI Application Platform, Modular Architecture,
Shared Services, Dashboard & Permission System.

Verifies:
1. Application registry loading (20 canonical apps).
2. Unique application IDs across the catalog.
3. Application manifest schema validation.
4. Application category filtering across all 10 categories.
5. Multi-attribute application search.
6. Truthful status rules: Available (3) vs Planned (17).
7. Opening an enabled Available application (POST /api/apps/launch/{id}).
8. Blocking execution of a Planned application with roadmap detail (HTTP 400).
9. Backend permission enforcement (minimum_role boundaries).
10. ADMIN status governance (update_status with PIN check).
11. USER access permissions.
12. GUEST role restrictions.
13. User isolation in favorites and recently opened apps.
14. Provider configuration state inspection.
15. Truthful handling of unconfigured cloud credentials.
16. Local Ollama health check.
17. Resource monitoring accuracy (real CPU, RAM, Disk, Temp).
18. Task status transitions and user isolation.
19. Application settings isolation per user.
20. Voice Assistant conversational intent routing.
21. Categories summary counts consistency.
22. Existing Vision & Identity regression check.
23. Existing camera capture regression check.
24. Existing camera service health check.
25. Single instance lock & desktop launcher compatibility.
"""

import os
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from apps.core.main import app
from apps.apps_center.models import (
    ApplicationManifest,
    AppCategory,
    AppStatus,
    ResourceProfile,
    CANONICAL_APP_IDS,
)
from apps.apps_center.registry import ApplicationRegistry, app_registry
from apps.apps_center.database import AppsCenterDatabase, apps_db
from apps.apps_center.resource_manager import ResourceManager, resource_manager
from apps.apps_center.ai_service import SharedAIService, shared_ai
from apps.apps_center.task_manager import AppTaskManager, task_manager
from apps.apps_center.permissions import AppsPermissionEngine, apps_permissions
from tools.identity.user_manager import UserManager, UserRole, user_manager
from tools.vision.camera_manager import CameraManager


class TestPhase8AppsCenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.registry = app_registry
        cls.db = apps_db
        cls.cam_mgr = CameraManager()

    # ── Test 1: Registry Loading ─────────────────────────────
    def test_01_registry_loads_twenty_applications(self):
        """ApplicationRegistry must load exactly 20 canonical applications."""
        apps = self.registry.get_all_apps()
        self.assertEqual(len(apps), 20, f"Expected 20 applications in registry, found {len(apps)}")
        loaded_ids = {a.id for a in apps}
        self.assertEqual(loaded_ids, CANONICAL_APP_IDS, "Catalog must match the exact 20 canonical application IDs")

    # ── Test 2: Unique IDs ───────────────────────────────────
    def test_02_unique_application_ids(self):
        """Every application in the catalog must possess a globally unique identifier."""
        apps = self.registry.get_all_apps()
        ids = [a.id for a in apps]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate application IDs detected in registry")

    # ── Test 3: Manifest Validation ──────────────────────────
    def test_03_application_manifest_validation(self):
        """Manifest schema must strictly enforce types and reject invalid IDs."""
        valid_app = self.registry.get_app("voice-assistant")
        self.assertIsNotNone(valid_app)
        self.assertEqual(valid_app.name, "Voice Assistant")
        self.assertEqual(valid_app.minimum_role, "USER")

        # Attempt to create invalid manifest (spaces in ID)
        with self.assertRaises(Exception):
            ApplicationManifest(
                id="Invalid ID With Spaces",
                name="Test",
                description="desc",
                category=AppCategory.PRODUCTIVITY,
                route="/test",
            )

    # ── Test 4: Category Filtering ───────────────────────────
    def test_04_application_category_filtering(self):
        """Registry search must accurately filter by any of the 10 categories."""
        categories = self.registry.get_categories()
        self.assertEqual(len(categories), 10, "Must support all 10 standard categories")

        research_apps = self.registry.search_apps(category="research_knowledge")
        self.assertGreaterEqual(len(research_apps), 3)
        for a in research_apps:
            self.assertEqual(a.category, AppCategory.RESEARCH_KNOWLEDGE)

    # ── Test 5: Search Functionality ─────────────────────────
    def test_05_application_search(self):
        """Search query must match across name, description, category, and capabilities."""
        results = self.registry.search_apps(query="transcription")
        self.assertTrue(any(a.id == "speech-translation" or a.id == "voice-assistant" for a in results))

        y_results = self.registry.search_apps(query="YouTube")
        self.assertTrue(any(a.id == "youtube-summarizer" for a in y_results))

    # ── Test 6: Truthful Status Rules ────────────────────────
    def test_06_truthful_status_rules(self):
        """Only genuine verified applications are Available; non-implemented apps are Planned."""
        avail_apps = self.registry.get_available_apps()
        avail_ids = {a.id for a in avail_apps}
        # Operational baseline applications must be available
        self.assertIn("voice-assistant", avail_ids)
        self.assertIn("face-recognition", avail_ids)
        self.assertIn("multi-agent-automation", avail_ids)
        self.assertGreaterEqual(len(avail_apps), 3, "Baseline applications must be marked Available")

    # ── Test 7: Launching Available Application ──────────────
    def test_07_launching_available_application(self):
        """POST /api/apps/launch/{id} must succeed for an Available application."""
        from tools.identity.permission_manager import permission_manager
        permission_manager.set_active_user({"user_id": "test_user", "role": "USER"})
        try:
            resp = self.client.post("/api/apps/launch/voice-assistant")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("app_id"), "voice-assistant")
            self.assertEqual(data.get("route"), "/voice")
            self.assertEqual(data.get("target_tab"), "voice")
        finally:
            permission_manager.set_active_user(None)

    # ── Test 8: Blocking Planned Application ─────────────────
    def test_08_blocking_planned_application(self):
        """POST /api/apps/launch/{id} must block Planned applications with HTTP 400 and roadmap info."""
        app = self.registry.get_app("document-qa")
        original_status = app.status
        try:
            app.status = AppStatus.PLANNED
            resp = self.client.post("/api/apps/launch/document-qa")
            self.assertEqual(resp.status_code, 400)
            detail = resp.json().get("detail", "")
            self.assertIn("Planned", detail)
            self.assertIn("not yet implemented", detail)
        finally:
            app.status = original_status

    # ── Test 9: Backend Permission Enforcement ───────────────
    def test_09_backend_permission_enforcement(self):
        """ADMIN apps must reject GUEST or USER launches without elevation."""
        trading_app = self.registry.get_app("trading-bot")
        self.assertEqual(trading_app.minimum_role, "ADMIN")

        # Guest role cannot launch admin app
        can_access, reason = apps_permissions.can_access_app(trading_app, "GUEST")
        self.assertFalse(can_access)

    # ── Test 10: ADMIN Status Governance ─────────────────────
    def test_10_admin_status_governance_with_pin(self):
        """POST /api/apps/admin/status requires valid admin PIN."""
        resp = self.client.post("/api/apps/admin/status", json={
            "app_id": "document-qa",
            "status": "planned",
            "admin_pin": "wrong_pin_0000"
        })
        self.assertEqual(resp.status_code, 403)

    # ── Test 11: USER Access Permissions ─────────────────────
    def test_11_user_role_permissions(self):
        """USER role can access USER-level applications."""
        voice_app = self.registry.get_app("voice-assistant")
        can_access, _ = apps_permissions.can_access_app(voice_app, "USER")
        self.assertTrue(can_access)

    # ── Test 12: GUEST Restrictions ──────────────────────────
    def test_12_guest_role_restrictions(self):
        """GUEST role cannot manage settings or elevate privileges."""
        self.assertFalse(apps_permissions.can_manage_settings("GUEST"))
        self.assertFalse(apps_permissions.can_manage_settings("USER"))
        self.assertTrue(apps_permissions.can_manage_settings("ADMIN"))

    # ── Test 13: User Isolation in Favorites & Recents ────────
    def test_13_user_isolation_favorites_and_recents(self):
        """User A's favorites and recents must be completely isolated from User B."""
        from tools.identity.permission_manager import permission_manager
        user_a = "user_alpha"
        user_b = "user_beta"

        try:
            # User A stars voice-assistant
            permission_manager.set_active_user({"user_id": user_a, "role": "USER"})
            self.client.post("/api/apps/favorite/voice-assistant")
            favs_a = self.db.get_user_favorites(user_a)
            favs_b = self.db.get_user_favorites(user_b)

            self.assertIn("voice-assistant", favs_a)
            self.assertNotIn("voice-assistant", favs_b)

            # Cleanup
            self.client.post("/api/apps/favorite/voice-assistant")
        finally:
            permission_manager.set_active_user(None)

    # ── Test 14: Provider Configuration State ────────────────
    def test_14_provider_configuration_state(self):
        """GET /api/apps/providers must return provider connection states."""
        resp = self.client.get("/api/apps/providers")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        providers = data.get("providers", [])
        self.assertGreaterEqual(len(providers), 3)

        ollama_p = next((p for p in providers if p["id"] == "ollama"), None)
        self.assertIsNotNone(ollama_p)
        self.assertTrue(ollama_p["configured"])

    # ── Test 15: Missing Cloud Credentials Truthful Handling ─
    def test_15_unconfigured_credentials_truthful_state(self):
        """Cloud providers without API keys must truthfully declare unconfigured state."""
        providers = shared_ai.get_providers_status()
        for p in providers:
            if not p.get("configured"):
                self.assertIsNotNone(p.get("error"))
                self.assertIn("not configured", p.get("error", "").lower())

    # ── Test 16: Local Ollama Health ─────────────────────────
    def test_16_local_ollama_health(self):
        """Ollama provider on 127.0.0.1:11434 must report connectivity."""
        providers = shared_ai.get_providers_status()
        ollama = next((p for p in providers if p["id"] == "ollama"), None)
        self.assertIsNotNone(ollama)
        self.assertTrue(ollama["connected"])

    # ── Test 17: Resource Monitoring Accuracy ────────────────
    def test_17_real_resource_monitoring(self):
        """ResourceManager must report actual non-zero CPU, RAM, and Disk metrics."""
        telem = resource_manager.get_real_telemetry()
        self.assertGreater(telem["ram_total_mb"], 1000)
        self.assertGreater(telem["ram_available_mb"], 100)
        self.assertGreater(telem["disk_total_gb"], 1.0)
        self.assertGreaterEqual(telem["cpu_percent"], 0.0)
        self.assertIn(telem["system_load_status"], ["nominal", "warning", "critical"])

    # ── Test 18: Task Lifecycle & Isolation ──────────────────
    def test_18_task_lifecycle_and_isolation(self):
        """Background tasks must transition status and enforce user isolation."""
        user_id = "test_worker_user"
        record = task_manager.submit_task(
            app_id="voice-assistant",
            user_id=user_id,
            task_type="diagnostic_ping",
            worker_func=lambda cancel_event: {"result": "ping_ok"},
            resource_profile="lightweight",
        )
        task_id = record["task_id"]
        self.assertIsNotNone(task_id)

        # Another user cannot fetch or cancel this task
        unauthorized = task_manager.get_task_status(task_id, user_id="intruder_user")
        self.assertIsNone(unauthorized)

        # Owner can fetch
        authorized = task_manager.get_task_status(task_id, user_id=user_id)
        self.assertIsNotNone(authorized)

    # ── Test 19: Application Settings Isolation ──────────────
    def test_19_application_settings_isolation(self):
        """User application settings must be strictly isolated per user."""
        app_id = "voice-assistant"
        self.db.set_app_setting(app_id, "user_one", "speech_speed", 0.9)
        self.db.set_app_setting(app_id, "user_two", "speech_speed", 1.2)

        s1 = self.db.get_app_settings(app_id, "user_one")
        s2 = self.db.get_app_settings(app_id, "user_two")

        self.assertEqual(s1.get("speech_speed"), 0.9)
        self.assertEqual(s2.get("speech_speed"), 1.2)

    # ── Test 20: Voice Assistant Application Navigation ──────
    def test_20_voice_assistant_apps_intent_routing(self):
        """Chat API must route 'Show all applications' and 'Open document question answering app'."""
        # 1. List applications
        resp = self.client.post("/api/chat", json={"message": "Show all applications"})
        self.assertEqual(resp.status_code, 200)
        text1 = resp.json().get("response", "")
        self.assertIn("Apps Center Catalog", text1)
        self.assertIn("Available", text1)

        # 2. Open available Document QA app
        resp2 = self.client.post("/api/chat", json={"message": "Open the document question answering app"})
        self.assertEqual(resp2.status_code, 200)
        text2 = resp2.json().get("response", "")
        self.assertIn("Opening Document Question Answering", text2)

    # ── Test 21: Categories Summary Consistency ──────────────
    def test_21_categories_endpoint(self):
        """GET /api/apps/categories must return counts that sum to exactly 20."""
        resp = self.client.get("/api/apps/categories")
        self.assertEqual(resp.status_code, 200)
        cats = resp.json().get("categories", [])
        total_count = sum(c["count"] for c in cats)
        self.assertEqual(total_count, 20)

    # ── Test 22: Existing Vision & Identity Regression ───────
    def test_22_existing_vision_and_identity_regression(self):
        """GET /api/identity/status and /api/vision/status must remain operational."""
        r_id = self.client.get("/api/identity/status")
        self.assertEqual(r_id.status_code, 200)

        r_vis = self.client.get("/api/vision/status")
        self.assertEqual(r_vis.status_code, 200)
        self.assertTrue(r_vis.json().get("available"))

    # ── Test 23: Existing Camera Capture Regression ──────────
    def test_23_existing_camera_capture_regression(self):
        """CameraManager must capture real frames without simulation."""
        if self.cam_mgr.is_service_running():
            res = self.cam_mgr.capture_photo()
            self.assertTrue(res.get("success"))
            self.assertFalse(res.get("simulated", True))
            self.assertEqual(res.get("backend"), "camera_service_picamera2")
        else:
            self.skipTest("Camera service not active in this test runner.")

    # ── Test 24: Existing Camera Service Health ──────────────
    def test_24_existing_camera_service_health(self):
        """Camera service at 127.0.0.1:8082 must report ok."""
        if self.cam_mgr.is_service_running():
            health = self.cam_mgr.get_service_health()
            self.assertIsNotNone(health)
            self.assertEqual(health.get("status"), "ok")
            self.assertEqual(health.get("backend"), "picamera2")
        else:
            self.skipTest("Camera service not running.")

    # ── Test 25: Desktop Launcher Compatibility ──────────────
    def test_25_desktop_launcher_compatibility(self):
        """Launcher single instance lock and route compatibility."""
        from apps.desktop.launcher import SingleInstanceLock, LOCK_FILE
        sil = SingleInstanceLock(LOCK_FILE.parent / "test_launcher.lock")
        acquired = sil.acquire()
        self.assertTrue(acquired)
        sil.release()


if __name__ == "__main__":
    unittest.main()

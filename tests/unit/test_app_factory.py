"""Regression tests for hardware-safe FastAPI construction."""

from fastapi.testclient import TestClient
import pytest

from apps.core.app_factory import create_app, noop_lifespan


def test_empty_factory_uses_noop_lifespan_without_importing_routers():
    """Focused tests can run a real ASGI shell without production services."""
    app = create_app(
        router_specs=(),
        lifespan_context=noop_lifespan,
        include_dashboard=False,
    )

    with TestClient(app) as client:
        response = client.get("/api/status")

    assert response.status_code == 404


def test_factory_can_include_a_selected_safe_router(monkeypatch: pytest.MonkeyPatch):
    """A narrow router can be exercised without the production lifecycle."""
    import tools.robotics.controller as controller_module

    monkeypatch.setattr(controller_module, "_robot", None)
    app = create_app(
        router_specs=(("apps.api.router", "router", "", ("core",)),),
        lifespan_context=noop_lifespan,
        include_dashboard=False,
    )

    with TestClient(app) as client:
        response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    assert controller_module.get_existing_robot() is None


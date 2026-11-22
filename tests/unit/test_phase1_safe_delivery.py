"""Phase 1: Tests for Safe Delivery Path and Regression Harness."""
from fastapi.testclient import TestClient
import pytest
from apps.core.app_factory import create_app, noop_lifespan


def test_parallel_route_mounts_futuristic_without_altering_root():
    """Verify /futuristic and / both mount safely with distinct content."""
    app = create_app(
        router_specs=(("apps.api.router", "router", "", ("core",)),),
        lifespan_context=noop_lifespan,
        include_dashboard=True,
    )

    with TestClient(app) as client:
        # Check root dashboard
        root_resp = client.get("/")
        assert root_resp.status_code == 200
        assert "JARVIS" in root_resp.text
        # Verify original dashboard contains its primary landmark (e.g. nav-home or control-center)
        assert 'id="nav-home"' in root_resp.text or 'id="tab-home"' in root_resp.text

        # Check parallel futuristic dashboard
        futuristic_resp = client.get("/futuristic/")
        assert futuristic_resp.status_code == 200
        assert "Futuristic" in futuristic_resp.text
        assert "Safe delivery parallel route active" in futuristic_resp.text


def test_disabled_dashboard_mounts_neither_root_nor_futuristic():
    """When include_dashboard=False, static mounts are omitted."""
    app = create_app(
        router_specs=(),
        lifespan_context=noop_lifespan,
        include_dashboard=False,
    )

    with TestClient(app) as client:
        assert client.get("/").status_code == 404
        assert client.get("/futuristic/").status_code == 404

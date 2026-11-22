"""MOCK routes only; do not import or execute downloaded module engines."""
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.apps_center.extension_catalog import extension_apps, extension_matches
from apps.apps_center.models import AppStatus
from jarvis_feature_suite_loader import loader


def host_with_registered_extension():
    app = FastAPI()
    app.add_api_route('/ai-data-analyst', lambda: {'fixture': 'MOCK UI'})
    app.add_api_route('/api/v1/ai-data-analyst/health', lambda: {'fixture': 'MOCK API'})
    return app


def test_all_25_extensions_discoverable_without_importing_module_code():
    apps = extension_apps(host_with_registered_extension())
    assert len(apps) == 25
    assert len({app.id for app in apps}) == 25
    analyst = next(app for app in apps if app.id == 'extension-28')
    assert analyst.status == AppStatus.AVAILABLE
    assert analyst.route == '/ai-data-analyst'
    assert 'must be checked' in analyst.roadmap
    assert all(app.status == AppStatus.IN_DEVELOPMENT for app in apps if app.id != analyst.id)


def test_disabled_extension_and_missing_api_are_not_launchable(monkeypatch):
    host = host_with_registered_extension()
    monkeypatch.setattr(loader, '_DISABLED_MODULES', {'ai_data_analyst'})
    assert next(a for a in extension_apps(host) if a.id == 'extension-28').status == AppStatus.DISABLED
    monkeypatch.setattr(loader, '_DISABLED_MODULES', set())
    host.routes[:] = [route for route in host.routes if route.path != '/api/v1/ai-data-analyst/health']
    assert next(a for a in extension_apps(host) if a.id == 'extension-28').status == AppStatus.IN_DEVELOPMENT


def test_extension_search_uses_existing_category_and_status_values():
    analyst = next(a for a in extension_apps(host_with_registered_extension()) if a.id == 'extension-28')
    assert extension_matches(analyst, query='data', category='research_knowledge', status='available')
    assert not extension_matches(analyst, query='unrelated')
    assert not extension_matches(analyst, category='experimental')


def test_catalog_and_launch_share_server_permissions_without_modifying_registry(monkeypatch):
    from apps.api import apps_center_api as api
    from apps.apps_center.permissions import AppRequestIdentity
    app = host_with_registered_extension()
    app.include_router(api.apps_center_router, prefix='/api')
    identity = AppRequestIdentity('MOCK-user','MOCK user','USER')
    app.dependency_overrides[api.get_active_app_identity] = lambda: identity
    monkeypatch.setattr(api.apps_db, 'get_user_favorites', lambda **_: [])
    opened=[]
    monkeypatch.setattr(api.apps_db, 'record_app_opened', lambda **kwargs: opened.append(kwargs))
    before = len(api.app_registry.get_all_apps())
    client = TestClient(app)
    result = client.get('/api/apps/catalog?query=data&category=research_knowledge')
    assert result.status_code == 200
    assert any(a['id'] == 'extension-28' for a in result.json()['applications'])
    launch = client.post('/api/apps/launch/extension-28', json={})
    assert launch.status_code == 200
    assert launch.json()['route'] == '/ai-data-analyst'
    assert launch.json()['target_tab'] is None
    assert opened == [{'user_id':'MOCK-user','app_id':'extension-28'}]
    identity = AppRequestIdentity('MOCK-guest','MOCK guest','GUEST')
    assert client.post('/api/apps/launch/extension-28',json={}).status_code == 403
    assert len(opened) == 1
    assert len(api.app_registry.get_all_apps()) == before
    assert client.post('/api/apps/launch/extension-99',json={}).status_code == 404


def test_nested_included_router_prefixes_are_resolved_without_running_handlers():
    from fastapi import APIRouter
    from starlette.staticfiles import StaticFiles
    host = FastAPI()
    called = []
    host.add_api_route('/ai-data-analyst', lambda: called.append('ui'))
    child = APIRouter(prefix='/ai-data-analyst')
    child.add_api_route('/health', lambda: called.append('health'))
    parent = APIRouter(prefix='/v1')
    parent.include_router(child)
    host.include_router(parent, prefix='/api')
    host.mount('/', StaticFiles(directory='.'))
    apps = extension_apps(host)
    assert next(a for a in apps if a.id == 'extension-28').status == AppStatus.AVAILABLE
    assert next(a for a in apps if a.id == 'extension-29').status == AppStatus.IN_DEVELOPMENT
    assert called == []

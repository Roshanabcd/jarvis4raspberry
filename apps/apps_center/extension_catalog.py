"""Expose already registered extension interfaces without importing their engines.

This bridge does not install, enable, run or health-probe a module. UI/API route
registration establishes that its page can be opened, not provider readiness.
"""
from apps.apps_center.models import ApplicationManifest, AppCategory, AppStatus, ResourceProfile

_CATEGORY_BY_NUMBER = {
    18: 'ai_agents', 19: 'ai_agents', 20: 'ai_agents', 21: 'research_knowledge',
    22: 'ai_agents', 23: 'productivity', 24: 'productivity', 25: 'productivity',
    26: 'developer_tools', 27: 'developer_tools', 28: 'research_knowledge',
    29: 'productivity', 30: 'experimental', 31: 'experimental',
    32: 'security_analytics', 33: 'security_analytics', 34: 'experimental',
    35: 'productivity', 36: 'computer_vision', 37: 'productivity',
    38: 'developer_tools', 39: 'productivity', 40: 'security_analytics',
    41: 'productivity', 42: 'developer_tools',
}


def extension_apps(host_app):
    if host_app is None:
        return []
    from jarvis_feature_suite_loader.loader import FEATURE_REGISTRY, _DISABLED_MODULES
    paths = set()
    for route in host_app.routes:
        # Newer FastAPI retains included routers instead of flattening them.
        # Resolve their prefixed metadata without invoking any handler/engine.
        contexts = getattr(route, 'effective_route_contexts', None)
        candidates = contexts() if callable(contexts) else (route,)
        for candidate in candidates:
            if hasattr(candidate, 'path') and 'GET' in (getattr(candidate, 'methods', None) or ()):
                paths.add(candidate.path)
    result = []
    for spec in FEATURE_REGISTRY:
        number = spec.get('module_number')
        if number not in _CATEGORY_BY_NUMBER:
            continue
        route = spec.get('ui_path', '')
        if not route.startswith('/') or route.startswith('//') or '\\' in route:
            continue
        mounted = route in paths and spec.get('health_path') in paths
        disabled = spec['id'] in _DISABLED_MODULES
        status = AppStatus.DISABLED if disabled else AppStatus.AVAILABLE if mounted else AppStatus.IN_DEVELOPMENT
        note = ('Interface and API registered. Provider, device and action readiness must be checked inside the module.' if mounted
                else 'Not available: this backend has not registered the module interface and API. Reload the updated backend.')
        if disabled:
            note = 'Not available: this module is disabled in the extension manager.'
        result.append(ApplicationManifest(
            id=f'extension-{number}', name=spec['name'], description=spec['description'],
            version='1.0.0', category=AppCategory(_CATEGORY_BY_NUMBER[number]),
            route=route, target_tab=None, status=status, minimum_role='USER',
            permissions=spec.get('permissions', []), capabilities=[spec['name']],
            resource_profile=ResourceProfile(spec.get('tier', 'MEDIUM').lower()),
            roadmap=note, icon='🧩',
        ))
    return result


def extension_matches(app, *, query=None, category=None, status=None, capability=None):
    if category and app.category.value != category.strip().lower():
        return False
    if status and app.status.value != status.strip().lower():
        return False
    if capability and not any(capability.lower() in item.lower() for item in app.capabilities):
        return False
    fields=[app.name, app.description, app.category.value, *app.capabilities, *app.permissions]
    return not query or any(query.strip().lower() in value.lower() for value in fields)

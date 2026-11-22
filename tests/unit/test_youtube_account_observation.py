"""Offline account observation: no personal sessions, cookies, or real websites."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import threading

import pytest

from tools.desktop.youtube_account_observation import account_result, supported_origin, ACCOUNT_SNAPSHOT_JS
from tools.desktop.browser_backend import PlaywrightBrowserBackend
from tools.desktop.unified_computer_service import UnifiedComputerService

URL = 'https://www.youtube.com/'


@pytest.mark.parametrize('url', ['https://youtube.com.evil.test/', 'http://youtube.com/', 'https://youtube.com:444/', 'https://user@youtube.com/', 'file:///youtube.com', None])
def test_untrusted_origin_rejected(url):
    assert not supported_origin(url)
    assert account_result({'url': url, 'labels': ['Work']})['status'] == 'unavailable'


@pytest.mark.parametrize('labels', [None, 'Work', [None], [''], ['a' * 257], ['Work'] * 101])
def test_invalid_observation_rejected(labels):
    assert account_result({'url': URL, 'labels': labels})['status'] == 'unavailable'


def test_duplicate_labels_need_clarification_not_deduplication():
    result = account_result({'url': URL, 'labels': ['Work', ' work ']}, 'WORK')
    assert result['status'] == 'needs_input'
    assert result['match_count'] == 2
    assert result['verified'] is False


def test_partial_label_does_not_select_a_different_identity():
    result = account_result({'url': URL, 'labels': ['Work Personal', 'Work Team']}, 'Work')
    assert result['status'] == 'needs_input'
    assert result['match_count'] == 0


def test_unique_match_does_not_verify_active_account():
    result = account_result({'url': URL, 'labels': ['Work Team', 'Personal']}, ' work   team ')
    assert result['status'] == 'observed'
    assert result['matched_label'] == 'Work Team'
    assert result['verified'] is False
    assert result['scope'] == 'managed_browser_only'


def test_empty_menu_is_unavailable():
    assert account_result({'url': URL, 'labels': []})['status'] == 'unavailable'


@pytest.mark.parametrize('running,url,expected_eval', [(False, URL, False), (True, 'https://example.test/', False), (True, URL, True)])
def test_backend_does_not_start_or_click(running, url, expected_eval):
    backend = PlaywrightBrowserBackend.__new__(PlaywrightBrowserBackend)
    backend._lock = threading.RLock()
    backend._run_on_browser_thread = lambda fn, *args, **kwargs: fn(*args)
    backend.is_running = Mock(return_value=running)
    page = Mock(url=url)
    page.evaluate.return_value = {'url': URL, 'labels': ['Work']}
    backend._raw_page = page
    backend._page_proxy = page
    backend.start = Mock()
    result = backend.observe_youtube_accounts('Work')
    assert result['status'] == ('observed' if expected_eval else 'unavailable')
    assert page.evaluate.called is expected_eval
    page.click.assert_not_called()
    backend.start.assert_not_called()


@pytest.mark.parametrize('source', ['chat', 'voice'])
def test_public_dispatcher_observation_is_read_only(source):
    from ai.capabilities.dispatcher import CapabilityDispatcher
    from ai.capabilities.models import CapabilityInvocationRequest
    service = UnifiedComputerService.__new__(UnifiedComputerService)
    service._emergency_stopped = False
    service._stop_requested = False
    cap = SimpleNamespace(id='desktop-pc-tools', name='Desktop', minimum_role='USER', is_cli=False,
                          actions=[SimpleNamespace(action_id='browser_ui_action')])
    dispatcher = CapabilityDispatcher.__new__(CapabilityDispatcher)
    dispatcher.registry = Mock()
    dispatcher.registry.get_capability.return_value = cap
    request = CapabilityInvocationRequest(capability_id=cap.id, action_id='browser_ui_action', source=source,
        parameters={'action': 'resolve_youtube_account', 'target': 'Work'})
    prefix = 'tools.desktop.unified_computer_service'
    with patch(f'{prefix}.unified_computer_service', service), patch(f'{prefix}.browser_backend') as browser, patch(f'{prefix}.native_backend') as native:
        browser.observe_youtube_accounts.return_value = account_result({'url': URL, 'labels': ['Work', 'Work']}, 'Work')
        result = dispatcher.execute(request)
    assert result.status == 'needs_input'
    assert result.data['verified'] is False
    assert native.mock_calls == []
    browser.observe_youtube_accounts.assert_called_once_with(target='Work')


def test_dom_extractor_with_isolated_chromium():
    # All requests intercepted. MOCK account elements, one temporary browser,
    # no personal profile, audio, screen capture or external network requests.
    from playwright.sync_api import sync_playwright
    html = '''<title>MOCK account menu</title>
    <style>ytd-account-item-renderer {display:block}</style>
    <ytd-account-item-renderer><span id="account-name">Work</span><span>private fixture email</span></ytd-account-item-renderer>
    <ytd-account-item-renderer><span id="account-name">Work</span></ytd-account-item-renderer>
    <ytd-account-item-renderer hidden><span id="account-name">Hidden</span></ytd-account-item-renderer>
    <ytd-account-item-renderer aria-disabled="true"><span id="account-name">Disabled</span></ytd-account-item-renderer>
    <p>Unrelated account text</p>'''
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
        try:
            context = browser.new_context(service_workers='block')
            context.route('**/*', lambda route: route.fulfill(status=200, content_type='text/html', body=html))
            page = context.new_page()
            page.goto(URL)
            observed = page.evaluate(ACCOUNT_SNAPSHOT_JS)
            assert observed['labels'] == ['Work', 'Work']
            assert account_result(observed, 'Work')['status'] == 'needs_input'
        finally:
            browser.close()


@pytest.mark.parametrize('channel', ['chat', 'voice'])
@pytest.mark.parametrize('prompt,action,target', [
    ('Jarvis, list YouTube accounts', 'list_youtube_accounts', None),
    ('show visible YouTube account labels', 'list_youtube_accounts', None),
    ('resolve YouTube account named "Work Team"', 'resolve_youtube_account', 'Work Team'),
    ('find YouTube account named "Play"', 'resolve_youtube_account', 'Play'),
])
def test_natural_language_observation_routes_without_switching(channel, prompt, action, target):
    from ai.capabilities.router import AutonomousCapabilityRouter
    router = AutonomousCapabilityRouter.__new__(AutonomousCapabilityRouter)
    router.registry = Mock()
    router.registry.list_capabilities.return_value = []
    result = router.route(prompt, channel=channel)
    assert result.action_id == 'browser_ui_action'
    assert result.extracted_parameters['action'] == action
    assert result.extracted_parameters.get('target') == target

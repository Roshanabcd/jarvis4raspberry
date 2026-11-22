"""No physical input: delivery acknowledgments cannot prove account selection."""
from unittest.mock import patch

import pytest

from tools.desktop.unified_computer_service import UnifiedComputerService


@pytest.mark.parametrize('delivery', [True, False])
def test_account_action_does_not_claim_verified_selection(delivery):
    service = UnifiedComputerService.__new__(UnifiedComputerService)
    service._emergency_stopped = False
    service._stop_requested = False
    service._action_history = []
    prefix = 'tools.desktop.unified_computer_service'
    with patch(f'{prefix}.native_backend') as backend, patch(f'{prefix}.time.sleep'):
        backend.get_screen_resolution.return_value = {'width': 1440, 'height': 900}
        backend.focus_window.return_value = {'verified': delivery}
        backend.click.return_value = {'verified': delivery}
        result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == ('unverified' if delivery else 'error')
    assert result['verified'] is False
    if delivery:
        assert 'not confirmed' in result['spoken_summary']
    assert result['response'] == result['spoken_summary']
    assert service._action_history[-1] == result


def test_stopped_account_action_does_not_send_input():
    service = UnifiedComputerService.__new__(UnifiedComputerService)
    service._emergency_stopped = True
    service._stop_requested = True
    with patch('tools.desktop.unified_computer_service.native_backend') as backend:
        result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == 'blocked'
    backend.click.assert_not_called()
    backend.focus_window.assert_not_called()


@pytest.fixture
def account_service():
    service = UnifiedComputerService.__new__(UnifiedComputerService)
    service._emergency_stopped = False
    service._stop_requested = False
    service._action_history = []
    with patch('tools.desktop.unified_computer_service.native_backend') as backend, patch('tools.desktop.unified_computer_service.time.sleep'):
        backend.get_screen_resolution.return_value = {'width': 1440, 'height': 900}
        backend.focus_window.return_value = {'verified': True}
        backend.click.return_value = {'verified': True}
        yield service, backend


@pytest.mark.parametrize('bad', [None, {}, {'verified': False}, {'verified': 'true'}, {'verified': True, 'status': 'error'}])
def test_both_focus_attempts_fail_without_clicking(account_service, bad):
    service, backend = account_service
    backend.focus_window.return_value = bad
    result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['failed_stage'] == 'focus'
    assert result['status'] == 'error'
    assert backend.focus_window.call_count == 2
    backend.click.assert_not_called()


def test_focus_fallback_can_proceed_but_not_verify_account(account_service):
    service, backend = account_service
    backend.focus_window.side_effect = [{'verified': False}, {'verified': True}]
    result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == 'unverified'
    assert backend.click.call_count == 2


@pytest.mark.parametrize('failed_click', [1, 2])
@pytest.mark.parametrize('bad', [None, {}, {'verified': False}, {'status': 'error', 'verified': True}, RuntimeError('adapter failed')])
def test_click_failure_stops_remaining_inputs(account_service, failed_click, bad):
    service, backend = account_service
    backend.click.side_effect = [{'verified': True}] * (failed_click - 1) + [bad]
    result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == 'error'
    assert result['verified'] is False
    assert result['failed_stage'] == ('avatar_click' if failed_click == 1 else 'menu_click')
    assert backend.click.call_count == failed_click
    assert service._action_history[-1] == result


def test_focus_exception_does_not_click(account_service):
    service, backend = account_service
    backend.focus_window.side_effect = RuntimeError('adapter failed')
    result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == 'error'
    backend.click.assert_not_called()


@pytest.mark.parametrize('stop_stage,click_count', [(1, 0), (2, 0), (3, 1)])
def test_progress_cancellation_prevents_next_input(account_service, stop_stage, click_count):
    service, backend = account_service
    events = []
    def progress(event):
        events.append(event)
        if len(events) == stop_stage:
            service._stop_requested = True
    result = service.browser_ui_action('switch_youtube_account', target='Work account', on_progress=progress)
    assert result['status'] == 'cancelled'
    assert backend.click.call_count == click_count


def test_emergency_stop_between_clicks_prevents_next_input(account_service):
    service, backend = account_service
    def click(**kwargs):
        service._emergency_stopped = True
        return {'verified': True}
    backend.click.side_effect = click
    result = service.browser_ui_action('switch_youtube_account', target='Work account')
    assert result['status'] == 'cancelled'
    assert backend.click.call_count == 1


@pytest.mark.parametrize('status', ['error', 'unverified', 'cancelled', 'blocked', 'ok'])
def test_dispatcher_preserves_browser_outcome_and_target(status):
    from types import SimpleNamespace
    from ai.capabilities.dispatcher import CapabilityDispatcher
    from ai.capabilities.models import CapabilityInvocationRequest
    dispatcher = CapabilityDispatcher.__new__(CapabilityDispatcher)
    request = CapabilityInvocationRequest(
        capability_id='desktop', action_id='browser_ui_action',
        parameters={'action': 'switch_youtube_account', 'target': 'Work account'},
    )
    reply = {'status': status, 'verified': False, 'response': 'Observed result', 'spoken_summary': 'Observed result'}
    with patch('tools.desktop.unified_computer_service.unified_computer_service.browser_ui_action', return_value=reply) as action:
        result = dispatcher._dispatch_desktop_tools(SimpleNamespace(id='desktop'), request)
    assert result.status == status
    assert result.data == reply
    assert result.spoken_summary == 'Observed result'
    action.assert_called_once_with(action='switch_youtube_account', target='Work account')


def test_dispatcher_does_not_invent_completion_for_missing_result_status():
    from types import SimpleNamespace
    from ai.capabilities.dispatcher import CapabilityDispatcher
    from ai.capabilities.models import CapabilityInvocationRequest
    dispatcher = CapabilityDispatcher.__new__(CapabilityDispatcher)
    request = CapabilityInvocationRequest(capability_id='desktop', action_id='browser_ui_action')
    with patch('tools.desktop.unified_computer_service.unified_computer_service.browser_ui_action', return_value={}):
        result = dispatcher._dispatch_desktop_tools(SimpleNamespace(id='desktop'), request)
    assert result.status == 'error'
    assert 'unavailable' in result.spoken_summary


@pytest.mark.parametrize('source', ['chat', 'voice'])
@pytest.mark.parametrize('failure', ['focus', 'click', None])
def test_public_dispatcher_routes_real_account_result(account_service, source, failure):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from ai.capabilities.dispatcher import CapabilityDispatcher
    from ai.capabilities.models import CapabilityInvocationRequest
    service, backend = account_service
    if failure == 'focus':
        backend.focus_window.return_value = {'verified': False}
    if failure == 'click':
        backend.click.return_value = {'verified': False}
    cap = SimpleNamespace(
        id='desktop-pc-tools', name='Desktop', minimum_role='USER', is_cli=False,
        actions=[SimpleNamespace(action_id='browser_ui_action')],
    )
    dispatcher = CapabilityDispatcher.__new__(CapabilityDispatcher)
    dispatcher.registry = Mock()
    dispatcher.registry.get_capability.return_value = cap
    request = CapabilityInvocationRequest(
        capability_id=cap.id, action_id='browser_ui_action', source=source,
        parameters={'action': 'switch_youtube_account', 'target': 'Work account'},
    )
    with patch('tools.desktop.unified_computer_service.unified_computer_service', service):
        result = dispatcher.execute(request)
    assert result.status == ('error' if failure else 'unverified')
    assert result.data['verified'] is False
    assert result.spoken_summary == result.data['spoken_summary']
    if failure == 'focus':
        backend.click.assert_not_called()
    elif failure == 'click':
        assert backend.click.call_count == 1


@pytest.mark.parametrize('target', [None, '', '   ', 42, ['Work account']])
def test_missing_account_target_asks_without_observation_or_input(account_service, target):
    service, backend = account_service
    result = service.browser_ui_action('switch_youtube_account', target=target)
    assert result['status'] == 'needs_input'
    assert result['verified'] is False
    assert 'Which signed-in account' in result['spoken_summary']
    backend.get_screen_resolution.assert_not_called()
    backend.focus_window.assert_not_called()
    backend.click.assert_not_called()

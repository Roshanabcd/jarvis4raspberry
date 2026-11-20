"""Explicit, bounded provider smoke checks; never return upstream bodies or keys."""
import copy
import time
from ai.providers.credentials import usable_key


def probe_provider(provider):
    result = {'provider': provider.name, 'model': provider.model, 'status': 'not_tested'}
    if not provider.enabled:
        return {**result, 'status': 'disabled'}
    if hasattr(provider, 'api_key') and not usable_key(provider.api_key):
        return {**result, 'status': 'missing_key'}
    client = copy.copy(provider)
    client.timeout = 20.0
    started = time.monotonic()
    try:
        answer = client.generate([{'role': 'user', 'content': 'Reply with exactly JARVIS_OK.'}],
                                 max_tokens=256, temperature=0)
        elapsed = round((time.monotonic() - started) * 1000)
        if not isinstance(answer, dict):
            return {**result, 'status': 'invalid_response', 'latency_ms': elapsed}
        if answer.get('error'):
            code = answer.get('http_status')
            status = {401: 'authentication_failed', 403: 'access_denied', 404: 'model_or_endpoint_unavailable', 410: 'model_or_endpoint_unavailable',
                      429: 'rate_or_quota_limited'}.get(code, 'request_failed')
            # Never expose raw upstream messages, even if an adapter returns them.
            return {**result, 'status': status, 'http_status': code, 'latency_ms': elapsed}
        text = answer.get('text') or ''
        return {**result, 'status': 'passed' if text.strip() == 'JARVIS_OK' else
                'unexpected_answer' if text.strip() else 'empty_response', 'latency_ms': elapsed}
    except Exception as exc:
        return {**result, 'status': 'request_failed', 'error': type(exc).__name__,
                'latency_ms': round((time.monotonic() - started) * 1000)}

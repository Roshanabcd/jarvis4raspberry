"""Read-only account-label matching. Never conveys authority to switch accounts."""
from urllib.parse import urlsplit

# Narrow support for visible YouTube account-item renderers. Unknown markup
# yields unavailable rather than treating arbitrary page text as account names.
ACCOUNT_SNAPSHOT_JS = r"""() => {
    const visible = el => {
        if (!el || el.closest('[hidden], [aria-hidden="true"]')) return false;
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return style.display !== 'none' && style.visibility !== 'hidden'
            && rect.width > 0 && rect.height > 0 && el.getClientRects().length > 0;
    };
    const items = [...document.querySelectorAll('ytd-account-item-renderer')];
    const labels = [];
    for (const item of items) {
        if (!visible(item) || item.hasAttribute('disabled') || item.getAttribute('aria-disabled') === 'true') continue;
        const name = item.querySelector('#account-name, #channel-title');
        if (!visible(name)) continue;
        const label = name.innerText.trim();
        if (label && label.length <= 256) labels.push(label);
        if (labels.length >= 100) break;
    }
    return {url: location.href, labels};
}"""


def supported_origin(url):
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == 'https' and parsed.hostname in {'youtube.com', 'www.youtube.com'}
                and not parsed.username and not parsed.password and parsed.port in (None, 443))
    except (ValueError, TypeError):
        return False


def account_result(snapshot, target=None):
    base = {'verified': False, 'scope': 'managed_browser_only', 'read_only': True}
    if not isinstance(snapshot, dict) or not supported_origin(snapshot.get('url')):
        return {**base, 'status': 'unavailable', 'response': 'Not available: the managed page is not a supported YouTube origin.'}
    labels = snapshot.get('labels')
    if not isinstance(labels, list) or len(labels) > 100 or any(not isinstance(x, str) or not x.strip() or len(x) > 256 for x in labels):
        return {**base, 'status': 'unavailable', 'response': 'Not available: account observation was invalid.'}
    if not labels:
        return {**base, 'status': 'unavailable', 'response': 'No supported visible account entries were observed. Open the account switcher in the managed browser; desktop Chrome may be a different session.'}
    candidates = [{'label': label.strip()} for label in labels]
    base.update(candidates=candidates, candidate_count=len(candidates))
    if target is None:
        return {**base, 'status': 'observed', 'response': 'Visible account labels in the managed browser: ' + ', '.join(c['label'] for c in candidates) + '. No account was selected.'}
    if not isinstance(target, str) or not target.strip():
        return {**base, 'status': 'needs_input', 'response': 'Please provide the exact visible account label. No account was selected.'}
    normalize = lambda text: ' '.join(text.split()).casefold()
    matches = [c for c in candidates if normalize(c['label']) == normalize(target)]
    if len(matches) > 1:
        return {**base, 'status': 'needs_input', 'match_count': len(matches), 'response': 'Multiple visible accounts have that label. Please distinguish them in the browser. No account was selected.'}
    if not matches:
        return {**base, 'status': 'needs_input', 'match_count': 0, 'response': 'That exact account label was not observed. Please choose a visible label. No account was selected.'}
    return {**base, 'status': 'observed', 'match_count': 1, 'matched_label': matches[0]['label'], 'response': 'One matching label was observed in the managed browser. This does not verify the active account; no account was selected.'}

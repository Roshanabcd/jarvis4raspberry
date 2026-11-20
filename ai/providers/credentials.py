"""Resolve configured credentials without exposing their values in diagnostics."""
import os

try:
    from dotenv import load_dotenv
    _proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _env_path = os.path.join(_proj_root, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=False)
except Exception:
    pass

ENV_KEYS = {
    'openai': ('OPENAI_API_KEY',),
    'gemini': ('GEMINI_API_KEY', 'GOOGLE_API_KEY'),
    'anthropic': ('ANTHROPIC_API_KEY',),
    'nvidia': ('NVIDIA_API_KEY', 'NIM_API_KEY'),
    'openrouter': ('OPENROUTER_API_KEY',),
    'groq': ('GROQ_API_KEY',),
    'together': ('TOGETHER_API_KEY',),
}


def usable_key(value):
    if not isinstance(value, str) or not value.strip():
        return False
    lowered = value.lower()
    return not any(marker in lowered for marker in ('****', 'replace', 'your-', 'your_', 'placeholder'))


def resolve_key(name, configuration):
    candidates = [os.getenv(key, '') for key in ENV_KEYS.get(name, ())]
    candidates += [(configuration.get('ai', {}).get(name, {}) or {}).get('api_key', ''),
                   configuration.get(name + '_api_key', '')]
    return next((value.strip() for value in candidates if usable_key(value)), '')

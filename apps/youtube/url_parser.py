"""
YouTube URL Validation and Normalization with Comprehensive SSRF Protection.
"""
import ipaddress
import re
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "music.youtube.com",
}

_VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{11}$")

# Denied private/local IP networks (SSRF prevention)
_DENIED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),        # IPv6 Link-Local
]


class InvalidYouTubeUrlError(ValueError):
    """Raised when an invalid, unsupported, or unsafe YouTube URL is provided."""
    pass


class SSRFSecurityError(ValueError):
    """Raised when an SSRF, loopback, or private network exploit is detected."""
    pass


def extract_video_id(url_or_id: str) -> str:
    """
    Extract and validate an 11-character YouTube video ID.
    Raises InvalidYouTubeUrlError or SSRFSecurityError if invalid.
    """
    if not url_or_id or not isinstance(url_or_id, str):
        raise InvalidYouTubeUrlError("URL or video ID must be a non-empty string")

    raw = url_or_id.strip()

    # Direct 11-char ID
    if _VIDEO_ID_REGEX.match(raw):
        return raw

    # Add scheme if omitted but clearly a URL
    if not raw.startswith(("http://", "https://")):
        if raw.startswith(("www.", "youtube.com", "youtu.be", "m.youtube.com")):
            raw = "https://" + raw
        else:
            raise InvalidYouTubeUrlError("Invalid YouTube URL scheme or missing protocol")

    parsed = urlparse(raw)

    # 1. Validate scheme
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported protocol scheme '{parsed.scheme}'; only HTTP/HTTPS permitted")

    # 2. Hostname validation
    host = (parsed.hostname or "").lower()
    if not host:
        raise InvalidYouTubeUrlError("URL has no hostname")

    # Prevent embedded userinfo credentials (e.g. user:pass@host)
    if parsed.username or parsed.password:
        raise SSRFSecurityError("Embedded credentials in URL are prohibited")

    # Prevent non-standard ports
    if parsed.port and parsed.port not in (80, 443):
        raise SSRFSecurityError(f"Prohibited port '{parsed.port}'; only standard ports 80/443 permitted")

    # Check for direct IP access (SSRF detection)
    ip = None
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        pass  # Hostname is a domain name, proceed

    if ip is not None:
        for net in _DENIED_NETWORKS:
            if ip in net:
                raise SSRFSecurityError(f"Host '{host}' resolves to restricted private/local network")
        # If it's a public IP, YouTube doesn't host on bare IPs
        raise InvalidYouTubeUrlError(f"Direct IP access '{host}' is not a valid YouTube domain")

    # Check host against allowlist
    if host not in _ALLOWED_HOSTS:
        # Check subdomains
        if not any(host.endswith("." + allowed) for allowed in ("youtube.com", "youtu.be")):
            raise InvalidYouTubeUrlError(f"Host '{host}' is not an authorized YouTube domain")

    # 3. Extract Video ID based on URL pattern
    video_id: Optional[str] = None
    path = parsed.path.strip("/")

    if host == "youtu.be":
        # Format: https://youtu.be/VIDEO_ID
        parts = path.split("/")
        if parts and parts[0]:
            video_id = parts[0]
    elif "embed" in path:
        # Format: https://www.youtube.com/embed/VIDEO_ID
        parts = path.split("/")
        idx = parts.index("embed") if "embed" in parts else -1
        if idx != -1 and len(parts) > idx + 1:
            video_id = parts[idx + 1]
    elif "shorts" in path:
        # Format: https://www.youtube.com/shorts/VIDEO_ID
        parts = path.split("/")
        idx = parts.index("shorts") if "shorts" in parts else -1
        if idx != -1 and len(parts) > idx + 1:
            video_id = parts[idx + 1]
    else:
        # Standard query param: https://www.youtube.com/watch?v=VIDEO_ID
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            video_id = qs["v"][0]

    if not video_id or not _VIDEO_ID_REGEX.match(video_id):
        raise InvalidYouTubeUrlError(f"Could not extract a valid 11-character video ID from '{url_or_id}'")

    return video_id


def normalize_youtube_url(url_or_id: str) -> Tuple[str, str]:
    """
    Validates input and returns normalized (canonical_url, video_id).
    Canonical URL form: https://www.youtube.com/watch?v=VIDEO_ID
    """
    video_id = extract_video_id(url_or_id)
    canonical = f"https://www.youtube.com/watch?v={video_id}"
    return canonical, video_id


def is_valid_youtube_url(url_or_id: str) -> bool:
    """
    Check if a string is a valid YouTube URL or video ID without raising exceptions.
    """
    try:
        extract_video_id(url_or_id)
        return True
    except Exception:
        return False

"""
Safe HTTP and PDF content extractor for JARVIS AI Research Assistant.
Features SSRF protection, size caps, HTML cleaning, Poppler pdftotext extraction,
and YouTube transcript integration. Never bypasses security controls or paywalls.
"""

from __future__ import annotations

import concurrent.futures
import html
import ipaddress
import logging
import os
import re
import socket
import subprocess
import tempfile
import urllib.parse
from typing import Any, Dict, List, Optional
import requests

from apps.research.models import (
    ExtractionStatus,
    ResearchSource,
    SourceCategory,
)

logger = logging.getLogger("JARVIS-RESEARCH-EXTRACTOR")
USER_AGENT = "JARVIS-OS/0.1.0 (Raspberry Pi 5; ARM64 Linux; SafeExtractor/1.0)"

# Maximum byte size for downloading web pages (100 KB) and PDFs (3 MB)
MAX_HTML_BYTES = 100 * 1024
MAX_PDF_BYTES = 3 * 1024 * 1024
DEFAULT_TIMEOUT = 8


class SSRFSecurityError(ValueError):
    """Raised when a URL attempts to connect to private or loopback networks."""
    pass


def validate_url_ssrf(url: str) -> None:
    """
    Validate that the given URL does not target loopback, link-local,
    private RFC1918 subnets, or cloud metadata services.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityError("Empty or invalid URL")

    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityError(f"Unsupported URL scheme: {parsed.scheme}")

    host = parsed.hostname
    if not host:
        raise SSRFSecurityError("Missing hostname in URL")

    # Reject localhost aliases
    if host.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise SSRFSecurityError(f"Direct localhost reference rejected: {host}")

    # Check IP directly or resolve hostname via DNS
    try:
        ip = ipaddress.ip_address(host)
        ip_addresses = [ip]
    except ValueError:
        # Not a raw IP, resolve via DNS
        try:
            addr_info = socket.getaddrinfo(host, None)
            ip_addresses = []
            for item in addr_info:
                sockaddr = item[4]
                ip_str = sockaddr[0]
                try:
                    ip_addresses.append(ipaddress.ip_address(ip_str))
                except ValueError:
                    pass
        except socket.gaierror as exc:
            raise SSRFSecurityError(f"DNS resolution failed for {host}: {exc}")

    if not ip_addresses:
        raise SSRFSecurityError(f"No IP addresses resolved for {host}")

    # Inspect each resolved IP
    for ip in ip_addresses:
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or str(ip) == "169.254.169.254"
        ):
            raise SSRFSecurityError(f"Access to private/local network address {ip} blocked for host {host}")


def _clean_html_text(raw_html: str) -> tuple[str, str, List[str], Optional[str]]:
    """
    Parse HTML to extract title, body text, authors, and published date.
    Returns: (title, cleaned_body, authors, published_date)
    """
    title = ""
    authors: List[str] = []
    pub_date: Optional[str] = None

    # Title extraction
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = html.unescape(title_match.group(1)).strip()
        title = re.sub(r"\s+", " ", title)

    # Meta tags extraction
    for meta in re.finditer(r"<meta\s+([^>]+)>", raw_html, re.IGNORECASE):
        content_attr = re.search(r'content=["\']([^"\']+)["\']', meta.group(1), re.IGNORECASE)
        name_attr = re.search(r'(?:name|property)=["\']([^"\']+)["\']', meta.group(1), re.IGNORECASE)
        if content_attr and name_attr:
            val = html.unescape(content_attr.group(1)).strip()
            name = name_attr.group(1).lower()

            if name in ("author", "article:author", "dc.creator") and val not in authors:
                authors.append(val)
            elif name in ("article:published_time", "publication_date", "date", "dc.date") and not pub_date:
                pub_date = val[:10]
            elif name in ("og:title", "twitter:title") and not title:
                title = val

    # Clean body
    # Remove script, style, nav, footer, header, svg, noscript
    cleaned = re.sub(
        r"<(script|style|nav|footer|header|svg|noscript|iframe)[^>]*>.*?</\1>",
        " ",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Replace block level elements with newlines
    cleaned = re.sub(r"<(?:p|div|h[1-6]|li|tr|blockquote)[^>]*>", "\n", cleaned, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Unescape entities
    cleaned = html.unescape(cleaned)
    # Collapse excess whitespace
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    body_text = "\n\n".join(lines)

    return title, body_text, authors, pub_date


class ContentExtractor:
    """Safe content extractor for web pages, PDFs, and academic documents."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def extract_source(self, source: ResearchSource) -> ResearchSource:
        """
        Extract full or partial text content for a single ResearchSource.
        Updates source.content, source.extraction_status, and metadata in-place.
        """
        if not source.url:
            return source

        url = source.url.strip()

        # Check for YouTube URL first
        if self._is_youtube_url(url):
            return self._extract_youtube(source)

        # SSRF Security Check
        try:
            validate_url_ssrf(url)
        except SSRFSecurityError as sec_err:
            logger.warning(f"SSRF Check blocked URL {url}: {sec_err}")
            source.extraction_status = ExtractionStatus.ACCESS_BLOCKED
            if not source.content:
                source.content = f"Access to this URL was blocked by security policy: {sec_err}"
            return source

        # If it's a PDF link or ends in .pdf
        if url.lower().endswith(".pdf") or "/pdf/" in url.lower():
            return self._extract_pdf(source)

        # Standard Web Page (HTML)
        return self._extract_web_page(source)

    def _extract_web_page(self, source: ResearchSource) -> ResearchSource:
        """Extract text from an HTML web page with size capping."""
        url = source.url
        try:
            resp = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
                headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
            )

            # SSRF check on final redirected URL as well
            if resp.url != url:
                try:
                    validate_url_ssrf(resp.url)
                except SSRFSecurityError as red_err:
                    source.extraction_status = ExtractionStatus.ACCESS_BLOCKED
                    source.content = f"Redirected URL blocked by security policy: {red_err}"
                    return source

            if resp.status_code == 403 or resp.status_code == 401:
                source.extraction_status = ExtractionStatus.ACCESS_BLOCKED
                if not source.content:
                    source.content = f"Access denied (HTTP {resp.status_code}). Content may require authentication or paywall."
                return source

            if resp.status_code >= 400:
                source.extraction_status = ExtractionStatus.SOURCE_UNAVAILABLE
                if not source.content:
                    source.content = f"Source returned HTTP error status {resp.status_code}."
                return source

            content_type = resp.headers.get("Content-Type", "").lower()
            if "application/pdf" in content_type:
                return self._extract_pdf(source)

            # Read up to MAX_HTML_BYTES
            content_bytes = bytearray()
            for chunk in resp.iter_content(chunk_size=4096):
                content_bytes.extend(chunk)
                if len(content_bytes) >= MAX_HTML_BYTES:
                    break

            encoding = resp.encoding or "utf-8"
            try:
                html_text = content_bytes.decode(encoding, errors="replace")
            except Exception:
                html_text = content_bytes.decode("utf-8", errors="replace")

            title, body_text, authors, pub_date = _clean_html_text(html_text)

            if title and (not source.title or source.title == url):
                source.title = title
            if authors and not source.authors:
                source.authors = authors
            if pub_date and not source.published_date:
                source.published_date = pub_date

            if len(body_text) >= 100:
                source.content = body_text[:40000]
                source.summary = body_text[:400]
                source.extraction_status = ExtractionStatus.FULL_CONTENT_RETRIEVED
                source.is_abstract_only = False
            elif len(body_text) > 30:
                source.content = body_text
                source.summary = body_text
                source.extraction_status = ExtractionStatus.PARTIAL_CONTENT_RETRIEVED
            elif source.content:
                # Retain existing abstract or summary
                source.extraction_status = ExtractionStatus.PARTIAL_CONTENT_RETRIEVED
            else:
                source.extraction_status = ExtractionStatus.METADATA_ONLY

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout extracting URL: {url}")
            if not source.content:
                source.extraction_status = ExtractionStatus.SOURCE_UNAVAILABLE
                source.content = "Request timed out while connecting to host."
        except Exception as exc:
            logger.warning(f"Error extracting URL {url}: {exc}")
            if not source.content:
                source.extraction_status = ExtractionStatus.EXTRACTION_FAILED
                source.content = f"Extraction failed: {str(exc)}"

        return source

    def _extract_pdf(self, source: ResearchSource) -> ResearchSource:
        """Download and extract plain text from PDF using poppler pdftotext."""
        url = source.url
        temp_pdf = None
        try:
            resp = self.session.get(url, timeout=self.timeout + 4, stream=True)
            if resp.status_code != 200:
                if not source.content:
                    source.extraction_status = ExtractionStatus.SOURCE_UNAVAILABLE
                return source

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                temp_pdf = f.name
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= MAX_PDF_BYTES:
                        break

            # Execute /usr/bin/pdftotext
            cmd = ["/usr/bin/pdftotext", "-layout", temp_pdf, "-"]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6, text=True)
            if proc.returncode == 0 and proc.stdout.strip():
                extracted = proc.stdout.strip()
                source.content = extracted[:50000]
                source.summary = extracted[:400]
                source.extraction_status = ExtractionStatus.FULL_CONTENT_RETRIEVED
                source.is_abstract_only = False
            else:
                if not source.content:
                    source.extraction_status = ExtractionStatus.PARTIAL_CONTENT_RETRIEVED

        except Exception as exc:
            logger.warning(f"PDF extraction error for {url}: {exc}")
            # Keep previous abstract if present
            if not source.content:
                source.extraction_status = ExtractionStatus.PARTIAL_CONTENT_RETRIEVED
        finally:
            if temp_pdf and os.path.exists(temp_pdf):
                try:
                    os.remove(temp_pdf)
                except OSError:
                    pass

        return source

    @staticmethod
    def _is_youtube_url(url: str) -> bool:
        """Check if URL targets YouTube."""
        parsed = urllib.parse.urlparse(url)
        return "youtube.com" in parsed.netloc.lower() or "youtu.be" in parsed.netloc.lower()

    def _extract_youtube(self, source: ResearchSource) -> ResearchSource:
        """Integrate with Phase 11 YouTube AI database if available."""
        url = source.url
        try:
            from apps.youtube.url_parser import parse_youtube_url
            from apps.youtube.database import get_youtube_db

            parsed = parse_youtube_url(url)
            video_id = parsed.video_id
            db = get_youtube_db()
            video = db.get_video(video_id)

            if video:
                source.title = video.title or source.title
                source.published_date = video.published_at or source.published_date
                source.publisher_or_domain = f"YouTube ({video.channel_title})" if video.channel_title else "YouTube"
                source.category = SourceCategory.REPUTABLE_SECONDARY_SOURCE

                summary = db.get_summary(video_id)
                transcript = db.get_transcript(video_id)

                if transcript and transcript.full_text:
                    source.content = transcript.full_text[:40000]
                    source.summary = (summary.executive_summary if summary else transcript.full_text[:400])
                    source.extraction_status = ExtractionStatus.FULL_CONTENT_RETRIEVED
                    return source
                elif summary and summary.executive_summary:
                    source.content = f"Executive Summary: {summary.executive_summary}\n\nKey Takeaways:\n" + "\n".join(
                        f"- {t}" for t in summary.key_takeaways
                    )
                    source.summary = summary.executive_summary[:400]
                    source.extraction_status = ExtractionStatus.PARTIAL_CONTENT_RETRIEVED
                    return source

        except Exception as exc:
            logger.info(f"YouTube database lookup not available for {url}: {exc}")

        # Fall back to standard page extraction
        return self._extract_web_page(source)

    def batch_extract(self, sources: List[ResearchSource], max_workers: int = 4) -> List[ResearchSource]:
        """Extract content from multiple sources concurrently."""
        if not sources:
            return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_src = {executor.submit(self.extract_source, src): src for src in sources}
            completed_sources = []
            for future in concurrent.futures.as_completed(future_to_src):
                try:
                    res = future.result()
                    completed_sources.append(res)
                except Exception as exc:
                    src = future_to_src[future]
                    logger.warning(f"Batch extract error for {src.url}: {exc}")
                    completed_sources.append(src)

        return completed_sources

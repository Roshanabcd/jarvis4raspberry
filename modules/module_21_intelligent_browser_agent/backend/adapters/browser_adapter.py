"""Browser automation adapter contract, real HTML DOM extractor & SafeSimulatedBrowserAdapter."""

from __future__ import annotations

import base64
import io
from abc import ABC, abstractmethod
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw

from modules.module_21_intelligent_browser_agent.backend.models.database import utc_now_iso


class DOMExtractorParser(HTMLParser):
    """Real stdlib HTML DOM parser extracting title, headings, links, forms, inputs, and text."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.headings: List[Dict[str, str]] = []
        self.links: List[Dict[str, str]] = []
        self.forms: List[Dict[str, Any]] = []
        self.text_chunks: List[str] = []
        self._current_tag: Optional[str] = None
        self._current_link: Optional[Dict[str, str]] = None
        self._current_form: Optional[Dict[str, Any]] = None

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        self._current_tag = tag
        if tag == "a":
            self._current_link = {"href": a.get("href", ""), "text": ""}
        elif tag == "form":
            self._current_form = {"id": a.get("id", f"form-{len(self.forms)+1}"), "action": a.get("action", ""), "method": a.get("method", "POST"), "inputs": []}
        elif tag in ("input", "textarea", "select") and self._current_form is not None:
            self._current_form["inputs"].append({"name": a.get("name", ""), "type": a.get("type", tag), "placeholder": a.get("placeholder", "")})

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link is not None:
            self.links.append(self._current_link)
            self._current_link = None
        elif tag == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None
        self._current_tag = None

    def handle_data(self, data: str) -> None:
        txt = data.strip()
        if not txt:
            return
        if self._current_tag == "title":
            self.title += txt
        elif self._current_tag in ("h1", "h2", "h3"):
            self.headings.append({"tag": self._current_tag, "text": txt})
        elif self._current_link is not None:
            self._current_link["text"] = (self._current_link["text"] + " " + txt).strip()
        if self._current_tag not in ("script", "style"):
            self.text_chunks.append(txt)


def extract_dom(html: str) -> Dict[str, Any]:
    parser = DOMExtractorParser()
    parser.feed(html)
    return {
        "title": parser.title,
        "headings": parser.headings,
        "links": parser.links,
        "forms": parser.forms,
        "text_preview": " ".join(parser.text_chunks)[:600],
        "element_counts": {
            "headings": len(parser.headings),
            "links": len(parser.links),
            "forms": len(parser.forms),
        },
    }


SIMULATED_PAGES: Dict[str, str] = {
    "https://docs.jarvis.local/overview": """
    <html><head><title>JARVIS OS Architecture Docs</title></head><body>
      <h1>JARVIS OS Modular Architecture</h1>
      <h2>Core Agent Layer</h2>
      <p>Module 21 provides policy-governed browser automation with human approval gates.</p>
      <a href="https://portal.jarvis.local/feedback">Submit Operator Feedback</a>
      <a href="https://releases.jarvis.local/downloads">Download Release Notes</a>
    </body></html>
    """,
    "https://portal.jarvis.local/feedback": """
    <html><head><title>JARVIS Operator Portal — Feedback Form</title></head><body>
      <h1>Operator Feedback &amp; Telemetry Submission</h1>
      <form id="feedback-form" action="/submit" method="POST">
        <input name="operator" type="text" placeholder="Operator Name" />
        <input name="module" type="text" placeholder="Module ID" />
        <textarea name="notes" placeholder="Observations"></textarea>
      </form>
      <a href="https://docs.jarvis.local/overview">Back to Docs</a>
    </body></html>
    """,
    "https://releases.jarvis.local/downloads": """
    <html><head><title>JARVIS Releases &amp; Artifacts</title></head><body>
      <h1>JARVIS OS Verified Release Manifests</h1>
      <a href="https://releases.jarvis.local/files/jarvis_release_notes.txt">jarvis_release_notes.txt</a>
      <a href="https://docs.jarvis.local/overview">Architecture Overview</a>
    </body></html>
    """,
}

SIMULATED_FILES: Dict[str, bytes] = {
    "https://releases.jarvis.local/files/jarvis_release_notes.txt": (
        b"JARVIS OS Release Notes (Simulated Local Fixture)\n"
        b"Module 21 Intelligent Browser Agent verified.\n"
    ),
}


class BrowserAutomationAdapter(ABC):
    adapter_name: str = "abstract"
    is_simulated: bool = True

    @abstractmethod
    def fetch_page(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def submit_form(self, url: str, form_id: str, fields: Dict[str, str]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_download(self, url: str) -> tuple[str, bytes]:
        raise NotImplementedError

    @abstractmethod
    def capture_and_analyze_screenshot(self, url: str, dom: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class SafeSimulatedBrowserAdapter(BrowserAutomationAdapter):
    adapter_name = "safe_simulated_browser"
    is_simulated = True

    def fetch_page(self, url: str) -> Dict[str, Any]:
        html = SIMULATED_PAGES.get(url)
        if not html:
            html = f"<html><head><title>Simulated Page: {url}</title></head><body><h1>Simulated Viewport</h1><p>Loaded authorized URL {url}</p></body></html>"
        return {"url": url, "status_code": 200, "html": html, "simulated": True}

    def submit_form(self, url: str, form_id: str, fields: Dict[str, str]) -> Dict[str, Any]:
        return {
            "simulated": True,
            "url": url,
            "form_id": form_id,
            "submitted_fields": fields,
            "confirmation": f"[SIMULATED] Form '{form_id}' submitted after human approval.",
            "timestamp": utc_now_iso(),
        }

    def fetch_download(self, url: str) -> tuple[str, bytes]:
        data = SIMULATED_FILES.get(url, f"Simulated download payload from {url}\n".encode("utf-8"))
        filename = url.rstrip("/").split("/")[-1] or "download.txt"
        return filename, data

    def capture_and_analyze_screenshot(self, url: str, dom: Dict[str, Any]) -> Dict[str, Any]:
        w, h = 920, 480
        img = Image.new("RGB", (w, h), color=(5, 11, 22))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w, 40], fill=(16, 30, 48))
        draw.line([(0, 40), (w, 40)], fill=(0, 217, 255), width=2)
        safe = lambda s: str(s).encode("ascii", "replace").decode("ascii")
        draw.text((14, 13), safe(f"JARVIS BROWSER AGENT (SIMULATED) | {url[:68]}"), fill=(0, 217, 255))
        draw.text((24, 64), safe(dom.get("title") or "Untitled Page"), fill=(240, 248, 255))
        y = 104
        for hd in dom.get("headings", [])[:4]:
            draw.text((24, y), safe(f"[{hd['tag'].upper()}] {hd['text'][:70]}"), fill=(37, 230, 162))
            y += 28
        for fm in dom.get("forms", [])[:2]:
            draw.rectangle([24, y, 560, y + 64], fill=(16, 30, 48), outline=(152, 104, 255), width=2)
            draw.text((34, y + 10), safe(f"FORM #{fm['id']} ({len(fm['inputs'])} fields)"), fill=(210, 189, 255))
            y += 78
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return {
            "simulated": True,
            "width": w,
            "height": h,
            "image_b64": base64.b64encode(buf.getvalue()).decode("ascii"),
            "analysis": {
                "page_title": dom.get("title", ""),
                "interactive_forms": len(dom.get("forms", [])),
                "navigable_links": len(dom.get("links", [])),
                "has_submission_gate": len(dom.get("forms", [])) > 0,
            },
        }

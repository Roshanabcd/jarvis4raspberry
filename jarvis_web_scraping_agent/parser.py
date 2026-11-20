"""Pure-stdlib structured HTML parser extracting titles, meta, headings, links, tables, and text."""

from __future__ import annotations

import hashlib
import urllib.parse
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple


class _StructuredHTMLParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self, base_url: str = "", target_tag: Optional[str] = None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.target_tag = target_tag.lower().strip() if target_tag else None

        self.skip_depth = 0
        self.in_title = False
        self.title_parts: List[str] = []
        self.meta_description = ""

        self.heading_tag: Optional[str] = None
        self.heading_buf: List[str] = []
        self.headings: List[str] = []

        self.link_href: Optional[str] = None
        self.link_buf: List[str] = []
        self.links: List[Dict[str, str]] = []

        self.in_table = False
        self.current_table: List[List[str]] = []
        self.current_row: List[str] = []
        self.in_cell = False
        self.cell_buf: List[str] = []
        self.tables: List[List[List[str]]] = []

        self.target_depth = 0
        self.target_buf: List[str] = []
        self.targeted_elements: List[str] = []

        self.text_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}

        if t in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if t == "title":
            self.in_title = True
        elif t == "meta" and attr_map.get("name", "").lower() == "description":
            if not self.meta_description and attr_map.get("content"):
                self.meta_description = attr_map["content"].strip()
        elif t in ("h1", "h2", "h3"):
            self.heading_tag = t
            self.heading_buf = []
        elif t == "a" and attr_map.get("href"):
            href = attr_map["href"].strip()
            if self.base_url:
                href = urllib.parse.urljoin(self.base_url, href)
            self.link_href = href
            self.link_buf = []
        elif t == "table":
            self.in_table = True
            self.current_table = []
        elif t == "tr" and self.in_table:
            self.current_row = []
        elif t in ("td", "th") and self.in_table:
            self.in_cell = True
            self.cell_buf = []

        if self.target_tag and t == self.target_tag:
            self.target_depth += 1
            if self.target_depth == 1:
                self.target_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
            return

        if t == "title":
            self.in_title = False
        elif t == self.heading_tag:
            txt = " ".join("".join(self.heading_buf).split())
            if txt:
                self.headings.append(txt)
            self.heading_tag = None
        elif t == "a" and self.link_href is not None:
            txt = " ".join("".join(self.link_buf).split())
            self.links.append({"text": txt or self.link_href, "href": self.link_href})
            self.link_href = None
        elif t in ("td", "th") and self.in_cell:
            self.current_row.append(" ".join("".join(self.cell_buf).split()))
            self.in_cell = False
        elif t == "tr" and self.in_table:
            if any(cell for cell in self.current_row):
                self.current_table.append(self.current_row)
            self.current_row = []
        elif t == "table" and self.in_table:
            if self.current_table:
                self.tables.append(self.current_table)
            self.in_table = False

        if self.target_tag and t == self.target_tag and self.target_depth > 0:
            self.target_depth -= 1
            if self.target_depth == 0:
                txt = " ".join("".join(self.target_buf).split())
                if txt:
                    self.targeted_elements.append(txt)

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            return
        if self.in_title:
            self.title_parts.append(data)
        if self.heading_tag:
            self.heading_buf.append(data)
        if self.link_href is not None:
            self.link_buf.append(data)
        if self.in_cell:
            self.cell_buf.append(data)
        if self.target_depth > 0:
            self.target_buf.append(data)
        cleaned = data.strip()
        if cleaned:
            self.text_chunks.append(cleaned)


def parse_html_structure(
    html: str,
    base_url: str = "",
    target_tag: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse HTML into structured JSON-ready fields and compute a deterministic SHA-256 hash."""
    parser = _StructuredHTMLParser(base_url=base_url, target_tag=target_tag)
    parser.feed(html)
    parser.close()

    full_text = "\n".join(parser.text_chunks)
    basis_for_hash = "\n".join(parser.targeted_elements) if parser.targeted_elements else full_text
    content_hash = hashlib.sha256(basis_for_hash.encode("utf-8")).hexdigest()

    return {
        "title": " ".join("".join(parser.title_parts).split()),
        "meta_description": parser.meta_description,
        "headings": parser.headings[:100],
        "links": parser.links[:200],
        "tables": parser.tables[:30],
        "targeted_elements": parser.targeted_elements[:100],
        "full_text": full_text,
        "text_preview": full_text[:1500],
        "word_count": len(full_text.split()),
        "content_hash": content_hash,
    }

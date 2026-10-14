"""Step 1 of the pipeline: download a web page and turn it into clean text for the AI."""

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 WebsiteAnalyzer/0.1"
)
REQUEST_TIMEOUT_SECONDS = 20
MAX_TEXT_CHARS = 40_000  # plenty for a homepage; keeps cost and latency predictable


class FetchError(Exception):
    """Raised when the website cannot be downloaded or has no readable content."""


@dataclass
class PageContent:
    url: str
    title: str = ""
    description: str = ""
    headings: list[str] = field(default_factory=list)
    nav_links: list[str] = field(default_factory=list)
    text: str = ""

    def to_prompt_text(self) -> str:
        """Render the extracted content as a compact, labelled block for the AI prompt."""
        parts = [f"URL: {self.url}"]
        if self.title:
            parts.append(f"Page title: {self.title}")
        if self.description:
            parts.append(f"Meta description: {self.description}")
        if self.nav_links:
            parts.append("Navigation menu: " + " | ".join(self.nav_links))
        if self.headings:
            parts.append("Headings:\n" + "\n".join(f"- {h}" for h in self.headings))
        if self.text:
            parts.append("Visible page text:\n" + self.text)
        return "\n\n".join(parts)


def normalize_url(raw: str) -> str:
    """Accept 'example.com' or 'https://example.com/...' and return a full http(s) URL."""
    url = (raw or "").strip()
    if not url:
        raise FetchError("Please enter a website URL.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise FetchError(f"Only http/https links are supported (got '{parsed.scheme}').")
    host = parsed.hostname
    if not host or ("." not in host and host != "localhost"):
        raise FetchError(f"'{raw}' does not look like a valid website address.")
    return url


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _unique(items, limit):
    seen, out = set(), []
    for item in items:
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
        if len(out) >= limit:
            break
    return out


def parse_html(url: str, html: str) -> PageContent:
    """Extract title, description, headings, nav links and visible text from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = _clean(soup.title.get_text()) if soup.title else ""

    description = ""
    for attrs in ({"name": "description"}, {"property": "og:description"}):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            description = _clean(tag["content"])
            break

    for tag in soup(["script", "style", "noscript", "svg", "iframe", "template"]):
        tag.decompose()

    headings = _unique((_clean(h.get_text(" ")) for h in soup.find_all(["h1", "h2", "h3"])), 40)

    nav_texts = []
    for nav in soup.find_all(["nav", "header"]):
        nav_texts.extend(_clean(a.get_text(" ")) for a in nav.find_all("a"))
    nav_links = _unique((t for t in nav_texts if 0 < len(t) <= 40), 30)

    body = soup.body or soup
    text = _clean(body.get_text(" "))
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + " [...truncated]"

    return PageContent(
        url=url,
        title=title,
        description=description,
        headings=headings,
        nav_links=nav_links,
        text=text,
    )


def fetch_page(raw_url: str, session: requests.Session | None = None) -> PageContent:
    """Download the URL and return its extracted content. Raises FetchError on any failure."""
    url = normalize_url(raw_url)
    http = session or requests.Session()
    try:
        resp = http.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
    except requests.exceptions.Timeout:
        raise FetchError(f"The website took too long to respond ({url}).")
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Could not reach {url}: {e.__class__.__name__}")

    if resp.status_code >= 400:
        raise FetchError(f"The website returned HTTP {resp.status_code} for {url}.")

    content_type = resp.headers.get("Content-Type", "")
    if content_type and "html" not in content_type.lower():
        raise FetchError(f"That link is not a web page (content type: {content_type}).")

    page = parse_html(resp.url or url, resp.text)
    if not (page.text or page.title or page.description):
        raise FetchError(
            "The page has no readable text. It may be built entirely with JavaScript "
            "or blocked for automated visitors."
        )
    return page

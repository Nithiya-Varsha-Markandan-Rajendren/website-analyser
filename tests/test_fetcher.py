import pytest
import requests

from analyzer.fetcher import FetchError, fetch_page, normalize_url, parse_html

SAMPLE_HTML = """
<html>
  <head>
    <title>Acme Paddles | Pro Pickleball Gear</title>
    <meta name="description" content="Premium pickleball paddles and balls for every level.">
    <script>var tracking = "should not appear";</script>
    <style>body { color: red; }</style>
  </head>
  <body>
    <header><nav>
      <a href="/">Home</a><a href="/paddles">Paddles</a><a href="/balls">Balls</a>
      <a href="/paddles">Paddles</a>
    </nav></header>
    <h1>Play your best game</h1>
    <h2>Carbon fiber paddles</h2>
    <h2>Tournament balls</h2>
    <p>Free shipping on orders over $50.</p>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, status=200, text=SAMPLE_HTML, content_type="text/html; charset=utf-8", url=None):
        self.status_code = status
        self.text = text
        self.headers = {"Content-Type": content_type}
        self.url = url


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.calls = response, exc, []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if self.exc:
            raise self.exc
        return self.response


# ---- normalize_url -------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("example.com", "https://example.com"),
        ("  https://example.com/path  ", "https://example.com/path"),
        ("http://shop.example.co.uk", "http://shop.example.co.uk"),
        ("localhost:8000", "https://localhost:8000"),
    ],
)
def test_normalize_url_valid(raw, expected):
    assert normalize_url(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "ftp://example.com", "notaurl", "https://"])
def test_normalize_url_invalid(raw):
    with pytest.raises(FetchError):
        normalize_url(raw)


# ---- parse_html ----------------------------------------------------------

def test_parse_html_extracts_key_parts():
    page = parse_html("https://acme.test", SAMPLE_HTML)
    assert page.title == "Acme Paddles | Pro Pickleball Gear"
    assert page.description == "Premium pickleball paddles and balls for every level."
    assert page.headings == ["Play your best game", "Carbon fiber paddles", "Tournament balls"]
    assert page.nav_links == ["Home", "Paddles", "Balls"]  # de-duplicated
    assert "Free shipping" in page.text
    assert "tracking" not in page.text and "color: red" not in page.text


def test_parse_html_og_description_fallback():
    html = '<html><head><meta property="og:description" content="OG text"></head><body>x</body></html>'
    assert parse_html("https://a.test", html).description == "OG text"


def test_parse_html_truncates_huge_pages(monkeypatch):
    monkeypatch.setattr("analyzer.fetcher.MAX_TEXT_CHARS", 100)
    page = parse_html("https://a.test", "<html><body>" + "word " * 1000 + "</body></html>")
    assert page.text.endswith("[...truncated]")
    assert len(page.text) < 130


def test_prompt_text_contains_labels():
    prompt = parse_html("https://acme.test", SAMPLE_HTML).to_prompt_text()
    for label in ("URL: https://acme.test", "Page title:", "Meta description:", "Navigation menu:", "Headings:"):
        assert label in prompt


# ---- fetch_page ----------------------------------------------------------

def test_fetch_page_success_uses_final_redirect_url():
    session = FakeSession(FakeResponse(url="https://www.acme.test/"))
    page = fetch_page("acme.test", session=session)
    assert session.calls == ["https://acme.test"]
    assert page.url == "https://www.acme.test/"
    assert page.title.startswith("Acme Paddles")


def test_fetch_page_http_error():
    with pytest.raises(FetchError, match="HTTP 404"):
        fetch_page("acme.test", session=FakeSession(FakeResponse(status=404)))


def test_fetch_page_not_html():
    with pytest.raises(FetchError, match="not a web page"):
        fetch_page("acme.test/file.pdf", session=FakeSession(FakeResponse(content_type="application/pdf")))


def test_fetch_page_timeout():
    with pytest.raises(FetchError, match="too long"):
        fetch_page("acme.test", session=FakeSession(exc=requests.exceptions.Timeout()))


def test_fetch_page_connection_error():
    with pytest.raises(FetchError, match="Could not reach"):
        fetch_page("acme.test", session=FakeSession(exc=requests.exceptions.ConnectionError()))


def test_fetch_page_empty_page():
    with pytest.raises(FetchError, match="no readable text"):
        fetch_page("acme.test", session=FakeSession(FakeResponse(text="<html><body></body></html>")))

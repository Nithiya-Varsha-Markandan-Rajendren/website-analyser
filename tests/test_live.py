"""End-to-end test against a real website and the real Claude API.

Skipped automatically unless ANTHROPIC_API_KEY is set (it costs a few cents per run).
"""

import os

import pytest

from analyzer.ai import analyze_page
from analyzer.fetcher import fetch_page

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set - live test skipped"
)


def test_live_end_to_end():
    page = fetch_page("https://www.python.org")
    result = analyze_page(page)
    assert "python" in result.about.lower()
    assert len(result.features) == 5
    assert all(f.name and f.description for f in result.features)

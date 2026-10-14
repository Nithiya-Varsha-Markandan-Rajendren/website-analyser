from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from analyzer import ai
from analyzer.ai import AnalysisError, Feature, WebsiteAnalysis, analyze_page
from analyzer.fetcher import PageContent

PAGE = PageContent(url="https://acme.test", title="Acme", description="Paddles", text="We sell paddles.")


def make_analysis(n_features=5):
    return WebsiteAnalysis(
        about="Acme sells pickleball gear.",
        category="E-commerce - sports equipment",
        features=[Feature(name=f"Feature {i}", description=f"Desc {i}") for i in range(1, n_features + 1)],
    )


class FakeMessages:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.kwargs = response, exc, None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.exc:
            raise self.exc
        return self.response


def fake_client(response=None, exc=None):
    return SimpleNamespace(messages=FakeMessages(response, exc))


def ok_response(parsed, stop_reason="end_turn"):
    return SimpleNamespace(parsed_output=parsed, stop_reason=stop_reason)


def api_error(cls, status):
    req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("boom", response=httpx2.Response(status, request=req), body=None)


def test_analyze_page_success_and_request_shape():
    client = fake_client(ok_response(make_analysis()))
    result = analyze_page(PAGE, client=client)

    assert result.about == "Acme sells pickleball gear."
    assert len(result.features) == 5

    kw = client.messages.kwargs
    assert kw["model"] == ai.MODEL
    assert kw["output_format"] is WebsiteAnalysis
    assert kw["output_config"] == {"effort": ai.EFFORT}
    assert "We sell paddles." in kw["messages"][0]["content"]
    assert "<website_content>" in kw["messages"][0]["content"]


@pytest.mark.skipif(
    "WEBSITE_ANALYZER_MODEL" in __import__("os").environ, reason="model overridden by env var"
)
def test_default_model_is_low_cost():
    assert ai.MODEL == "claude-haiku-5-5"
    assert ai.EFFORT == "low"


def test_analyze_page_trims_to_five_features():
    result = analyze_page(PAGE, client=fake_client(ok_response(make_analysis(7))))
    assert [f.name for f in result.features] == [f"Feature {i}" for i in range(1, 6)]


@pytest.mark.parametrize(
    "stop_reason, message",
    [("refusal", "declined"), ("max_tokens", "cut off")],
)
def test_analyze_page_bad_stop_reasons(stop_reason, message):
    with pytest.raises(AnalysisError, match=message):
        analyze_page(PAGE, client=fake_client(ok_response(make_analysis(), stop_reason)))


def test_analyze_page_unparseable_output():
    with pytest.raises(AnalysisError, match="unexpected response"):
        analyze_page(PAGE, client=fake_client(ok_response(None)))


@pytest.mark.parametrize(
    "exc, message",
    [
        (api_error(anthropic.AuthenticationError, 401), "API key"),
        (api_error(anthropic.RateLimitError, 429), "rate limit"),
        (api_error(anthropic.InternalServerError, 500), "Claude API error \\(500\\)"),
        (
            anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")),
            "Could not connect",
        ),
    ],
)
def test_analyze_page_api_errors(exc, message):
    with pytest.raises(AnalysisError, match=message):
        analyze_page(PAGE, client=fake_client(exc=exc))

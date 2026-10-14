import builtins

from analyzer import cli
from analyzer.ai import AnalysisError, Feature, WebsiteAnalysis
from analyzer.fetcher import FetchError, PageContent

ANALYSIS = WebsiteAnalysis(
    about="Acme sells pickleball paddles and balls online to players of all levels.",
    category="E-commerce - sports equipment",
    features=[Feature(name=f"Feature {i}", description=f"Description {i}.") for i in range(1, 6)],
)
PAGE = PageContent(url="https://acme.test/", title="Acme Paddles", text="x" * 1234)


def stub_pipeline(monkeypatch, fetch_exc=None, ai_exc=None):
    def fake_fetch(url):
        if fetch_exc:
            raise fetch_exc
        return PAGE

    def fake_analyze(page):
        if ai_exc:
            raise ai_exc
        return ANALYSIS

    monkeypatch.setattr(cli, "fetch_page", fake_fetch)
    monkeypatch.setattr(cli, "analyze_page", fake_analyze)


def test_format_report_has_both_sections():
    report = cli.format_report("https://acme.test/", "Acme Paddles", ANALYSIS)
    assert "1) WHAT THE WEBSITE IS ABOUT" in report
    assert "Category: E-commerce - sports equipment" in report
    assert "2) TOP 5 FEATURES" in report
    for i in range(1, 6):
        assert f"{i}. Feature {i}" in report
    assert all(len(line) <= cli.WIDTH for line in report.splitlines())


def test_main_with_url_argument(monkeypatch, capsys):
    stub_pipeline(monkeypatch)
    assert cli.main(["acme.test"]) == 0
    out = capsys.readouterr().out
    assert "WEBSITE ANALYSIS: https://acme.test/" in out
    assert "1,234 characters" in out


def test_main_warns_on_thin_page(monkeypatch, capsys):
    stub_pipeline(monkeypatch)
    monkeypatch.setattr(cli, "fetch_page", lambda url: PageContent(url="https://thin.test/", text="x" * 300))
    assert cli.main(["thin.test"]) == 0
    assert "very little readable text" in capsys.readouterr().out


def test_main_no_warning_on_normal_page(monkeypatch, capsys):
    stub_pipeline(monkeypatch)
    assert cli.main(["acme.test"]) == 0
    assert "very little readable text" not in capsys.readouterr().out


def test_main_reports_fetch_error(monkeypatch, capsys):
    stub_pipeline(monkeypatch, fetch_exc=FetchError("HTTP 404"))
    assert cli.main(["acme.test"]) == 1
    assert "Error: HTTP 404" in capsys.readouterr().out


def test_main_reports_ai_error(monkeypatch, capsys):
    stub_pipeline(monkeypatch, ai_exc=AnalysisError("No Claude API key found."))
    assert cli.main(["acme.test"]) == 1
    assert "Error: No Claude API key found." in capsys.readouterr().out


def test_interactive_loop_until_quit(monkeypatch, capsys):
    stub_pipeline(monkeypatch)
    inputs = iter(["", "acme.test", "q"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))
    assert cli.main([]) == 0
    assert capsys.readouterr().out.count("WEBSITE ANALYSIS") == 1


def test_interactive_loop_handles_ctrl_c(monkeypatch):
    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr(builtins, "input", raise_interrupt)
    assert cli.main([]) == 0

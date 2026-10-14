"""Step 3 of the pipeline: terminal input/output."""

import sys
import textwrap

from .ai import AnalysisError, WebsiteAnalysis, analyze_page
from .fetcher import FetchError, fetch_page

WIDTH = 78
QUIT_WORDS = {"q", "quit", "exit"}
THIN_PAGE_CHARS = 800


def _wrap(text: str, indent: str = "   ") -> str:
    return textwrap.fill(text, width=WIDTH, initial_indent=indent, subsequent_indent=indent)


def format_report(url: str, title: str, analysis: WebsiteAnalysis) -> str:
    line = "=" * WIDTH
    out = [
        line,
        f" WEBSITE ANALYSIS: {url}",
    ]
    if title:
        out.append(f" Page title: {title}")
    out += [
        line,
        "",
        "1) WHAT THE WEBSITE IS ABOUT",
        f"   Category: {analysis.category}",
        "",
        _wrap(analysis.about),
        "",
        f"2) TOP {len(analysis.features)} FEATURES",
    ]
    for i, feat in enumerate(analysis.features, 1):
        out.append("")
        out.append(f"   {i}. {feat.name}")
        out.append(_wrap(feat.description, indent="      "))
    out += ["", line]
    return "\n".join(out)


def run_once(url: str) -> int:
    print(f"\nFetching {url} ...")
    try:
        page = fetch_page(url)
        print(f"Analysing with AI ({len(page.text):,} characters of page text) ...\n")
        if len(page.text) < THIN_PAGE_CHARS:
            print(
                "Warning: this page has very little readable text (it may load its content with "
                "JavaScript or block automated visitors). Results may be limited.\n"
            )
        analysis = analyze_page(page)
    except (FetchError, AnalysisError) as e:
        print(f"Error: {e}\n")
        return 1
    print(format_report(page.url, page.title, analysis))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        return run_once(args[0])

    print("Website Analyzer - type a website link and press Enter ('q' to quit).")
    status = 0
    while True:
        try:
            url = input("\nWebsite URL: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return status
        if url.lower() in QUIT_WORDS:
            return status
        if url:
            status = run_once(url)

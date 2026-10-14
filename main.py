"""Website Analyzer - entry point.

Usage:
    python main.py                      # interactive: type URLs one after another
    python main.py https://example.com  # analyse a single URL
"""

import sys

from analyzer.env import load_env_file

load_env_file()  # must run before analyzer.ai is imported so .env settings apply

from analyzer.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

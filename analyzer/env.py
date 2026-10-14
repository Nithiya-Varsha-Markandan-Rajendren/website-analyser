"""Load settings (such as ANTHROPIC_API_KEY) from the project's .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path: Path = ENV_FILE) -> None:
    """Read KEY=value lines from .env into the environment.

    Variables already set in the terminal take priority over the file.
    Blank values are dropped so an empty `ANTHROPIC_API_KEY=` line counts as "not set".
    """
    load_dotenv(path, override=False)
    for name in ("ANTHROPIC_API_KEY", "WEBSITE_ANALYZER_MODEL", "WEBSITE_ANALYZER_EFFORT"):
        if name in os.environ and not os.environ[name].strip():
            del os.environ[name]

import sys
from pathlib import Path

# Make the project root importable when running `pytest` from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Pick up ANTHROPIC_API_KEY etc. from .env so the live test can run.
from analyzer.env import load_env_file  # noqa: E402

load_env_file()

import os

from analyzer.env import load_env_file

NAME = "ANTHROPIC_API_KEY"


def test_loads_key_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    env = tmp_path / ".env"
    env.write_text("# comment\nANTHROPIC_API_KEY=sk-ant-test-123\n")
    load_env_file(env)
    assert os.environ[NAME] == "sk-ant-test-123"


def test_blank_key_counts_as_not_set(tmp_path, monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=\n")
    load_env_file(env)
    assert NAME not in os.environ


def test_terminal_value_wins_over_file(tmp_path, monkeypatch):
    monkeypatch.setenv(NAME, "from-terminal")
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=from-file\n")
    load_env_file(env)
    assert os.environ[NAME] == "from-terminal"


def test_missing_file_is_fine(tmp_path, monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    load_env_file(tmp_path / "does-not-exist.env")
    assert NAME not in os.environ

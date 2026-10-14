# Website Analyzer (MVP)

Type a website link in the terminal and get back:

1. **What the website is about**: a short summary plus a business category
2. **Top 5 features**: the main products, services or features the business offers

## How it works

```
 +-----------+     +----------------+     +-----------------+     +-------------+     +-------------+
 |  1. INPUT | --> |  2. FETCH      | --> |  3. EXTRACT     | --> |  4. ANALYSE | --> |  5. OUTPUT  |
 |  Terminal |     |  requests      |     |  BeautifulSoup  |     |  Claude API |     |  Terminal   |
 |  URL      |     |  GET page HTML |     |  title, meta,   |     |  Haiku 5.5 +|     |  formatted  |
 |           |     |                |     |  nav, headings, |     |  structured |     |  report     |
 |  cli.py   |     |  fetcher.py    |     |  text           |     |  output     |     |  cli.py     |
 +-----------+     +----------------+     +-----------------+     |  ai.py      |     +-------------+
                                                                  +-------------+
```

| File | Role |
|---|---|
| `main.py` | Entry point |
| `analyzer/cli.py` | Reads the URL, prints progress, errors and the final report |
| `analyzer/fetcher.py` | Checks the URL, downloads the page, strips scripts/styles, extracts the useful text |
| `analyzer/ai.py` | Sends the text to Claude and gets JSON back that matches a Pydantic schema (`about`, `category`, `features[5]`) |
| `analyzer/env.py` | Loads `ANTHROPIC_API_KEY` and settings from the `.env` file |
| `.env` | Your API key goes here (private, git-ignored) |
| `tests/` | 41 offline tests (network and AI mocked) + 1 live end-to-end test |

## Setup (one time)

```bash
pip install -r requirements.txt
```

Get an API key at https://console.anthropic.com (API Keys), then open the `.env` file in this
folder and paste it after the `=` sign:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxx
```

No quotes and no spaces. Save the file. `.env` is listed in `.gitignore`, so it is never uploaded
to GitHub. A key set in the terminal (`$env:ANTHROPIC_API_KEY = "..."`) takes priority over the file.

## Run

```bash
python main.py                       # interactive: paste links one after another, 'q' to quit
python main.py https://www.python.org   # analyse one link
```

## Test

```bash
python -m pytest -v
```

The live test (`tests/test_live.py`) runs only when `ANTHROPIC_API_KEY` is set.

## Settings (optional, in `.env` or the terminal)

| Variable | Default | Meaning |
|---|---|---|
| `WEBSITE_ANALYZER_MODEL` | `claude-haiku-5-5` | Claude model to use. Haiku is the cheapest; `claude-sonnet-5-5` or `claude-opus-5-5` give deeper analysis at higher cost |
| `WEBSITE_ANALYZER_EFFORT` | `low` | How hard the model thinks: `low` is fastest and cheapest, `medium`/`high` are more thorough |

## Known MVP limits

- Only the page you enter is read (no crawling of other pages on the site).
- Sites that render all their content with JavaScript, or that block bots, may return little or no text.
- Page text is capped at 40,000 characters.

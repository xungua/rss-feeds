# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Read [AGENTS.md](./AGENTS.md) before doing any work.** It is the authoritative source for all operations including adding, testing, and deprecating feeds.

## Commands

```bash
make env_setup              # Install dependencies (uv sync)
make dev_setup              # Install dev deps + pre-commit hooks
make feeds_generate_all     # Run all feed generators
make feeds_<name>           # Run one feed (e.g., feeds_ollama, feeds_anthropic_news)
uv run feed_generators/<source>_blog.py          # Run single generator directly
uv run feed_generators/<source>_blog.py --full   # Full fetch (paginated/cached feeds)
make dev_lint               # Lint with ruff
make dev_lint_fix           # Auto-fix + format with ruff
```

## Architecture

RSS feed generators scrape blogs that lack native RSS feeds and output XML to `feeds/`. A GitHub Action runs hourly via `run_all_feeds.py`.

**Key files:**
- `feeds.yaml` — feed registry (single source of truth); `run_all_feeds.py` reads this, not filesystem
- `feed_generators/utils.py` — shared helpers (`setup_feed_links`, `setup_logging`, `get_project_root`, HTTP defaults)
- `feed_generators/models.py` — Pydantic models (`FeedConfig`, `GlobalSettings`, `load_feed_registry`); settings overridable via `RSS_` env vars

**Three generator patterns** (choose based on how target site loads content):

| Pattern | When | Cache | Reference |
|---|---|---|---|
| Simple Static | All posts in initial HTML | No | `ollama_blog.py` |
| Pagination + Caching | URL-based pagination (`?page=2`) | `cache/<name>_posts.json` | `dagster_blog.py` |
| Selenium + Click | JS-rendered / "Load More" button | `cache/<name>_posts.json` | `anthropic_news_blog.py` |

**Critical: feed link order.** In `feedgen`, `rel="self"` must be set before `rel="alternate"` or the main `<link>` will point to the XML file instead of the blog. Always use `setup_feed_links()` from `utils.py`.

## Adding a New Feed

1. Create `feed_generators/<source>_blog.py` using the appropriate pattern
2. Register in `feeds.yaml` (set `type: requests` or `type: selenium`)
3. Add Make target in `makefiles/feeds.mk`
4. Update README.md table (alphabetical order)
5. Run `make dev_lint_fix` before submitting

See AGENTS.md for the full step-by-step guide including HTML sample analysis, testing, and PR checklist.

## Code Style

- Python 3.11+, ruff for linting/formatting, line length 120
- Lint rules: `F, E, W, I, N, UP, B, SIM, C4, RUF, PERF` (E501 ignored)
- `utils` and `models` are configured as first-party imports in isort

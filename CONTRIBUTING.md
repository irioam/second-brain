# Contributing To Second Brain

Thanks for considering a contribution to Second Brain.

This project handles browser history, which can be sensitive. Contributions are welcome, but privacy and local-first behavior come first.

## Project Priorities

Before opening a pull request, keep these priorities in mind:

1. Protect user privacy.
2. Keep data local by default.
3. Do not overwrite existing Obsidian notes.
4. Avoid committing generated data, caches, browser databases, or personal history.
5. Prefer simple, testable changes.

## Local Setup

Requirements:

- Windows
- Python 3.11+
- `uv`

Install dependencies:

```powershell
uv sync
```

Run the CLI:

```powershell
uv run second-brain --help
```

Run tests:

```powershell
uv run pytest
```

## Development Workflow

1. Create a branch from `main`.
2. Make focused changes.
3. Add or update tests when behavior changes.
4. Run `uv run pytest`.
5. Open a pull request with a clear summary.

Suggested branch names:

```text
fix/short-description
feat/short-description
docs/short-description
```

## Pull Request Expectations

A good pull request includes:

- What changed.
- Why it changed.
- How it was tested.
- Any privacy or data-handling impact.

If your change touches extraction, persistence, semantic clustering, or vault generation, explain what happens to existing user data.

## Do Not Commit Private Or Generated Data

Never commit:

```text
data/
.cache/
.venv/
*.duckdb
*.db
*.sqlite
*.sqlite3
.env
.env.*
```

Use fake URLs and fake data in tests and examples.

Good examples:

```text
https://example.com/docs
https://example.org/article
https://github.com/example/repo
```

Bad examples:

```text
Real browser history
Private company URLs
Client names
Internal systems
Tokens or API keys
```

## Testing Guidelines

Use temporary databases in tests. Do not use real browser history files.

For database behavior, prefer isolated tests with temporary DuckDB files.

For CLI changes, verify the command help still works:

```powershell
uv run second-brain --help
```

## Documentation Guidelines

Update documentation when changing:

- CLI commands or options.
- Default paths.
- Database behavior.
- Privacy behavior.
- Obsidian vault output.

Documentation should be clear enough for a non-expert user to follow.

## Security Issues

Do not report security issues in public issues. Read [SECURITY.md](SECURITY.md) first.

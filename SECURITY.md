# Security Policy

Second Brain processes browser history. Browser history can reveal personal interests, work topics, accounts used, internal systems, private URLs, client names, health research, financial research, and other sensitive information.

Treat every database, generated vault, log file, screenshot, and debug output from this project as potentially private.

## Supported Versions

Security fixes are handled on the `main` branch.

Until the project publishes versioned releases, assume only the latest commit on `main` is supported.

## Reporting A Vulnerability

Do not open a public GitHub issue for security vulnerabilities or privacy leaks.

Report privately by contacting the maintainer:

- GitHub: [https://github.com/irioam](https://github.com/irioam)

When reporting, include:

- A short description of the problem.
- Steps to reproduce it.
- The operating system and Python version.
- The affected command, such as `extract`, `build-vault`, `all`, or `build-semantic`.
- Whether the issue can expose browser history, local file paths, generated notes, embeddings, or DuckDB data.

Do not include:

- Your real browser history.
- DuckDB files from `data/`.
- Obsidian vault exports containing private notes.
- Hugging Face cache files.
- Screenshots that show private URLs, account names, tokens, cookies, or internal systems.
- API keys, access tokens, passwords, or `.env` files.

If a reproduction needs sample data, create a fake minimal dataset with dummy URLs such as:

```text
https://example.com/docs
https://example.org/article
https://github.com/example/repo
```

## Expected Response

The maintainer will try to:

1. Acknowledge the report.
2. Reproduce and assess the issue.
3. Prioritize fixes for issues that expose private data, overwrite user notes, corrupt databases, or execute unexpected code.
4. Credit the reporter if requested and appropriate.

This project is maintained as a personal/open-source project, so response times are best effort.

## Security And Privacy Boundaries

Second Brain is designed to run locally. It should not intentionally upload browser history, DuckDB databases, generated Markdown notes, embeddings, or logs to external services.

Important boundaries:

- Browser history is read from local browser databases.
- Consolidated data is stored locally in DuckDB.
- Generated notes are written locally to an Obsidian-compatible folder.
- Existing Markdown files should not be overwritten by default.
- Generated databases, caches, and temporary browser-history copies must not be committed to Git.

## Sensitive Files

Never commit these files or folders:

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

If any of these files are accidentally committed, remove them from the current Git tree immediately. If they contain private data and were pushed publicly, rewrite Git history and rotate any exposed credentials.

## Dependency And Model Security

The semantic pipeline may use local ML dependencies and embedding models. Treat downloaded model caches as generated artifacts, not source code.

Recommended practices:

- Keep dependencies updated.
- Review changes to `pyproject.toml` and `uv.lock`.
- Do not commit downloaded model files.
- Be careful when enabling future LLM integrations, because sending URLs or page metadata to an external provider may expose private browsing context.

## Responsible Use

Do not use this project to collect another person's browsing history without clear permission.

Do not publish generated vaults or DuckDB databases without reviewing and removing private information.

Do not include real personal browsing data in bug reports, pull requests, documentation examples, tests, or screenshots.

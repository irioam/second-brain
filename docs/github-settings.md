# Recommended GitHub Settings

Use these settings before making the repository public.

## Branch Protection

Protect the `main` branch:

- Require a pull request before merging.
- Require status checks to pass before merging.
- Require the `CI` workflow to pass.
- Block force pushes.
- Block branch deletion.
- Require conversation resolution before merging.

Recommended but optional:

- Require linear history.
- Require approvals for external contributors.

## Security Features

Enable:

- Dependabot alerts.
- Dependabot security updates.
- Secret scanning.
- Push protection.
- Private vulnerability reporting, if available.

## Repository Hygiene

Confirm these paths are ignored and not tracked:

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

## Issue And Pull Request Flow

Use the templates in `.github/`:

- Bug report
- Feature request
- Pull request template

Close or edit issues that include private browser history, credentials, private URLs, or real DuckDB files.

## Public Repository Warning

This project handles sensitive local data. Public contributors should never be asked to upload real browsing history, local databases, generated vaults, screenshots with private URLs, tokens, or `.env` files.

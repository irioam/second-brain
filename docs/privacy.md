# Privacy

Second Brain processes browser history. Browser history can be sensitive.

It may reveal:

- Topics you study.
- Work projects.
- Internal systems.
- Client names.
- Personal interests.
- Health, finance, or legal research.
- Account names or private URLs.

Use this project as a local personal tool and review generated files before sharing anything.

## What Data Is Read

Second Brain reads local browser history from supported browsers:

- Chrome
- Edge
- Firefox

The extracted data includes fields such as:

- URL
- Page title
- Domain
- Visit count
- Last visit timestamp
- Browser name

## Where Data Is Stored

By default, consolidated data is stored locally in:

```text
data/second_brain.duckdb
```

Generated Obsidian notes are written to the vault path configured by the user.

Semantic features may create local embedding and cluster tables inside the same DuckDB database.

## What Is Not Intended To Happen

Second Brain should not intentionally:

- Upload browser history.
- Upload DuckDB databases.
- Upload generated Obsidian notes.
- Upload embeddings or clusters.
- Commit generated data to Git.
- Overwrite existing Markdown notes.

## External Services

The current semantic pipeline may use local ML dependencies and downloaded embedding models.

Future LLM integrations must be reviewed carefully. Sending URLs, titles, domains, or summaries to an external LLM provider may expose private browsing context.

If an external provider is ever enabled, it must be documented clearly and remain opt-in.

## Files You Should Not Share

Do not publish or attach:

```text
data/
.cache/
*.duckdb
*.db
*.sqlite
*.sqlite3
.env
.env.*
```

Also avoid screenshots that show private URLs, internal tools, account names, or personal research.

## Safe Example Data

Use fake URLs in examples, issues, tests, and pull requests:

```text
https://example.com/docs
https://example.org/article
https://github.com/example/repo
```

## If You Accidentally Share Private Data

If private data is committed locally:

1. Remove it from the Git index.
2. Add or confirm `.gitignore` rules.
3. Rewrite Git history if the data was committed.

If private data was pushed publicly:

1. Rewrite Git history.
2. Force push carefully.
3. Rotate any exposed credentials.
4. Assume the data may already have been copied.

Git history cleanup reduces exposure, but it cannot guarantee that already-published data was never downloaded.

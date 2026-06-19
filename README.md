# Second Brain for Obsidian

This project helps you turn your browsing history into a second brain that can be accessed through Obsidian.

It turns links you visited into a local, searchable memory: URLs, titles, domains, visit dates, and visit counts become a DuckDB database and Markdown notes.

It does four main things:

1. Reads the local history from Chrome, Edge, and Firefox.
2. Saves the data in a DuckDB database at `data/second_brain.duckdb`.
3. Generates Markdown files that can be opened in Obsidian.
4. Optionally creates semantic topic clusters.

The `extract` command is incremental. This means it does not delete the database when the browser has no history. If you clear your browser history, the old data already saved in DuckDB remains preserved.

## Why Use It?

This project is useful if you research a lot and later lose important links along the way.

In practice, it helps you:

- Find pages you already visited.
- Preserve references even after clearing your browser history.
- Understand which topics you researched over time.
- Build a personal knowledge base for study, work, and research.
- Keep your data on your own computer.

Brutally honest: this project is not for everyone. If you only browse casually, your browser history may already be enough. It makes more sense for students, developers, researchers, writers, analysts, and people who use Obsidian as a knowledge base.

## What It Does Not Do Yet

Today, the project organizes browsing history and creates structured notes, but it does not yet capture or automatically summarize the full content of web pages.

The generated notes are a starting point. They help you find, classify, and review links, but the final curation is still yours.

## Before You Start

You need:

- Windows.
- PowerShell.
- Python 3.11 or newer.
- `uv`, which installs and runs the project.
- Obsidian, if you want to open the generated notes as a vault.

To open PowerShell:

1. Press the Windows key.
2. Type `PowerShell`.
3. Open the `PowerShell` app.

Then go to the project folder:

```powershell
cd C:\Users\<your_user>\Documents\second_brain\second_brain
```

## Step-By-Step Installation

### 1. Check If Python Exists

In PowerShell, run:

```powershell
python --version
```

If you see something like `Python 3.11.9`, you are good to go.

### 2. Install `uv`, If You Do Not Have It Yet

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then close and reopen PowerShell.

### 3. Install The Project Dependencies

Inside the project folder, run:

```powershell
uv sync
```

This command downloads everything the project needs to work.

### 4. Test If The CLI Responds

```powershell
uv run second-brain --help
```

If a list of commands appears, the installation worked.

## Main Commands

### `extract`

Reads browser history and syncs the DuckDB database.

```powershell
uv run second-brain extract
```

Use this command when you want to update the database with new visits.

### `build-vault --dry-run`

Simulates creating the Obsidian notes without writing files.

```powershell
uv run second-brain build-vault --dry-run
```

Use this command to test safely.

### `build-vault`

Generates Markdown notes in the Obsidian vault.

```powershell
uv run second-brain build-vault
```

If you want to choose the vault path:

```powershell
uv run second-brain build-vault --vault-path "C:\obsidian\my_vault\second_brain"
```

### `all`

Runs two steps in sequence:

1. Runs `extract`.
2. Runs `build-vault`.

```powershell
uv run second-brain all
```

With a vault path:

```powershell
uv run second-brain all --vault-path "C:\obsidian\my_vault\second_brain"
```

To simulate without writing files:

```powershell
uv run second-brain all --dry-run
```

### `build-semantic --dry-run`

Simulates semantic clustering.

```powershell
uv run second-brain build-semantic --dry-run
```

### `build-semantic`

Creates topic aggregators in `03 - Aggregators`.

```powershell
uv run second-brain build-semantic
```

On the first run, this command may take longer because it may load or download embedding models.

## Ready-To-Use Recipes

### Safe First Run

Use these commands to test without creating notes yet:

```powershell
uv run second-brain extract
uv run second-brain build-vault --dry-run
```

### Full Run

```powershell
uv run second-brain all
```

### Full Run With Vault Path

```powershell
uv run second-brain all --vault-path "C:\obsidian\my_vault\second_brain"
```

### Run Tests

```powershell
uv run pytest
```

## Useful CLI Options

| Option | What It Does |
|---|---|
| `--db-path` | Changes the DuckDB database path. |
| `--vault-path` | Changes the Obsidian vault path. |
| `--dry-run` | Shows what would happen without writing files. |
| `--limit` | Limits the number of notes or sources processed. |
| `--min-visit-count` | Uses only URLs with a minimum number of visits. |
| `--n-clusters` | Defines how many semantic groups will be created. |
| `--embedding-model` | Chooses the model used for embeddings. |
| `--llm-provider` | Chooses a provider for labels/summaries. The default is `none`. |

## Where Files Are Stored

The main database is stored here:

```text
data/second_brain.duckdb
```

The Obsidian notes follow a structure similar to this:

```text
00 - Index/
01 - Sources/
02 - Topics/
03 - Daily/
03 - Aggregators/
99 - Attachments/
```

The full example is available in `vault_structure_sample.md`.

## Important Notes

- Your data stays local on your computer.
- Avoid publishing the DuckDB database or generated notes before reviewing them.
- Chrome, Edge, and Firefox store history in SQLite databases.
- This project reads that data and consolidates everything into DuckDB.
- Clearing your browser history does not automatically delete the DuckDB data.
- Existing Markdown files in Obsidian are not overwritten.
- Use `--dry-run` when you want to test without creating files.

## Detailed Documentation

For technical details, read:

- [CLI Reference](docs/cli-reference.md)
- [Internal Pipeline](docs/pipeline-overview.md)
- [Incremental Upsert Plan](.plans/incremental-history-upsert-plan.md)

## Project Structure

```text
second_brain/
  cli.py
  extraction.py
  database.py
  vault.py
  semantic.py
  templates.py
README.md
docs/
  cli-reference.md
  pipeline-overview.md
  incremental-history-upsert-plan.md
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full license text.

You may use, modify, and distribute this project as long as you keep credit to the original author.

Copyright (c) 2026 Irio Andre Moesch.

GitHub: [https://github.com/irioam](https://github.com/irioam)

# Roadmap

This roadmap is intentionally practical. Second Brain should become more useful without compromising privacy.

## Near Term

- Keep extraction incremental and safe.
- Improve documentation for first-time users.
- Add more tests around DuckDB migrations and vault generation.
- Add CI checks for pull requests.
- Keep generated data, cache, and local databases out of Git.

## Cross-Platform

- Linux support: detect browser profiles under `~/.config`, `~/.mozilla`, etc.
- macOS support: detect browser profiles under `~/Library/Application Support`.
- Use platform-agnostic path resolution instead of hardcoded Windows paths.
- Run CI tests on Linux and macOS in addition to Windows.

## High-Value Features

- Better noise filtering for low-value browser history entries.
- Better source classification beyond Docs, Articles, Videos, and Repos.
- A search command for finding previously visited sources.
- Optional page-content capture with strong privacy controls.
- Optional local summaries for generated source notes.
- Better semantic cluster labels without exposing private data.

## Possible CLI Improvements

- `second-brain search`
- `second-brain stats`
- `second-brain doctor`
- `second-brain clean-cache`
- `second-brain migrate`

## Privacy Requirements For Future Work

Any feature that sends data outside the machine must be:

- Opt-in.
- Documented.
- Easy to disable.
- Clear about what data leaves the computer.

Browser history, generated notes, embeddings, and DuckDB files must remain local by default.

## Not A Priority Yet

- Multi-user collaboration.
- Cloud sync.
- Hosted dashboards.
- Browser extensions.
- Automatic publishing.

These may be useful later, but they increase privacy and maintenance risk.

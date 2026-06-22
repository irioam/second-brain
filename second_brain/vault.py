"""Obsidian vault generation from the consolidated DuckDB history table."""

from collections import defaultdict
from pathlib import Path

from .config import DEFAULT_DB_PATH, VAULT_DIRECTORIES, resolve_default_vault_path
from .database import load_source_notes
from .models import SourceNote
from .templates import (
    render_category_note,
    render_daily_note,
    render_moc,
    render_source_note,
)


def safe_write(path: Path, content: str, dry_run: bool) -> str:
    """Write a file only if it does not already exist."""
    if path.exists():
        return "skipped"
    if dry_run:
        return "planned"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def ensure_vault_directories(vault_path: Path, dry_run: bool) -> None:
    """Create the expected Obsidian vault directory structure."""
    if dry_run:
        return
    for directory in VAULT_DIRECTORIES:
        (vault_path / directory).mkdir(parents=True, exist_ok=True)


def build_vault(
    db_path: Path = DEFAULT_DB_PATH,
    vault_path: Path | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    min_visit_count: int | None = None,
) -> None:
    """Build source notes, daily notes, and the MOC from the DuckDB history table."""
    vault_path = vault_path or resolve_default_vault_path()
    notes = load_source_notes(db_path, limit=limit, min_visit_count=min_visit_count)
    ensure_vault_directories(vault_path, dry_run=dry_run)

    counters = defaultdict(int)
    for note in notes:
        status = safe_write(
            vault_path / note.path, render_source_note(note), dry_run=dry_run
        )
        counters[f"source_{status}"] += 1

    notes_by_day: dict[str, list[SourceNote]] = defaultdict(list)
    for note in notes:
        notes_by_day[note.visited].append(note)

    sorted_days = sorted(notes_by_day)
    previous_by_day = {
        day: sorted_days[index - 1] if index > 0 else None
        for index, day in enumerate(sorted_days)
    }
    next_by_day = {
        day: sorted_days[index + 1] if index < len(sorted_days) - 1 else None
        for index, day in enumerate(sorted_days)
    }

    for visited, daily_notes in notes_by_day.items():
        daily_path = vault_path / "03 - Daily" / f"{visited}.md"
        status = safe_write(
            daily_path,
            render_daily_note(
                visited,
                daily_notes,
                previous_day=previous_by_day[visited],
                next_day=next_by_day[visited],
            ),
            dry_run=dry_run,
        )
        counters[f"daily_{status}"] += 1

    notes_by_type: dict[str, list[SourceNote]] = defaultdict(list)
    for note in notes:
        notes_by_type[note.source_type].append(note)

    for source_type, typed_notes in notes_by_type.items():
        category_path = vault_path / "01 - Sources" / f"{source_type}.md"
        status = safe_write(
            category_path,
            render_category_note(source_type, typed_notes),
            dry_run=dry_run,
        )
        counters[f"category_{status}"] += 1

    moc_status = safe_write(
        vault_path / "00 - Index" / "MOC.md", render_moc(notes), dry_run=dry_run
    )
    counters[f"moc_{moc_status}"] += 1

    mode = "DRY-RUN" if dry_run else "WRITE"
    print(f"[{mode}] Cofre: {vault_path}")
    print(f"Fontes carregadas: {len(notes)}")
    for key in sorted(counters):
        print(f"{key}: {counters[key]}")

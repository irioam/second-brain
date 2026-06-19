"""Shared data models used by extraction, persistence, and vault generation."""

from dataclasses import dataclass
from pathlib import Path

HistoryRow = tuple[str, str, int, int, str, str, str, str, str | None]


@dataclass(frozen=True)
class SourceNote:
    """Represents one deduplicated source note to be written to the vault."""

    url: str
    title: str
    visit_count: int
    domain: str
    visited: str
    timestamp: str
    browser: str
    source_type: str
    path: Path

    @property
    def obsidian_link(self) -> str:
        """Return an Obsidian wikilink pointing to this source note."""
        note_path = self.path.with_suffix("").as_posix()
        return f"[[{note_path}|{self.title}]]"


@dataclass(frozen=True)
class SemanticSourceRecord:
    """Record used to compute semantic embeddings and clusters."""

    url_norm: str
    url: str
    title: str
    domain: str
    visit_count: int
    source_type: str
    path: Path


@dataclass(frozen=True)
class ClusterItem:
    """One source note assignment inside a semantic cluster."""

    cluster_id: int
    url_norm: str
    title: str
    domain: str
    visit_count: int
    source_type: str
    path: Path

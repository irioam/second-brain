from pathlib import Path

from second_brain.models import SourceNote
from second_brain.templates import render_daily_note, render_source_note


def source_note(
    title: str,
    domain: str,
    visit_count: int,
    filename: str,
    *,
    visited: str = "2026-06-21",
) -> SourceNote:
    return SourceNote(
        url=f"https://{domain}/{filename}",
        title=title,
        visit_count=visit_count,
        domain=domain,
        visited=visited,
        timestamp=f"{visited} 10:00:00",
        browser="edge",
        source_type="Articles",
        path=Path("01 - Sources") / "Articles" / f"{filename}.md",
    )


def test_render_source_note_includes_daily_note_frontmatter():
    note = source_note("Google Tradutor", "translate.google.com.br", 28, "tradutor")

    content = render_source_note(note)

    assert 'daily_note: "[[03 - Daily/2026-06-21|2026-06-21]]"' in content
    assert "visited: 2026-06-21" in content
    assert "visit_count: 28" in content


def test_render_daily_note_groups_by_domain_and_title_with_neighbor_links():
    notes = [
        source_note("Google Tradutor", "translate.google.com.br", 28, "tradutor-1"),
        source_note("Google Tradutor", "translate.google.com.br", 8, "tradutor-2"),
        source_note("(21111) YouTube", "www.youtube.com", 22, "youtube-1"),
    ]

    content = render_daily_note(
        "2026-06-21",
        notes,
        previous_day="2026-06-20",
        next_day="2026-06-22",
    )

    assert "[[03 - Daily/2026-06-20|Dia anterior]]" in content
    assert "[[03 - Daily/2026-06-22|Proximo dia]]" in content
    assert (
        "- Google Tradutor - translate.google.com.br (2 fontes, 36 visitas)" in content
    )
    assert (
        "  - [[01 - Sources/Articles/tradutor-1|Google Tradutor]] (28 visitas)"
        in content
    )
    assert (
        "  - [[01 - Sources/Articles/tradutor-2|Google Tradutor]] (8 visitas)"
        in content
    )
    assert "- (21111) YouTube - www.youtube.com (1 fontes, 22 visitas)" in content


def test_render_daily_note_handles_missing_neighbor_links():
    note = source_note("Power BI", "app.powerbi.com", 6, "power-bi")

    content = render_daily_note("2026-06-21", [note])

    assert "Dia anterior: - | Proximo dia: -" in content
    assert "- Power BI - app.powerbi.com (1 fontes, 6 visitas)" in content

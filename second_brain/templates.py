"""Markdown renderers for the generated Obsidian vault."""

from collections import defaultdict
from typing import Iterable

from slugify import slugify

from .models import ClusterItem, SourceNote


def yaml_quote(value: str) -> str:
    """Quote a string for simple YAML frontmatter fields."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_source_note(note: SourceNote) -> str:
    """Render one source note as Markdown with Obsidian-friendly frontmatter."""
    tag_domain = slugify(note.domain).replace("-", "_")
    return f"""---
title: {yaml_quote(note.title)}
url: {yaml_quote(note.url)}
domain: {yaml_quote(note.domain)}
visited: {note.visited}
visit_count: {note.visit_count}
browser: {yaml_quote(note.browser)}
source_type: {yaml_quote(note.source_type)}
tags:
  - web-clip
  - source/{note.source_type.lower()}
  - domain/{tag_domain}
---

# {note.title}

Fonte: [{note.domain}]({note.url})
Ultima visita: {note.timestamp}
Visitas registradas: {note.visit_count}
Navegador: {note.browser}

## Resumo

> Preencher manualmente ou via enriquecimento futuro.

## Topicos relacionados

- 

## Notas pessoais

- 
"""


def render_daily_note(visited: str, notes: Iterable[SourceNote]) -> str:
    """Render one daily index note linking to all source notes visited that day."""
    sorted_notes = sorted(notes, key=lambda item: (-item.visit_count, item.title.lower()))
    lines = [
        "---",
        f"date: {visited}",
        "tags:",
        "  - daily",
        "  - second-brain",
        "---",
        "",
        f"# {visited}",
        "",
        "## Fontes visitadas",
        "",
    ]
    lines.extend(f"- {note.obsidian_link} - {note.domain} ({note.visit_count} visitas)" for note in sorted_notes)
    lines.extend(["", "## Notas do dia", "", "- "])
    return "\n".join(lines) + "\n"


def render_category_note(source_type: str, notes: Iterable[SourceNote]) -> str:
    """Render one category index note for the source section."""
    sorted_notes = sorted(notes, key=lambda item: (-item.visit_count, item.title.lower()))
    lines = [
        "---",
        "tags:",
        "  - index",
        "  - second-brain",
        f"  - source/{source_type.lower()}",
        "---",
        "",
        f"# {source_type}",
        "",
        "## Fontes",
        "",
    ]
    lines.extend(f"- {note.obsidian_link} - {note.domain} ({note.visit_count} visitas)" for note in sorted_notes)
    return "\n".join(lines) + "\n"


def render_moc(notes: list[SourceNote]) -> str:
    """Render the main map of content for the generated vault."""
    by_type: dict[str, int] = defaultdict(int)
    by_day: dict[str, int] = defaultdict(int)
    for note in notes:
        by_type[note.source_type] += 1
        by_day[note.visited] += 1

    latest_days = sorted(by_day.keys(), reverse=True)[:10]
    lines = [
        "---",
        "tags:",
        "  - moc",
        "  - second-brain",
        "---",
        "",
        "# MOC",
        "",
        "## Areas",
        "",
        "- [[01 - Sources/Docs|Docs]]",
        "- [[01 - Sources/Articles|Articles]]",
        "- [[01 - Sources/Videos|Videos]]",
        "- [[01 - Sources/Repos|Repos]]",
        "- [[03 - Daily|Daily]]",
        "- [[03 - Aggregators/Clusters Index|Semantic Clusters]]",
        "- [[03 - Aggregators/By Domain|By Domain]]",
        "",
        "## Totais por tipo",
        "",
    ]
    lines.extend(f"- {source_type}: {count}" for source_type, count in sorted(by_type.items()))
    lines.extend(["", "## Dias recentes", ""])
    lines.extend(f"- [[03 - Daily/{day}|{day}]] ({by_day[day]} fontes)" for day in latest_days)
    return "\n".join(lines) + "\n"


def render_cluster_note(cluster_id: int, label: str, summary: str, items: Iterable[ClusterItem]) -> str:
    """Render one semantic cluster note."""
    sorted_items = sorted(items, key=lambda item: (-item.visit_count, item.title.lower()))
    lines = [
        "---",
        "tags:",
        "  - index",
        "  - semantic-cluster",
        f"  - cluster/{cluster_id:03d}",
        "---",
        "",
        f"# Cluster {cluster_id:03d}: {label}",
        "",
        "## Resumo",
        "",
        summary or "> Resumo semantico nao gerado para este cluster.",
        "",
        "## Fontes",
        "",
    ]
    lines.extend(
        f"- [[{item.path.with_suffix('').as_posix()}|{item.title}]] - {item.domain} ({item.visit_count} visitas)"
        for item in sorted_items
    )
    return "\n".join(lines) + "\n"


def render_clusters_index(clusters: dict[int, dict[str, object]]) -> str:
    """Render index note with all semantic clusters."""
    lines = [
        "---",
        "tags:",
        "  - index",
        "  - semantic",
        "---",
        "",
        "# Semantic Clusters",
        "",
        "## Clusters",
        "",
    ]
    for cluster_id in sorted(clusters):
        label = str(clusters[cluster_id].get("label", f"Cluster {cluster_id:03d}"))
        size = int(clusters[cluster_id].get("size", 0))
        lines.append(f"- [[03 - Aggregators/Clusters/Cluster-{cluster_id:03d}|Cluster {cluster_id:03d}: {label}]] ({size} fontes)")
    return "\n".join(lines) + "\n"


def render_aggregator_by_domain(clusters: dict[int, list[ClusterItem]]) -> str:
    """Render domain-centric semantic aggregation note."""
    by_domain: dict[str, list[int]] = defaultdict(list)
    for cluster_id, items in clusters.items():
        for item in items:
            if cluster_id not in by_domain[item.domain]:
                by_domain[item.domain].append(cluster_id)

    lines = [
        "---",
        "tags:",
        "  - index",
        "  - semantic",
        "  - domain",
        "---",
        "",
        "# By Domain",
        "",
        "## Dominios",
        "",
    ]
    for domain, cluster_ids in sorted(by_domain.items(), key=lambda kv: kv[0].lower()):
        links = ", ".join(f"[[03 - Aggregators/Clusters/Cluster-{cluster_id:03d}|C{cluster_id:03d}]]" for cluster_id in sorted(cluster_ids))
        lines.append(f"- {domain}: {links}")
    return "\n".join(lines) + "\n"

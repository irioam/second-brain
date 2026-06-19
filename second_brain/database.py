"""DuckDB persistence and read models for navigation history."""

import hashlib
import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import duckdb
from slugify import slugify

from .classification import classify_source
from .config import DEFAULT_DB_PATH
from .models import ClusterItem, HistoryRow, SemanticSourceRecord, SourceNote


def make_history_key(browser_name: str | None, url: str) -> str:
    """Build a stable key for one browser-history record."""
    browser = browser_name or "unknown"
    return f"{browser}:{normalize_url(url)}"


def _history_table_exists(connection: duckdb.DuckDBPyConnection) -> bool:
    result = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'historico'
        """,
    ).fetchone()
    return bool(result and result[0])


def _history_columns(connection: duckdb.DuckDBPyConnection) -> set[str]:
    if not _history_table_exists(connection):
        return set()
    return {
        row[1]
        for row in connection.execute("PRAGMA table_info('historico')").fetchall()
    }


def _create_history_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("""
        CREATE TABLE historico (
            history_key VARCHAR PRIMARY KEY,
            url VARCHAR,
            title VARCHAR,
            visit_count INTEGER,
            last_visit_time BIGINT,
            domain VARCHAR,
            date_last_visit DATE,
            hour_last_visit TIME,
            timestamp_last_visit TIMESTAMP,
            navegador VARCHAR,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def _add_missing_history_metadata(
    connection: duckdb.DuckDBPyConnection, columns: set[str]
) -> None:
    if "first_seen_at" not in columns:
        connection.execute(
            "ALTER TABLE historico ADD COLUMN first_seen_at "
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
    if "last_seen_at" not in columns:
        connection.execute(
            "ALTER TABLE historico ADD COLUMN last_seen_at "
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
    if "updated_at" not in columns:
        connection.execute(
            "ALTER TABLE historico ADD COLUMN updated_at "
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )


def _migrate_legacy_history_table(connection: duckdb.DuckDBPyConnection) -> None:
    legacy_table = f"historico_legacy_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    legacy_rows = connection.execute(
        """
        SELECT url, title, visit_count, last_visit_time, domain,
               date_last_visit, hour_last_visit, timestamp_last_visit,
               navegador
        FROM historico
        ORDER BY COALESCE(visit_count, 0) DESC,
                 COALESCE(last_visit_time, 0) DESC
        """,
    ).fetchall()
    deduplicated_rows: dict[str, HistoryRow] = {}
    for row in legacy_rows:
        url, _, visit_count, last_visit_time, _, _, _, _, browser_name = row
        history_key = make_history_key(browser_name, url)
        current = deduplicated_rows.get(history_key)
        if current is None:
            deduplicated_rows[history_key] = row
            continue

        current_visit_count = int(current[2] or 0)
        current_last_visit_time = int(current[3] or 0)
        row_visit_count = int(visit_count or 0)
        row_last_visit_time = int(last_visit_time or 0)
        if (row_visit_count, row_last_visit_time) > (
            current_visit_count,
            current_last_visit_time,
        ):
            deduplicated_rows[history_key] = row

    connection.execute(f"ALTER TABLE historico RENAME TO {legacy_table}")
    _create_history_table(connection)
    upsert_history_rows(connection, list(deduplicated_rows.values()))
    connection.execute(f"DROP TABLE {legacy_table}")


def ensure_history_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Create or migrate the history table without deleting preserved history."""
    if not _history_table_exists(connection):
        _create_history_table(connection)
        connection.commit()
        return

    columns = _history_columns(connection)
    if "history_key" not in columns:
        _migrate_legacy_history_table(connection)
    else:
        _add_missing_history_metadata(connection, columns)
    connection.commit()


def upsert_history_rows(
    connection: duckdb.DuckDBPyConnection, rows: list[HistoryRow]
) -> None:
    """Insert new history rows and update changed rows without deleting missing rows."""
    if not rows:
        return

    for row in rows:
        (
            url,
            title,
            visit_count,
            last_visit_time,
            domain,
            date_last_visit,
            hour_last_visit,
            timestamp_last_visit,
            browser_name,
        ) = row
        history_key = make_history_key(browser_name, url)
        existing = connection.execute(
            """
            SELECT visit_count, last_visit_time
            FROM historico
            WHERE history_key = ?
            """,
            [history_key],
        ).fetchone()

        if existing is None:
            connection.execute(
                """
                INSERT INTO historico (
                    history_key, url, title, visit_count, last_visit_time, domain,
                    date_last_visit, hour_last_visit, timestamp_last_visit, navegador,
                    first_seen_at, last_seen_at, updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                [
                    history_key,
                    url,
                    title,
                    visit_count,
                    last_visit_time,
                    domain,
                    date_last_visit,
                    hour_last_visit,
                    timestamp_last_visit,
                    browser_name,
                ],
            )
            continue

        existing_visit_count = int(existing[0] or 0)
        existing_last_visit_time = int(existing[1] or 0)
        should_update = (
            last_visit_time > existing_last_visit_time
            or visit_count > existing_visit_count
        )
        if should_update:
            connection.execute(
                """
                UPDATE historico
                SET
                    url = ?,
                    title = ?,
                    visit_count = ?,
                    last_visit_time = ?,
                    domain = ?,
                    date_last_visit = ?,
                    hour_last_visit = ?,
                    timestamp_last_visit = ?,
                    navegador = ?,
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE history_key = ?
                """,
                [
                    url,
                    title,
                    visit_count,
                    last_visit_time,
                    domain,
                    date_last_visit,
                    hour_last_visit,
                    timestamp_last_visit,
                    browser_name,
                    history_key,
                ],
            )
        else:
            connection.execute(
                "UPDATE historico SET last_seen_at = CURRENT_TIMESTAMP "
                "WHERE history_key = ?",
                [history_key],
            )


def insert_history_rows(
    connection: duckdb.DuckDBPyConnection, rows: list[HistoryRow]
) -> None:
    """Compatibility wrapper for the incremental upsert implementation."""
    upsert_history_rows(connection, rows)


def sync_history_database(
    browser_histories: list[tuple[str, str]], db_path: Path = DEFAULT_DB_PATH
) -> int:
    """Extract all browser histories and incrementally sync the DuckDB history table."""
    from .extraction import extract_history_to_rows

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(db_path))
    ensure_history_table(connection)

    total_rows = 0
    for path, browser_name in browser_histories:
        rows = extract_history_to_rows(path, browser_name=browser_name)
        if rows:
            upsert_history_rows(connection, rows)
            total_rows += len(rows)
            print(f"Sincronizados {len(rows)} registros de {browser_name}")

    connection.commit()
    connection.close()
    print(
        f"Histórico sincronizado em {db_path} com {total_rows} "
        "registros lidos nesta execução."
    )
    return total_rows


def create_history_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Compatibility wrapper that now preserves existing history."""
    ensure_history_table(connection)


def rebuild_history_database(
    browser_histories: list[tuple[str, str]], db_path: Path = DEFAULT_DB_PATH
) -> int:
    """Compatibility wrapper for the incremental sync implementation."""
    return sync_history_database(browser_histories, db_path=db_path)


def normalize_url(url: str) -> str:
    """Normalize URL enough to deduplicate browser-history rows safely."""
    parsed_url = urlparse(url.strip())
    normalized_netloc = parsed_url.netloc.lower()
    normalized_path = parsed_url.path.rstrip("/") or parsed_url.path
    return urlunparse(
        (
            parsed_url.scheme.lower(),
            normalized_netloc,
            normalized_path,
            "",
            parsed_url.query,
            "",
        )
    )


def source_filename(title: str, visited: str, url: str) -> str:
    """Create a stable, readable, collision-resistant Markdown filename."""
    title_slug = slugify(title or "sem-titulo")[:70] or "sem-titulo"
    url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{visited} - {title_slug} - {url_hash}.md"


def load_source_notes(
    db_path: Path, limit: int | None, min_visit_count: int | None
) -> list[SourceNote]:
    """Load and deduplicate history rows from DuckDB as source-note records."""
    if not db_path.exists():
        raise FileNotFoundError(f"Banco DuckDB nao encontrado: {db_path}")

    query = """
        SELECT
            url,
            title,
            visit_count,
            domain,
            CAST(date_last_visit AS VARCHAR) AS visited,
            CAST(timestamp_last_visit AS VARCHAR) AS timestamp,
            navegador AS browser
        FROM historico
    """
    params: list[int] = []
    if min_visit_count is not None:
        query += "\nWHERE visit_count >= ?"
        params.append(min_visit_count)
    query += "\nORDER BY url, visit_count DESC, timestamp_last_visit DESC"

    with duckdb.connect(str(db_path), read_only=True) as connection:
        rows = connection.execute(query, params).fetchall()

    deduplicated: dict[str, SourceNote] = {}
    for url, title, visit_count, domain, visited, timestamp, browser in rows:
        normalized_url = normalize_url(url)
        if normalized_url in deduplicated:
            continue

        note_title = title or url
        source_type = classify_source(url, domain or "")
        relative_path = (
            Path("01 - Sources")
            / source_type
            / source_filename(note_title, visited, normalized_url)
        )
        deduplicated[normalized_url] = SourceNote(
            url=url,
            title=note_title,
            visit_count=int(visit_count or 0),
            domain=domain or urlparse(url).netloc,
            visited=visited,
            timestamp=timestamp,
            browser=browser or "unknown",
            source_type=source_type,
            path=relative_path,
        )

        if limit and len(deduplicated) >= limit:
            break

    return list(deduplicated.values())


def create_semantic_tables(connection: duckdb.DuckDBPyConnection) -> None:
    """Create semantic tables used by embedding and clustering pipelines."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS source_embeddings (
            url_norm VARCHAR PRIMARY KEY,
            title VARCHAR,
            domain VARCHAR,
            model_name VARCHAR,
            embedding_json VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS source_clusters (
            run_id VARCHAR,
            url_norm VARCHAR,
            cluster_id INTEGER,
            distance_to_centroid DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS cluster_metadata (
            run_id VARCHAR,
            cluster_id INTEGER,
            label VARCHAR,
            summary VARCHAR,
            top_terms VARCHAR,
            size INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()


def load_semantic_sources(
    db_path: Path, min_visit_count: int | None, limit: int | None = None
) -> list[SemanticSourceRecord]:
    """Load deduplicated records used as input to semantic clustering."""
    notes = load_source_notes(
        db_path=db_path, limit=limit, min_visit_count=min_visit_count
    )
    records: list[SemanticSourceRecord] = []
    for note in notes:
        url_norm = normalize_url(note.url)
        records.append(
            SemanticSourceRecord(
                url_norm=url_norm,
                url=note.url,
                title=note.title,
                domain=note.domain,
                visit_count=note.visit_count,
                source_type=note.source_type,
                path=note.path,
            )
        )
    return records


def load_existing_embeddings(
    connection: duckdb.DuckDBPyConnection, model_name: str
) -> dict[str, list[float]]:
    """Load already computed embeddings by normalized URL."""
    rows = connection.execute(
        """
        SELECT url_norm, embedding_json
        FROM source_embeddings
        WHERE model_name = ?
        """,
        [model_name],
    ).fetchall()
    return {url_norm: json.loads(embedding_json) for url_norm, embedding_json in rows}


def upsert_embeddings(
    connection: duckdb.DuckDBPyConnection,
    rows: Iterable[tuple[str, str, str, str, list[float]]],
) -> None:
    """Insert or update semantic embeddings."""
    payload = [
        (
            url_norm,
            title,
            domain,
            model_name,
            json.dumps(embedding, ensure_ascii=True),
        )
        for url_norm, title, domain, model_name, embedding in rows
    ]
    if not payload:
        return
    connection.executemany(
        """
        INSERT OR REPLACE INTO source_embeddings
            (url_norm, title, domain, model_name, embedding_json, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        payload,
    )
    connection.commit()


def replace_cluster_run(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    assignments: Iterable[tuple[str, int, float]],
    metadata: Iterable[tuple[int, str, str, list[str], int]],
) -> None:
    """Replace one clustering run with cluster assignments and metadata."""
    connection.execute("DELETE FROM source_clusters WHERE run_id = ?", [run_id])
    connection.execute("DELETE FROM cluster_metadata WHERE run_id = ?", [run_id])
    assignment_rows = [
        (run_id, url_norm, cluster_id, distance)
        for url_norm, cluster_id, distance in assignments
    ]
    if assignment_rows:
        connection.executemany(
            """
            INSERT INTO source_clusters
                (run_id, url_norm, cluster_id, distance_to_centroid, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            assignment_rows,
        )
    metadata_rows = [
        (
            run_id,
            cluster_id,
            label,
            summary,
            json.dumps(top_terms, ensure_ascii=True),
            size,
        )
        for cluster_id, label, summary, top_terms, size in metadata
    ]
    if metadata_rows:
        connection.executemany(
            """
            INSERT INTO cluster_metadata
                (run_id, cluster_id, label, summary, top_terms, size, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            metadata_rows,
        )
    connection.commit()


def load_cluster_items(db_path: Path, run_id: str) -> dict[int, list[ClusterItem]]:
    """Load clustered items grouped by cluster ID for vault rendering."""
    query = """
        SELECT
            sc.cluster_id,
            sc.url_norm,
            se.title,
            se.domain,
            COALESCE(h.visit_count, 0) AS visit_count,
            CASE
                WHEN lower(h.domain) LIKE '%youtube.com%'
                    OR lower(h.domain) LIKE '%youtu.be%'
                    OR lower(h.domain) LIKE '%vimeo.com%' THEN 'Videos'
                WHEN lower(h.domain) LIKE '%github.com%'
                    OR lower(h.domain) LIKE '%gitlab.com%'
                    OR lower(h.domain) LIKE '%bitbucket.org%' THEN 'Repos'
                WHEN lower(h.url) LIKE '%/docs%'
                    OR lower(h.url) LIKE '%docs.%'
                    OR lower(h.url) LIKE '%documentation%'
                    OR lower(h.url) LIKE '%/learn%'
                    OR lower(h.url) LIKE '%developer.%' THEN 'Docs'
                ELSE 'Articles'
            END AS source_type,
            CAST(h.date_last_visit AS VARCHAR) AS visited
        FROM source_clusters sc
        JOIN source_embeddings se ON se.url_norm = sc.url_norm
        LEFT JOIN historico h ON h.url = (
            SELECT url
            FROM historico h2
            WHERE lower(h2.url) LIKE '%' || sc.url_norm || '%'
            ORDER BY h2.visit_count DESC, h2.timestamp_last_visit DESC
            LIMIT 1
        )
        WHERE sc.run_id = ?
        ORDER BY sc.cluster_id, visit_count DESC, se.title
    """
    grouped: dict[int, list[ClusterItem]] = {}
    with duckdb.connect(str(db_path), read_only=True) as connection:
        rows = connection.execute(query, [run_id]).fetchall()
    for cluster_id, url_norm, title, domain, visit_count, source_type, visited in rows:
        visited_text = visited or "unknown-date"
        path = (
            Path("01 - Sources")
            / source_type
            / source_filename(title or "sem-titulo", visited_text, url_norm)
        )
        item = ClusterItem(
            cluster_id=int(cluster_id),
            url_norm=url_norm,
            title=title or "sem-titulo",
            domain=domain or "",
            visit_count=int(visit_count or 0),
            source_type=source_type,
            path=path,
        )
        grouped.setdefault(int(cluster_id), []).append(item)
    return grouped


def load_cluster_metadata(db_path: Path, run_id: str) -> dict[int, dict[str, object]]:
    """Load cluster metadata for one run."""
    with duckdb.connect(str(db_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT cluster_id, label, summary, top_terms, size
            FROM cluster_metadata
            WHERE run_id = ?
            ORDER BY cluster_id
            """,
            [run_id],
        ).fetchall()
    metadata: dict[int, dict[str, object]] = {}
    for cluster_id, label, summary, top_terms_json, size in rows:
        metadata[int(cluster_id)] = {
            "label": label or f"Cluster {cluster_id:03d}",
            "summary": summary or "",
            "top_terms": json.loads(top_terms_json or "[]"),
            "size": int(size or 0),
        }
    return metadata

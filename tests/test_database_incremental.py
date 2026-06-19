import duckdb

from second_brain.database import ensure_history_table, sync_history_database, upsert_history_rows


def history_row(
    url: str,
    *,
    title: str = "Example",
    visit_count: int = 3,
    last_visit_time: int = 100,
    browser_name: str = "chrome",
):
    return (
        url,
        title,
        visit_count,
        last_visit_time,
        "example.com",
        "2026-01-01",
        "10:00:00",
        "2026-01-01 10:00:00",
        browser_name,
    )


def fetch_history(connection):
    return connection.execute(
        """
        SELECT history_key, url, title, visit_count, last_visit_time, navegador
        FROM historico
        ORDER BY history_key
        """,
    ).fetchall()


def test_ensure_history_table_creates_incremental_schema(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        ensure_history_table(connection)
        columns = {row[1] for row in connection.execute("PRAGMA table_info('historico')").fetchall()}

    assert {
        "history_key",
        "url",
        "title",
        "visit_count",
        "last_visit_time",
        "first_seen_at",
        "last_seen_at",
        "updated_at",
    }.issubset(columns)


def test_ensure_history_table_adds_missing_metadata_columns(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            """
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
                navegador VARCHAR
            )
            """,
        )

        ensure_history_table(connection)
        columns = {row[1] for row in connection.execute("PRAGMA table_info('historico')").fetchall()}

    assert {"first_seen_at", "last_seen_at", "updated_at"}.issubset(columns)


def test_upsert_does_not_duplicate_existing_url(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        ensure_history_table(connection)
        upsert_history_rows(connection, [history_row("https://example.com/docs")])
        upsert_history_rows(connection, [history_row("https://example.com/docs")])

        rows = fetch_history(connection)

    assert len(rows) == 1
    assert rows[0][1] == "https://example.com/docs"


def test_upsert_updates_when_timestamp_is_newer(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        ensure_history_table(connection)
        upsert_history_rows(connection, [history_row("https://example.com/docs", title="Old", visit_count=5, last_visit_time=100)])
        upsert_history_rows(connection, [history_row("https://example.com/docs", title="New", visit_count=4, last_visit_time=200)])

        row = fetch_history(connection)[0]

    assert row[2] == "New"
    assert row[3] == 4
    assert row[4] == 200


def test_upsert_updates_when_visit_count_is_higher(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        ensure_history_table(connection)
        upsert_history_rows(connection, [history_row("https://example.com/docs", title="Old", visit_count=3, last_visit_time=200)])
        upsert_history_rows(connection, [history_row("https://example.com/docs", title="More Visits", visit_count=7, last_visit_time=150)])

        row = fetch_history(connection)[0]

    assert row[2] == "More Visits"
    assert row[3] == 7
    assert row[4] == 150


def test_empty_sync_preserves_existing_history(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        ensure_history_table(connection)
        upsert_history_rows(connection, [history_row("https://example.com/docs")])

    total_rows = sync_history_database([], db_path=db_path)

    with duckdb.connect(str(db_path)) as connection:
        rows = fetch_history(connection)

    assert total_rows == 0
    assert len(rows) == 1


def test_legacy_schema_is_migrated_and_deduplicated(tmp_path):
    db_path = tmp_path / "history.duckdb"
    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            """
            CREATE TABLE historico (
                url VARCHAR,
                title VARCHAR,
                visit_count INTEGER,
                last_visit_time BIGINT,
                domain VARCHAR,
                date_last_visit DATE,
                hour_last_visit TIME,
                timestamp_last_visit TIMESTAMP,
                navegador VARCHAR
            )
            """,
        )
        connection.executemany(
            """
            INSERT INTO historico (url, title, visit_count, last_visit_time, domain, date_last_visit, hour_last_visit, timestamp_last_visit, navegador)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                history_row("https://example.com/docs/", title="Lower", visit_count=3, last_visit_time=100),
                history_row("https://example.com/docs", title="Higher", visit_count=5, last_visit_time=90),
            ],
        )

        ensure_history_table(connection)
        rows = fetch_history(connection)

    assert len(rows) == 1
    assert rows[0][2] == "Higher"
    assert rows[0][3] == 5

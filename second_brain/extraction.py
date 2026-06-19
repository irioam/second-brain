"""Browser-history extraction for Chrome, Edge, and Firefox."""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from .models import HistoryRow


def chrome_time_to_dt(chrome_time: int) -> datetime:
    """Converte timestamp WebKit (Chrome/Edge) para `datetime`.

    Chrome e Edge armazenam datas como microsegundos desde 1601-01-01 00:00:00
    (epoch WebKit). Esta função normaliza esse valor para um objeto `datetime`
    Python no fuso local do processo.

    Args:
        chrome_time: Valor inteiro em microsegundos desde o epoch WebKit.

    Returns:
        `datetime` correspondente ao instante informado.
    """
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)


def firefox_time_to_dt(firefox_time: int) -> datetime:
    """Converte timestamp do Firefox para `datetime`.

    O campo `last_visit_date` do Firefox é armazenado em microsegundos desde
    1970-01-01 00:00:00 (Unix epoch). A função transforma esse valor em
    `datetime` Python.

    Args:
        firefox_time: Valor inteiro em microsegundos desde Unix epoch.

    Returns:
        `datetime` correspondente ao instante informado.
    """
    return datetime(1970, 1, 1) + timedelta(microseconds=firefox_time)


def format_visit_datetime(
    raw_timestamp: int, browser_name: str | None
) -> tuple[str, str, str]:
    """Formata timestamp bruto de visita em representações textuais padronizadas."""
    if browser_name and browser_name.startswith("firefox"):
        visit_dt = firefox_time_to_dt(raw_timestamp)
    else:
        visit_dt = chrome_time_to_dt(raw_timestamp)

    last_visit_date = visit_dt.date().isoformat()
    last_visit_hour = visit_dt.time().strftime("%H:%M:%S")
    last_visit_timestamp = visit_dt.strftime("%Y-%m-%d %H:%M:%S")
    return last_visit_date, last_visit_hour, last_visit_timestamp


def discover_browser_histories(
    user_profile: str | None = None,
) -> list[tuple[str, str]]:
    """Discover local browser-history databases for the supported browsers."""
    user_profile = user_profile or os.environ.get("USERPROFILE")
    if not user_profile:
        raise RuntimeError("Variável de ambiente USERPROFILE não encontrada.")

    chrome_history = os.path.join(
        user_profile, r"AppData\Local\Google\Chrome\User Data\Default\History"
    )
    edge_history = os.path.join(
        user_profile, r"AppData\Local\Microsoft\Edge\User Data\Default\History"
    )
    firefox_profiles_dir = os.path.join(
        user_profile, r"AppData\Roaming\Mozilla\Firefox\Profiles"
    )

    firefox_histories: list[tuple[str, str]] = []
    if os.path.exists(firefox_profiles_dir):
        for profile in os.listdir(firefox_profiles_dir):
            places_path = os.path.join(firefox_profiles_dir, profile, "places.sqlite")
            if os.path.exists(places_path):
                firefox_histories.append((places_path, f"firefox_{profile}"))
    else:
        print(f"Pasta de perfis do Firefox não encontrada: {firefox_profiles_dir}")

    return [
        (chrome_history, "chrome"),
        (edge_history, "edge"),
    ] + firefox_histories


def extract_history_to_rows(
    history_path: str | Path, browser_name: str | None = None
) -> list[HistoryRow]:
    """Extrai histórico de um banco SQLite de navegador para uma lista normalizada."""
    history_path = str(history_path)
    if not os.path.exists(history_path):
        print(f"Arquivo de histórico não encontrado: {history_path}")
        return []

    temp_dir = tempfile.gettempdir()
    temp_copy = os.path.join(temp_dir, f"history_copy_{browser_name or 'nav'}.db")
    try:
        shutil.copy2(history_path, temp_copy)
    except Exception as error:
        print(f"Erro ao copiar arquivo de histórico: {error}")
        return []

    try:
        uri = f"file:{temp_copy}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            cursor = conn.cursor()
            if browser_name and browser_name.startswith("firefox"):
                query = """
                SELECT url, title, visit_count, last_visit_date as last_visit_time
                FROM moz_places
                WHERE visit_count > 2
                ORDER BY last_visit_date DESC;
                """
            else:
                query = """
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE visit_count > 2
                ORDER BY last_visit_time DESC;
                """

            cursor.execute(query)
            rows = cursor.fetchall()

            normalized_rows: list[HistoryRow] = []
            for row in rows:
                if row[3] is None:
                    continue

                url = row[0]
                title = row[1] if row[1] else row[0]
                visit_count = int(row[2]) if row[2] is not None else 0
                last_visit_time = int(row[3])
                domain = urlparse(url).netloc
                date_last_visit, hour_last_visit, timestamp_last_visit = (
                    format_visit_datetime(
                        last_visit_time,
                        browser_name,
                    )
                )

                normalized_rows.append(
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
                    )
                )
            return normalized_rows
    except Exception as error:
        print(f"Erro ao ler o banco: {error}")
        return []
    finally:
        try:
            os.remove(temp_copy)
        except Exception:
            pass

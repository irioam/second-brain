"""Compatibility wrapper for building the Obsidian vault."""

import argparse
from pathlib import Path

from second_brain.config import DEFAULT_DB_PATH
from second_brain.vault import build_vault


def parse_args() -> argparse.Namespace:
    """Parse legacy wrapper arguments."""
    parser = argparse.ArgumentParser(
        description="Gera um cofre Obsidian a partir do DuckDB de historico.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run python build_obsidian_vault.py --dry-run\n"
            "  uv run python build_obsidian_vault.py --dry-run --vault-path \"C:\\obsidian\\my_vault\\second_brain\""
        ),
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Caminho do banco DuckDB.")
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="Caminho do cofre Obsidian. Use aspas quando houver espacos no caminho. Se omitido, usa OBSIDIAN_VAULT_PATH ou o fallback do projeto.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula a geracao sem escrever arquivos.")
    parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de notas de fonte geradas.")
    parser.add_argument("--min-visit-count", type=int, default=3, help="Contagem minima de visitas.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_vault(
        db_path=args.db_path,
        vault_path=args.vault_path,
        dry_run=args.dry_run,
        limit=args.limit,
        min_visit_count=args.min_visit_count,
    )

"""Command-line interface for extraction and Obsidian vault generation."""

import argparse
from pathlib import Path

from .config import (
    DEFAULT_DB_PATH,
    EMBEDDING_MODEL_NAME,
    SEMANTIC_DEFAULT_N_CLUSTERS,
)
from .database import sync_history_database
from .extraction import discover_browser_histories
from .semantic import build_semantic
from .vault import build_vault


def run_extract(db_path: Path = DEFAULT_DB_PATH) -> int:
    """Extract browser histories and incrementally sync the DuckDB database."""
    browser_histories = discover_browser_histories()
    return sync_history_database(browser_histories, db_path=db_path)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Second Brain: extrai historico de navegacao e gera cofre Obsidian.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run second-brain extract\n"
            "  uv run second-brain build-vault --dry-run --vault-path \"C:\\obsidian\\my_vault\\second_brain\"\n"
            "  uv run second-brain all --vault-path \"C:\\obsidian\\my_vault\\second_brain\""
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser(
        "extract",
        help="Sincroniza historico dos navegadores para DuckDB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Exemplo:\n  uv run second-brain extract --db-path ./data/second_brain.duckdb",
    )
    extract_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Caminho do banco DuckDB.")

    vault_parser = subparsers.add_parser(
        "build-vault",
        help="Gera o cofre Obsidian a partir do DuckDB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run second-brain build-vault --dry-run\n"
            "  uv run second-brain build-vault --dry-run --vault-path \"C:\\obsidian\\my_vault\\second_brain\""
        ),
    )
    vault_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Caminho do banco DuckDB.")
    vault_parser.add_argument(
        "--vault-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="Caminho do cofre Obsidian. Use aspas quando houver espacos no caminho. Se omitido, usa OBSIDIAN_VAULT_PATH ou o fallback do projeto.",
    )
    vault_parser.add_argument("--dry-run", action="store_true", help="Simula a geracao sem escrever arquivos.")
    vault_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de notas de fonte geradas.")
    vault_parser.add_argument(
        "--min-visit-count",
        type=int,
        default=None,
        help="Contagem minima de visitas. Se omitido, considera todas as visitas.",
    )

    all_parser = subparsers.add_parser(
        "all",
        help="Executa extracao e geracao do cofre.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run second-brain all\n"
            "  uv run second-brain all --vault-path \"C:\\obsidian\\my_vault\\second_brain\""
        ),
    )
    all_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Caminho do banco DuckDB.")
    all_parser.add_argument(
        "--vault-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="Caminho do cofre Obsidian. Use aspas quando houver espacos no caminho. Se omitido, usa OBSIDIAN_VAULT_PATH ou o fallback do projeto.",
    )
    all_parser.add_argument("--dry-run", action="store_true", help="Simula a geracao do cofre sem escrever arquivos.")
    all_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de notas de fonte geradas.")
    all_parser.add_argument(
        "--min-visit-count",
        type=int,
        default=None,
        help="Contagem minima de visitas. Se omitido, considera todas as visitas.",
    )

    semantic_parser = subparsers.add_parser(
        "build-semantic",
        help="Gera agregadores semanticos com embeddings e clusters.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  uv run second-brain build-semantic --dry-run\n"
            "  uv run second-brain build-semantic --n-clusters 12 --llm-provider none"
        ),
    )
    semantic_parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Caminho do banco DuckDB.")
    semantic_parser.add_argument(
        "--vault-path",
        type=Path,
        default=None,
        metavar="PATH",
        help="Caminho do cofre Obsidian. Se omitido, usa OBSIDIAN_VAULT_PATH ou fallback do projeto.",
    )
    semantic_parser.add_argument("--dry-run", action="store_true", help="Simula sem escrever arquivos.")
    semantic_parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de fontes processadas.")
    semantic_parser.add_argument(
        "--min-visit-count",
        type=int,
        default=None,
        help="Contagem minima de visitas para entrar na camada semantica. Se omitido, considera todas as visitas.",
    )
    semantic_parser.add_argument(
        "--n-clusters",
        type=int,
        default=SEMANTIC_DEFAULT_N_CLUSTERS,
        help="Quantidade alvo de clusters semanticos.",
    )
    semantic_parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL_NAME,
        help="Nome do modelo sentence-transformers.",
    )
    semantic_parser.add_argument(
        "--llm-provider",
        choices=("none", "openai", "anthropic", "gemini"),
        default="none",
        help="Provider opcional para rotulo/resumo dos clusters.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the selected CLI command."""
    args = parse_args()

    if args.command == "extract":
        run_extract(db_path=args.db_path)
        return

    if args.command == "build-vault":
        build_vault(
            db_path=args.db_path,
            vault_path=args.vault_path,
            dry_run=args.dry_run,
            limit=args.limit,
            min_visit_count=args.min_visit_count,
        )
        return

    if args.command == "all":
        run_extract(db_path=args.db_path)
        build_vault(
            db_path=args.db_path,
            vault_path=args.vault_path,
            dry_run=args.dry_run,
            limit=args.limit,
            min_visit_count=args.min_visit_count,
        )
        return

    if args.command == "build-semantic":
        build_semantic(
            db_path=args.db_path,
            vault_path=args.vault_path,
            min_visit_count=args.min_visit_count,
            n_clusters=args.n_clusters,
            model_name=args.embedding_model,
            llm_provider=args.llm_provider,
            dry_run=args.dry_run,
            limit=args.limit,
        )
        return

    raise SystemExit("Informe um comando: extract, build-vault, build-semantic ou all.")


if __name__ == "__main__":
    main()

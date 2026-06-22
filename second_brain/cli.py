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


def add_db_path_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared DuckDB path option."""
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the DuckDB database.",
    )


def add_vault_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared vault-generation options."""
    add_db_path_argument(parser)
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Path to the Obsidian vault. Use quotes when the path contains spaces. "
            "If omitted, uses OBSIDIAN_VAULT_PATH or the project fallback."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing vault files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of sources processed.",
    )
    parser.add_argument(
        "--min-visit-count",
        type=int,
        default=None,
        help="Minimum visit count filter. If omitted, all visits are included.",
    )


def add_semantic_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared semantic clustering options."""
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=SEMANTIC_DEFAULT_N_CLUSTERS,
        help="Target number of semantic clusters.",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL_NAME,
        help="Name of the sentence-transformers embedding model.",
    )
    parser.add_argument(
        "--llm-provider",
        choices=("none", "openai", "anthropic", "gemini"),
        default="none",
        help="Optional provider for cluster labels and summaries.",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Second Brain: extract browser history and build an Obsidian vault."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run second-brain extract\n"
            "  uv run second-brain build-vault --dry-run "
            '--vault-path "C:\\obsidian\\my_vault\\second_brain"\n'
            "  uv run second-brain build-semantic --dry-run\n"
            "  uv run second-brain all "
            '--vault-path "C:\\obsidian\\my_vault\\second_brain"'
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser(
        "extract",
        help="Sync browser history into DuckDB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Example:\n"
            "  uv run second-brain extract --db-path ./data/second_brain.duckdb"
        ),
    )
    add_db_path_argument(extract_parser)

    vault_parser = subparsers.add_parser(
        "build-vault",
        help="Build Obsidian Markdown notes from DuckDB.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run second-brain build-vault --dry-run\n"
            "  uv run second-brain build-vault --dry-run "
            '--vault-path "C:\\obsidian\\my_vault\\second_brain"'
        ),
    )
    add_vault_arguments(vault_parser)

    semantic_parser = subparsers.add_parser(
        "build-semantic",
        help="Build semantic aggregators with embeddings and clusters.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run second-brain build-semantic --dry-run\n"
            "  uv run second-brain build-semantic --n-clusters 12 --llm-provider none"
        ),
    )
    add_vault_arguments(semantic_parser)
    add_semantic_arguments(semantic_parser)

    all_parser = subparsers.add_parser(
        "all",
        help="Run extract, vault generation, and semantic clustering.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run second-brain all\n"
            "  uv run second-brain all "
            '--vault-path "C:\\obsidian\\my_vault\\second_brain"\n'
            "  uv run second-brain all --dry-run --n-clusters 12"
        ),
    )
    add_vault_arguments(all_parser)
    add_semantic_arguments(all_parser)

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

    raise SystemExit("Provide a command: extract, build-vault, build-semantic, or all.")


if __name__ == "__main__":
    main()

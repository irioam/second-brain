"""Shared configuration constants for the Second Brain project."""

import os
from pathlib import Path

DEFAULT_DB_PATH = Path("./data/second_brain.duckdb")
VAULT_PATH_ENV_VAR = "OBSIDIAN_VAULT_PATH"
FALLBACK_VAULT_PATH = Path(r"C:\obsidian\my_vault\second_brain")

VAULT_DIRECTORIES = (
    "00 - Index",
    "01 - Sources/Docs",
    "01 - Sources/Articles",
    "01 - Sources/Videos",
    "01 - Sources/Repos",
    "02 - Topics",
    "03 - Daily",
    "03 - Aggregators",
    "03 - Aggregators/Clusters",
    "99 - Attachments",
)

SEMANTIC_ENABLED = True
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SEMANTIC_DEFAULT_N_CLUSTERS = 8


def resolve_default_vault_path() -> Path:
    """Resolve the default vault path from environment or project fallback."""
    env_value = os.environ.get(VAULT_PATH_ENV_VAR)
    if env_value:
        return Path(env_value)
    return FALLBACK_VAULT_PATH

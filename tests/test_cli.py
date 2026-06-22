from pathlib import Path

import pytest

from second_brain import cli


def run_cli_help(monkeypatch: pytest.MonkeyPatch, args: list[str], capsys) -> str:
    monkeypatch.setattr("sys.argv", ["second-brain", *args])
    with pytest.raises(SystemExit) as exc_info:
        cli.parse_args()

    assert exc_info.value.code == 0
    return capsys.readouterr().out


def test_main_help_is_english_and_ordered(monkeypatch, capsys):
    help_text = run_cli_help(monkeypatch, ["--help"], capsys)

    assert "extract browser history and build an Obsidian vault" in help_text
    assert "{extract,build-vault,build-semantic,all}" in help_text
    assert "Sync browser history into DuckDB." in help_text
    assert "Build Obsidian Markdown notes from DuckDB." in help_text
    assert "Build semantic aggregators with embeddings and clusters." in help_text
    assert "Run extract, vault generation, and semantic clustering." in help_text
    assert "Exemplos" not in help_text
    assert "Caminho" not in help_text
    assert "Sincroniza" not in help_text


def test_all_help_includes_vault_and_semantic_options(monkeypatch, capsys):
    help_text = run_cli_help(monkeypatch, ["all", "--help"], capsys)

    assert "--vault-path PATH" in help_text
    assert "--dry-run" in help_text
    assert "--limit LIMIT" in help_text
    assert "--min-visit-count MIN_VISIT_COUNT" in help_text
    assert "--n-clusters N_CLUSTERS" in help_text
    assert "--embedding-model EMBEDDING_MODEL" in help_text
    assert "--llm-provider {none,openai,anthropic,gemini}" in help_text
    assert "Examples:" in help_text
    assert "Simula" not in help_text
    assert "Quantidade" not in help_text


def test_all_dispatch_runs_full_pipeline_in_order(monkeypatch):
    calls = []

    def fake_run_extract(db_path):
        calls.append(("extract", db_path))

    def fake_build_vault(**kwargs):
        calls.append(("build-vault", kwargs))

    def fake_build_semantic(**kwargs):
        calls.append(("build-semantic", kwargs))

    monkeypatch.setattr(cli, "run_extract", fake_run_extract)
    monkeypatch.setattr(cli, "build_vault", fake_build_vault)
    monkeypatch.setattr(cli, "build_semantic", fake_build_semantic)
    monkeypatch.setattr(
        "sys.argv",
        [
            "second-brain",
            "all",
            "--db-path",
            "custom.duckdb",
            "--vault-path",
            "vault",
            "--dry-run",
            "--limit",
            "10",
            "--min-visit-count",
            "3",
            "--n-clusters",
            "12",
            "--embedding-model",
            "custom-model",
            "--llm-provider",
            "none",
        ],
    )

    cli.main()

    assert calls == [
        ("extract", Path("custom.duckdb")),
        (
            "build-vault",
            {
                "db_path": Path("custom.duckdb"),
                "vault_path": Path("vault"),
                "dry_run": True,
                "limit": 10,
                "min_visit_count": 3,
            },
        ),
        (
            "build-semantic",
            {
                "db_path": Path("custom.duckdb"),
                "vault_path": Path("vault"),
                "min_visit_count": 3,
                "n_clusters": 12,
                "model_name": "custom-model",
                "llm_provider": "none",
                "dry_run": True,
                "limit": 10,
            },
        ),
    ]

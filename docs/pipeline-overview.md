# Pipeline Overview

Este documento descreve o fluxo interno da CLI, as funcoes envolvidas e os artefatos gerados.

## Diagrama textual

`extract`
-> `run_extract()`
-> `discover_browser_histories()` + `sync_history_database()`
-> artefato: DuckDB com tabela `historico` sincronizada incrementalmente

`build-vault`
-> `build_vault()`
-> `load_source_notes()` + renderizacao (`render_source_note`, `render_daily_note`, `render_category_note`, `render_moc`)
-> artefatos: `MOC`, notas de fontes, indices por categoria e notas diarias

`all`
-> `run_extract()`
-> `build_vault()`
-> artefatos: atualiza DuckDB + gera cofre

`build-semantic`
-> `build_semantic()`
-> `load_semantic_sources()` + `compute_embeddings()` + `cluster_embeddings()`
-> persistencia semantica (`create_semantic_tables`, `upsert_embeddings`, `replace_cluster_run`)
-> renderizacao semantica (`render_cluster_note`, `render_clusters_index`, `render_aggregator_by_domain`)

## Artefatos gerados

### DuckDB

- `historico`: historico consolidado dos navegadores, preservado incrementalmente.
- `source_embeddings`: embeddings por URL normalizada.
- `source_clusters`: atribuicao URL -> cluster por `run_id`.
- `cluster_metadata`: rotulo/resumo/termos por cluster.

### Cofre Obsidian

- `00 - Index/MOC.md`
- `01 - Sources/<categoria>.md`
- `01 - Sources/<categoria>/*.md`
- `03 - Daily/YYYY-MM-DD.md`
- `03 - Aggregators/Clusters/Cluster-XXX.md`
- `03 - Aggregators/Clusters Index.md`
- `03 - Aggregators/By Domain.md`

## Fluxos de decisao

### Persistencia incremental de `historico`

- `extract` cria ou migra a tabela `historico` sem apagar registros existentes.
- Cada registro usa `history_key`, calculada por navegador + URL normalizada.
- URLs novas sao inseridas e URLs ja conhecidas sao atualizadas quando `last_visit_time` ou `visit_count` aumentam.
- Registros ausentes na nova extracao sao mantidos intactos; limpar o historico do navegador nao zera o DuckDB.

### Resolucao de `vault_path`

Ordem de resolucao:
1. `--vault-path` informado na CLI.
2. Variavel de ambiente `OBSIDIAN_VAULT_PATH`.
3. Fallback do projeto em `config.py`.

### Comportamento de `--min-visit-count`

- Omitido (`None`): sem clausula `WHERE visit_count >= ...` na leitura de fontes.
- Informado (`int`): aplica filtro minimo de visitas na query.

### Fallback de embeddings

No `build-semantic`:
- tenta carregar `sentence-transformers` e gerar embeddings densos.
- em falha de runtime/dependencia/acesso, cai para embeddings deterministas baseados em hash.

## Validacao rapida recomendada

1. `uv run second-brain extract`
2. `uv run second-brain build-vault --dry-run`
3. `uv run second-brain build-semantic --dry-run`

Com esses tres passos, um usuario valida diferenca entre comandos, local dos artefatos e efeito de filtros da CLI.

## Referencias cruzadas

- Visao geral e onboarding: [README.md](../README.md)
- Referencia de parametros: [cli-reference.md](./cli-reference.md)

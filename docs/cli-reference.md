# Referencia da CLI

Este documento descreve todos os comandos e parametros da CLI `second-brain`.

## Comando `extract`

Extrai historico dos navegadores e sincroniza incrementalmente a base DuckDB.

| Parametro | Tipo | Default | Obrigatorio | Descricao |
|---|---|---|---|---|
| `--db-path` | `Path` | `./data/second_brain.duckdb` | Nao | Caminho do banco DuckDB de saida. |

O comando preserva registros existentes que nao aparecerem na extracao atual. Se o historico do navegador for limpo, o DuckDB nao e zerado.

Exemplo minimo:

```bash
uv run second-brain extract
```

Exemplo com caminho explicito:

```bash
uv run second-brain extract --db-path ./data/second_brain.duckdb
```

## Comando `build-vault`

Gera notas Markdown do cofre Obsidian a partir do DuckDB.

| Parametro | Tipo | Default | Obrigatorio | Descricao |
|---|---|---|---|---|
| `--db-path` | `Path` | `./data/second_brain.duckdb` | Nao | Caminho do banco DuckDB de entrada. |
| `--vault-path` | `Path` | `None` | Nao | Caminho do cofre. Se omitido, usa `OBSIDIAN_VAULT_PATH` e depois fallback. |
| `--dry-run` | `flag` | `False` | Nao | Simula a geracao sem escrever arquivos. |
| `--limit` | `int` | `None` | Nao | Limita a quantidade de fontes processadas. |
| `--min-visit-count` | `int` | `None` | Nao | Filtro minimo de visitas por URL. Omitido = todas as visitas. |

Exemplo minimo:

```bash
uv run second-brain build-vault --dry-run
```

Exemplo com filtro:

```bash
uv run second-brain build-vault --min-visit-count 3
```

Exemplo com caminho explicito:

```bash
uv run second-brain build-vault --vault-path "C:\obsidian\my_vault\second_brain"
```

## Comando `all`

Executa `extract` e depois `build-vault` em sequencia.

| Parametro | Tipo | Default | Obrigatorio | Descricao |
|---|---|---|---|---|
| `--db-path` | `Path` | `./data/second_brain.duckdb` | Nao | Caminho do banco DuckDB. |
| `--vault-path` | `Path` | `None` | Nao | Caminho do cofre. |
| `--dry-run` | `flag` | `False` | Nao | Simula apenas a etapa de geracao do cofre. |
| `--limit` | `int` | `None` | Nao | Limita notas na etapa `build-vault`. |
| `--min-visit-count` | `int` | `None` | Nao | Filtro minimo na etapa `build-vault`. Omitido = todas as visitas. |

Exemplo minimo:

```bash
uv run second-brain all
```

Exemplo com filtro:

```bash
uv run second-brain all --min-visit-count 5
```

## Comando `build-semantic`

Gera agregadores semanticos por embeddings e clusterizacao.

| Parametro | Tipo | Default | Obrigatorio | Descricao |
|---|---|---|---|---|
| `--db-path` | `Path` | `./data/second_brain.duckdb` | Nao | Caminho do banco DuckDB. |
| `--vault-path` | `Path` | `None` | Nao | Caminho do cofre. |
| `--dry-run` | `flag` | `False` | Nao | Simula sem escrever arquivos. |
| `--limit` | `int` | `None` | Nao | Limita a quantidade de fontes para clusterizacao. |
| `--min-visit-count` | `int` | `None` | Nao | Filtro minimo de visitas. Omitido = todas as visitas. |
| `--n-clusters` | `int` | `8` | Nao | Quantidade alvo de clusters semanticos. |
| `--embedding-model` | `str` | `sentence-transformers/all-MiniLM-L6-v2` | Nao | Modelo de embedding. |
| `--llm-provider` | `str` | `none` | Nao | Provider opcional para rotulo/resumo: `none`, `openai`, `anthropic`, `gemini`. |

Exemplo minimo:

```bash
uv run second-brain build-semantic --dry-run
```

Exemplo com filtro e clusters:

```bash
uv run second-brain build-semantic --n-clusters 12 --min-visit-count 3 --llm-provider none
```

## Regras importantes

- `--min-visit-count` omitido significa sem filtro por recorrencia (todas as visitas entram).
- `--dry-run` nao cria arquivos no cofre.
- `extract` nao apaga a tabela `historico`; ele faz upsert incremental por navegador + URL normalizada.
- Em `build-semantic`, pode haver fallback de embeddings para modo hash quando runtime de ML local nao estiver disponivel.
- Arquivos Markdown existentes nao sao sobrescritos (`safe write` => `skipped`).

## Referencias cruzadas

- Visao geral: [README.md](../README.md)
- Fluxo interno e artefatos: [pipeline-overview.md](./pipeline-overview.md)

# Second Brain para Obsidian

Este projeto ajuda voce a transformar seu historico de navegacao no seu segundo cérebro que pode ser acessado pelo Obsidian.

Ele transforma links que voce visitou em uma memoria local e pesquisavel: URLs, titulos, dominios, datas de visita e contagem de acessos viram uma base DuckDB e notas Markdown.

Ele faz quatro coisas principais:

1. Le o historico local do Chrome, Edge e Firefox.
2. Salva os dados em um banco DuckDB em `data/second_brain.duckdb`.
3. Gera arquivos Markdown para abrir no Obsidian.
4. Opcionalmente cria agrupamentos (clusters) semanticos por tema.

O comando `extract` e incremental. Isso significa que ele nao apaga o banco quando o navegador esta sem historico. Se voce limpar o historico do navegador, os dados antigos ja salvos no DuckDB continuam guardados.

## Por que usar?

Este projeto e util se voce pesquisa muito e depois perde links importantes no meio do caminho.

Na pratica, ele ajuda voce a:

- Reencontrar paginas que ja visitou.
- Preservar referencias mesmo depois de limpar o historico do navegador.
- Entender quais temas voce pesquisou ao longo do tempo.
- Criar uma base pessoal de estudos, trabalho e pesquisa.
- Manter seus dados no seu proprio computador.

Brutalmente honesto: este projeto nao e para todo mundo. Se voce so navega casualmente, talvez o historico do navegador ja baste. Ele faz mais sentido para estudantes, desenvolvedores, pesquisadores, escritores, analistas e pessoas que usam o Obsidian como base de conhecimento.

## O que ele ainda nao faz

Hoje o projeto organiza o historico e cria notas estruturadas, mas ainda nao captura nem resume automaticamente o conteudo completo das paginas.

As notas geradas sao um ponto de partida. Elas ajudam voce a encontrar, classificar e revisar links, mas a curadoria final ainda e sua.

## Antes de comecar

Voce precisa de:

- Windows.
- PowerShell.
- Python 3.11 ou mais novo.
- `uv`, que instala e executa o projeto.
- Obsidian, se quiser abrir as notas geradas como um cofre.

Para abrir o PowerShell:

1. Aperte a tecla Windows.
2. Digite `PowerShell`.
3. Abra o aplicativo `PowerShell`.

Depois entre na pasta do projeto:

```powershell
cd C:\Users\<seu_usuario>\Documents\second_brain\second_brain
```

## Instalacao passo a passo

### 1. Confira se o Python existe

No PowerShell, rode:

```powershell
python --version
```

Se aparecer algo como `Python 3.11.9`, esta certo.

### 2. Instale o `uv`, se ainda nao tiver

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Depois feche e abra o PowerShell de novo.

### 3. Instale as dependencias do projeto

Dentro da pasta do projeto, rode:

```powershell
uv sync
```

Esse comando baixa tudo que o projeto precisa para funcionar.

### 4. Teste se a CLI responde

```powershell
uv run second-brain --help
```

Se aparecer uma lista de comandos, a instalacao funcionou.

## Comandos principais

### `extract`

Le o historico dos navegadores e sincroniza o banco DuckDB.

```powershell
uv run second-brain extract
```

Use este comando quando quiser atualizar o banco com visitas novas.

### `build-vault --dry-run`

Simula a criacao das notas do Obsidian, sem escrever arquivos.

```powershell
uv run second-brain build-vault --dry-run
```

Use este comando para testar com seguranca.

### `build-vault`

Gera as notas Markdown no cofre Obsidian.

```powershell
uv run second-brain build-vault
```

Se quiser escolher o caminho do cofre:

```powershell
uv run second-brain build-vault --vault-path "C:\obsidian\my_vault\second_brain"
```

### `all`

Faz duas etapas em sequencia:

1. Executa `extract`.
2. Executa `build-vault`.

```powershell
uv run second-brain all
```

Com caminho do cofre:

```powershell
uv run second-brain all --vault-path "C:\obsidian\my_vault\second_brain"
```

Para simular sem escrever arquivos:

```powershell
uv run second-brain all --dry-run
```

### `build-semantic --dry-run`

Simula os agrupamentos semanticos.

```powershell
uv run second-brain build-semantic --dry-run
```

### `build-semantic`

Cria agregadores por tema em `03 - Aggregators`.

```powershell
uv run second-brain build-semantic
```

Na primeira execucao, esse comando pode demorar porque pode carregar ou baixar modelos de embeddings.

## Receitas prontas

### Primeira execucao segura

Use estes comandos para testar sem criar notas ainda:

```powershell
uv run second-brain extract
uv run second-brain build-vault --dry-run
```

### Execucao completa

```powershell
uv run second-brain all
```

### Execucao completa com caminho do cofre

```powershell
uv run second-brain all --vault-path "C:\obsidian\my_vault\second_brain"
```

### Rodar testes

```powershell
uv run pytest
```

## Opcoes uteis da CLI

| Opcao | Para que serve |
|---|---|
| `--db-path` | Muda o caminho do banco DuckDB. |
| `--vault-path` | Muda o caminho do cofre Obsidian. |
| `--dry-run` | Mostra o que aconteceria sem escrever arquivos. |
| `--limit` | Limita a quantidade de notas ou fontes processadas. |
| `--min-visit-count` | Usa apenas URLs com uma quantidade minima de visitas. |
| `--n-clusters` | Define quantos grupos semanticos serao criados. |
| `--embedding-model` | Escolhe o modelo usado para embeddings. |
| `--llm-provider` | Escolhe um provedor para rotulos/resumos. O padrao e `none`. |

## Onde os arquivos ficam

O banco principal fica aqui:

```text
data/second_brain.duckdb
```

As notas do Obsidian seguem uma estrutura parecida com esta:

```text
00 - Index/
01 - Sources/
02 - Topics/
03 - Daily/
03 - Aggregators/
99 - Attachments/
```

O exemplo completo esta em `vault_structure_sample.md`.

## Cuidados importantes

- Os dados ficam locais no seu computador.
- Evite publicar o banco DuckDB ou as notas geradas sem revisar antes.
- Chrome, Edge e Firefox guardam o historico em bancos SQLite.
- Este projeto le esses dados e consolida tudo em DuckDB.
- Apagar o historico do navegador nao apaga automaticamente o DuckDB.
- Arquivos Markdown existentes no Obsidian nao sao sobrescritos.
- Use `--dry-run` quando quiser testar sem criar arquivos.

## Documentacao detalhada

Para detalhes tecnicos, leia:

- [Referencia da CLI](docs/cli-reference.md)
- [Pipeline interno](docs/pipeline-overview.md)
- [Plano do upsert incremental](.plans/incremental-history-upsert-plan.md)

## Estrutura resumida do projeto

```text
second_brain/
  cli.py
  extraction.py
  database.py
  vault.py
  semantic.py
  templates.py
README.md
docs/
  cli-reference.md
  pipeline-overview.md
  incremental-history-upsert-plan.md
```

## Licença

Este projeto está licenciado sob a licença MIT. Consulte [LICENSE](LICENSE) para ler o texto completo da licença.

Você pode usar, modificar e distribuir este projeto, desde que mantenha os créditos ao autor original.

Copyright (c) 2026 Irio Andre Moesch.

GitHub: [https://github.com/irioam](https://github.com/irioam)

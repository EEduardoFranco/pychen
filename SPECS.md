# SPECS — chen-diagram-lang

> A "bíblia" do projeto. Toda decisão de design passa por aqui: se não está na spec,
> ou entra na spec, ou não entra no código.

Status: v0.3 · Última atualização: 2026-10-26

---

## 1. Visão

**chen-diagram-lang** é uma DSL embutida em Python para representar diagramas
conceituais de bancos de dados (notação de Chen) e renderizá-los em SVG.

A declaração do diagrama é código Python idiomático (estilo Django models).
O desenho é produzido automaticamente: o usuário declara **o que** o diagrama é;
o projeto decide **como** desenhá-lo.

Princípios:

1. **Modelo ≠ Desenho.** O modelo é um grafo puro, sem coordenadas. O desenho é derivado.
2. **Declarativo por cima, imperativo por baixo.** A API pública é classe/descritor;
   internamente é um grafo simples que pode ser construído por código (bom p/ testes e serialização).
3. **Determinismo.** Mesma entrada → mesmo SVG (byte a byte, sempre que possível). Nada de
   ordenação por `set()` ou dict de importação.
4. **Erros bons.** Violações de notação Chen são erros de validação com mensagem clara,
   apontando o elemento culpado.

### Filosofia — o Zen de Python (PEP 20)

O **Zen de Python** (`import this`) é a constituição deste projeto. Quando duas opções de
design empatarem tecnicamente, vence a mais alinhada com o Zen. Lema destilado:

> **Simples e funcional é melhor do que complexo e difícil de ler.**

Os aforismos que mais mandam aqui, já aplicados às decisões da spec:

- *Beautiful is better than ugly.* — A declaração de um diagrama lê-se como a própria notação de Chen (seção 4).
- *Explicit is better than implicit.* — Sem registro mágico: `Diagram(elements=[...])` é explícito; validação falha alto.
- *Simple is better than complex.* — `subprocess` ao `dot` em vez de pygraphviz; fragmentos SVG em vez de framework de templates.
- *Flat is better than nested.* — Pacote raso: `model` / `layout` / `render`, nada de camadas abstratas "para o futuro".
- *Readability counts.* — Nomes de teste contam a regra (11.2); a spec lê-se como prosa, não como burocracia.
- *Special cases aren't special enough to break the rules.* — Determinismo byte a byte vale para todo SVG, inclusive nos testes.
- *Errors should never pass silently.* — Diagrama inválido nunca gera SVG (seção 6); skips são explícitos (11.2).
- *There should be one — and preferably only one — obvious way to do it.* — Uma API oficial (seção 4), um runner (`pytest`).
- *Now is better than never.* — Fatias verticais: o 0.1.0 renderiza, ainda que mínimo (seção 10).
- *If the implementation is hard to explain, it's a bad idea.* — O conversor da fase 3 é o juiz final do modelo.

Regra prática de revisão: **toda mudança responde qual aforismo autoriza a complexidade
que ela introduz.** Sem resposta, a mudança não entra.

### Não-objetivos (fase 1)

- PNG/PDF/mermaid (fase futura; SVG basta).
- Posicionamento manual de elementos.
- ISA / especialização-generalização (fase 2).
- Diagramas lógicos e conversão conceitual → lógico (fase 3).
- Editor visual ou interface web.

---

## 2. Escopo da notação (fase 1)

| Conceito | Forma no diagrama | Suporte |
|---|---|---|
| Entidade forte | retângulo | ✅ |
| Entidade fraca | retângulo duplo | ✅ |
| Relacionamento | losango | ✅ |
| Atributo simples | elipse | ✅ |
| Atributo-chave | elipse com texto sublinhado | ✅ |
| Atributo-chave parcial (entidade fraca) | elipse com texto sublinhado tracejado | ✅ |
| Atributo composto | elipse ligada a sub-elipses | ✅ |
| Atributo multivalorado | elipse dupla | ✅ |
| Atributo derivado | elipse tracejada | ✅ |
| Cardinalidade (1, N, M) | rótulo na aresta | ✅ |
| Participação parcial/total | linha simples / linha dupla | ✅ |
| Atributo de relacionamento | elipse ligada ao losango | ✅ |
| ISA | triângulo | ❌ fase 2 |
| Entidade associativa | losango dentro de retângulo | ❌ fase 2 |

Cardinalidades válidas: `"1"`, `"N"`, `"M"` (validadas; qualquer outra coisa é erro).

---

## 3. Arquitetura

Três camadas, dependências só apontando para baixo:

```
┌─────────────────────────────────────────────┐
│  model   grafo puro: Diagram, Entity,       │  ← sem SVG, sem graphviz
│          Relationship, Attribute, ...       │
├─────────────────────────────────────────────┤
│  layout  model → DOT → dot -Tjson →         │  ← graphviz via subprocess
│          posições {x, y, w, h} + splines    │
├─────────────────────────────────────────────┤
│  render   posições + templates SVG →        │  ← fragmentos SVG compostos
│           um único documento .svg           │
└─────────────────────────────────────────────┘
```

Estrutura de pacotes proposta:

```
chen/
  __init__.py          # API pública
  model/
    core.py            # Diagram, identificação, metaclass
    entities.py        # Entity, WeakEntity
    attributes.py      # Attribute, Composite
    relationships.py   # Relationship, Link, Owner
    validate.py        # validações semânticas
  layout/
    dot.py             # model → DOT; dot -Tjson → posições
  render/
    composer.py        # monta o SVG final
    shapes.py          # cada conceito → fragmento
  exceptions.py
templates/             # fragmentos SVG (uma forma por arquivo)
tests/
specs.md               # este arquivo
```

---

## 4. API pública (canônica)

Este exemplo é o **golden test** do projeto. Se ele compilar e renderizar, a spec está viva.

```python
from chen import Diagram, Entity, WeakEntity, Relationship, Attribute, Composite, Link, Owner

class Cliente(Entity):
    cpf = Attribute(primary_key=True)
    nome = Attribute()
    telefones = Attribute(multivalued=True)
    endereco = Composite(
        rua = Attribute(),
        numero = Attribute(),
        cidade = Attribute(),
    )

class Pedido(Entity):
    numero = Attribute(primary_key=True)
    data_emissao = Attribute(derived=True)   # elipse tracejada

class ItemPedido(WeakEntity):
    owner = Owner(Pedido)                    # ligação ao dono (total, (1,1) por definição)
    codigo = Attribute(partial_key=True)     # sublinhado tracejado
    quantidade = Attribute()

class Faz(Relationship):
    cliente = Link(Cliente, "1")             # participação parcial (padrão)
    pedido  = Link(Pedido, "N", total=True)  # participação total (linha dupla)
    valor_total = Attribute(derived=True)    # atributo de relacionamento

diagram = Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz])
diagram.save("vendas.svg")
```

Regras da API:

- **Nome do elemento** no diagrama = nome da classe. Para sobrescrever:
  `class Meta: name = "ClientePJ"`.
- `Diagram(elements=[...])` recebe classes explicitamente — sem registro global mágico.
  A ordem da lista é a ordem de renderização (determinismo).
- Descritores (`Attribute`, `Composite`, `Link`, `Owner`) são declarados como atributos
  de classe; uma metaclass coleta e registra tudo. Reaproveitar a mesma classe
  `Entity` em dois `Diagram`s é permitido (o modelo instancia cópias por diagrama).
- `Diagram.save(path)` e `Diagram.to_svg()` são a saída da fase 1.

---

## 5. Modelo de domínio

Identidade: todo nó/aresta recebe `obj_id` inteiro sequencial por diagrama (evolução do
`Identifier` atual, movido para dentro de `Diagram` — sem contador global de módulo).

Nós do grafo:

- `Entity(name, attributes)` — forte.
- `WeakEntity(owner, partial_key, attributes)` — exatamente **um** dono; a aresta
  dono→fraca é total e de cardinalidade `(1,1)`; exige ao menos um `partial_key`.
- `Relationship(name, links, attributes)` — ≥ 2 `Link`s.
- `Attribute(name, flags)` — flags: `primary_key`, `multivalued`, `derived`, `partial_key`.
- `Composite(name, attributes)` — nó que agrega sub-atributos; renderiza como elipse
  mãe + elipses filhas ligadas.

Arestas do grafo:

- `attributed_to` — atributo → (entidade | relacionamento | composto pai).
- `link` — relacionamento → entidade, portando `cardinality` e `total`.

Invariantes (garantidos pelo construtor/metaclass, não pelo renderizador):

- Aresta `link` só conecta `Relationship` a `Entity`.
- Cardinalidade ∈ {"1", "N", "M"}.
- `WeakEntity` tem `owner`; `Entity` não pode ter `owner`.

---

## 6. Validações (erros, com mensagem apontando o elemento)

| ID | Regra | Severidade |
|---|---|---|
| E01 | Atributo declarado mas nunca anexado a nada | erro |
| E02 | Entidade forte sem atributo-chave | warning |
| E03 | Entidade fraca sem chave parcial | erro |
| E04 | Entidade fraca com mais de um dono | erro |
| E05 | Relacionamento com menos de 2 entidades | erro |
| E06 | Cardinalidade inválida (fora de 1/N/M) | erro (na declaração) |
| E07 | Nomes duplicados no mesmo diagrama | erro |
| E08 | Classe referenciada em `Link`/`Owner` fora do diagrama | erro |

Validação roda **antes** do layout. Diagrama inválido nunca gera SVG.

---

## 7. Pipeline de renderização

1. **Validar** (seção 6).
2. **Modelar → DOT.** Nós com `shape=point` invisíveis? Não: usamos `shape=box` genérico
   e ignoramos a forma — o DOT serve só para geometria. Arestas atributo↔entidade e
   relacionamento↔entidade viram arestas DOT com `label` (cardinalidade).
3. **`dot -Tjson`** → extrair, por nó: `x, y, width, height` (e por aresta: polilinha
   dos splines + posição do label). Graphviz é chamado via **subprocess** (sem pygraphviz,
   que exige compilação no Windows). Se `dot` não estiver no PATH: erro claro com
   instrução de instalação. Dependência opcional: `pip install chen-diagram-lang[layout]`
   documenta o requisito. **Contrato do JSON (verificado com experimento real, Graphviz
   16.1.0):** `bb = "0,0,W,H"` — o ymax é o **4º** número e o eixo y do graphviz cresce
   para cima, então `y_svg = ymax - y`; nós em `objects` com `name` (`n{obj_id}`),
   `pos = "x,y"` (centro, já em points) e `width`/`height` em polegadas (×72 → px);
   arestas em `edges` com `tail`/`head` (`_gvid`), `pos` = spline `"x,y x,y ..."` e
   `lp = "x,y"` — presente só quando a aresta tem `label`.
4. **Compor SVG.** Um documento `<svg>` raiz; para cada nó, instancia o fragmento do
   template correspondente (seção 8) com parâmetros `x, y, w, h, text, variant`;
   arestas viram `<path>` com os splines do graphviz; rótulos de cardinalidade e
   participação total (linha dupla) são desenhados sobre a aresta.
5. **Emitir.** `Diagram.to_svg() -> str` e `Diagram.save(path)`.

---

## 8. Templates SVG

**Regra nova (mudança do protótipo atual):** templates são **fragmentos**, não documentos.
Cada arquivo em `templates/` contém um `<g class="...">` com a forma e o texto, e declara
placeholders `{%param%}`. O documento raiz é gerado pelo composer.

Tabela como implementada no M1 (ajustes do protótipo aprovados na spec — 11.4):

| Template | Forma | Parâmetros |
|---|---|---|
| `Entity.svg` | `<rect>` | x, y (topo-esquerda), w, h, cx, cy (centro do texto), text |
| `WeakEntity.svg` | `<rect>` duplo | (M2) |
| `Relationship.svg` | `<polygon>` (losango) | points (os 4 vértices), cx, cy, text |
| `Attribute.svg` | `<ellipse>` | x, y (centro), rx, ry, text |
| `Attribute_key.svg` | `<ellipse>` + sublinhado | idem `Attribute.svg` |
| `Edge.svg` | `<path>` | d |
| `EdgeLabel.svg` | `<text>` solto | x, y, text |

Ajustes na tabela original, com justificativa: fragmento não avalia expressões, então o
composer passa valores pré-computados — `cx`/`cy` na entidade, `points` no losango; a
variante do atributo **escolhe o arquivo** (`variant="simple"` → `Attribute.svg`,
`variant="key"` → `Attribute_key.svg`) em vez de entrar como parâmetro condicional dentro
de um único template; o rótulo da aresta virou fragmento próprio (`EdgeLabel.svg`) para
não existir `<text>` vazio quando a aresta não tem label. Os demais variants
(`partial_key`, `multivalued`, `derived`) entram no M2 como arquivos novos seguinte o
mesmo esquema.

O `template_loader.py` carrega o fragmento, descobre placeholders por regex
`{%(\w+)%}` e preenche por `str.replace` (nunca `format` — nenhum valor do usuário
passa por interpolação de template); todo texto é escapado: `&`, `<`, `>`, `"`; e os
números saem sempre com `f"{v:.2f}"` (determinismo byte a byte da seção 7).

---

## 9. Serialização (fase 2, decisão antecipada)

O modelo grafo terá `to_json()` / `from_json()` canônicos:

- Servem para testes dourados, cache e futura CLI (`chen render input.json`).
- IDs são determinísticos (ordem da lista `elements` + ordem de declaração dos descritores).
- Formato do JSON será definido na fase 2, mas **nenhum estado visual** entra no modelo —
  logo, o JSON é só semântica.

---

## 10. Roadmap

**Estratégia: fatias verticais.** Cada milestone entrega algo renderizando de ponta a ponta
(modelo → layout → SVG), mesmo que a notação seja parcial. Nada de camada completa
"flutuando" sem uso — o protótipo atual (modelo sem render) mostra o risco de camadas
horizontais incompletas.

**Versionamento:** SemVer em 0.x durante o desenvolvimento. `1.0.0` marca a fase 1 completa
e a promessa de que a API declarativa não muda sem deprecação.

**Regra de ouro:** feature só está pronta quando a spec (este arquivo) foi atualizada junto —
e o roadmap reflete o estado real do trabalho (11.4). Checkbox é registro, não intenção.

### M0 — Fundação (v0.0.x)

Infraestrutura mínima para desenvolver com prazer.

- [x] `git init` — repositório **local** (sem remoto; GitHub fica para quando/ se fizer sentido)
- [x] Venv **dentro do projeto** (`.venv/`) + `.gitignore` cobrindo `.venv/` e `__pycache__/` — seção 11.1
- [x] Pacote `chen/` + `pyproject.toml` (Python ≥ 3.10) com extra `[dev]` + `ruff` + `pytest`
- [x] Migrar o protótipo (`components.py`, `renderer.py`, `template_loader.py`)
      para `chen/model/` — o código atual vira a base, não é jogado fora
- [x] `.agent-playground/` prevista no `.gitignore` — seção 11.3
      *(fechado na sessão de 2026-10-26: entrada adicionada ao `.gitignore` e `demo.dot` apagado da raiz)*

**DoD:** `pip install -e .` e `pytest` verdes rodando localmente.

### M1 — Esqueleto vertical (v0.1.0)

O caminho feliz completo, com notação mínima. Objetivo: provar o pipeline, não a cobertura.

- [x] Metaclass + `Entity` + `Attribute` (simples e chave) + `Relationship` + `Link`
      *(implementado via `__init_subclass__` + `__set_name__` — decisão registrada em §13)*
- [x] Validações mínimas: E05, E06 (as que caem grátis na declaração) — mais E08, que caiu
      de graça como guarda do consumo de links (`None` silencioso é violação do Zen)
- [x] Layout: modelo → DOT → `dot -Tjson` → posições
- [x] Render: fragmentos `Entity`/`Relationship`/`Attribute` + arestas + rótulo de cardinalidade
- [x] Golden test v1: `Cliente` + `Pedido` + `Faz` → SVG (snapshot syrupy, revisado no preview)

**DoD:** ✅ verificado em 2026-10-26 — a versão reduzida do exemplo da seção 4 gera SVG
válido e determinístico (duas execuções → bytes idênticos; 53 testes verdes com v0.1.0).

### M2 — Notação intermediária completa (v0.2.0)

Completar a tabela da seção 2.

- [ ] `WeakEntity` + `Owner` + `partial_key` (retângulo duplo, sublinhado tracejado)
- [ ] `Composite` (elipse mãe + filhas), `multivalued` (elipse dupla), `derived` (tracejada)
- [ ] Participação total (linha dupla) nas arestas
- [ ] Atributos de relacionamento (elipse ligada ao losango)
- [ ] Snapshots de SVG por variante de forma (uma falha de regressão = um arquivo diff-ável)

**DoD:** o exemplo canônico da seção 4, completo, renderiza conforme a seção 2.

### M3 — Robustez e DX (v0.3.0) → fecha a fase 1

- [ ] Validações E01–E08 completas, com mensagens apontando o elemento culpado
- [ ] Erro claro quando `dot` não estiver no PATH (instrução de instalação)
- [ ] Teste de idempotência: mesmo modelo sempre → mesmo SVG
- [ ] README com quickstart; exemplos em `examples/`
- [ ] Publicar no PyPI (opcional, decide na hora)

**DoD:** fase 1 fechada; tag `1.0.0`.

### Fase 2 — Chen completo (0.4.x)

- [ ] ISA: triângulo, total/parcial, disjunta/sobreposta
- [ ] Entidade associativa (losango dentro de retângulo)
- [ ] Serialização: `to_json()` / `from_json()` determinísticos (seção 9)
- [ ] PNG como extra (`[png]`)

### Fase 3 — Diagramas lógicos (0.5.x)

- [ ] Modelo lógico: `Table`, `Column`, PK/FK, com render próprio
- [ ] Conversor conceitual → lógico:
      1:N vira FK no lado N · N:N vira tabela intermediária ·
      multivalorado vira tabela própria · entidade fraca absorve a PK do dono
- [ ] O conversor é a recompensa por ter o modelo certo: se ele for difícil, o modelo
      da seção 5 está errado e volta para revisão.

### Backlog (sem compromisso, sem data)

- CLI (`chen render diagram.py -o out.svg`)
- CI (quando o projeto ganhar um repositório remoto)
- Export para DOT e Mermaid (embed em GitHub/Notion)
- Notação pé-de-galinha (crow's foot) reutilizando o mesmo modelo
- Playground web / render inline no Jupyter
- Hints de posicionamento manual (override fino sobre o graphviz)

---

## 11. Fluxo de desenvolvimento — TDD e ambiente

Esta spec é o contrato para quem implementa (agente ou humano). Dúvida de design se
resolve **aqui**, atualizando a spec — nunca em decisão implícita no código.

### 11.1 Ambiente — venv dentro do projeto

O ambiente virtual vive na raiz do repositório. Nada de instalar dependências no
Python global do sistema.

```
python -m venv .venv            # na raiz do projeto (uma vez)
.venv\Scripts\Activate.ps1      # ativação no PowerShell (Windows)
pip install -e ".[dev]"         # instalação editável + ferramentas
```

- `.venv/` e `__pycache__/` entram no `.gitignore` (item do M0).
- O extra `[dev]` do `pyproject.toml` reúne tudo que o desenvolvimento precisa:
  `pytest`, `pytest-cov`, `ruff` e o utilitário de snapshot escolhido.
- **Teste de sanidade do ambiente:** recriar do zero deve ser exatamente dois comandos
  (`python -m venv .venv` + `pip install -e ".[dev]"`). Um comando a mais = `pyproject.toml` errado.

### 11.2 Disciplina TDD

Todo código de produção nasce de um teste que falhou primeiro. Ciclo Red–Green–Refactor,
nesta ordem, sem pular etapas:

1. **Red** — escrever o teste que materializa uma regra desta spec (seção 2, 4, 5, 6 ou 10).
   Rodar `pytest` e vê-lo falhar **pelo motivo certo** (assert, não `ImportError`/typo).
2. **Green** — escrever o **mínimo** de produção para o teste passar. Sem antecipar o
   próximo passo.
3. **Refactor** — limpar código e teste mantendo o verde. Repetir.

Regras que valem para todo milestone:

- **Testes descrevem comportamento, não implementação.** Nome de teste fala da regra
  (`test_entidade_fraca_sem_chave_parcial_gera_E03`), não do método (`test_validate`).
- **Bug corrigido = teste de regressão primeiro:** reproduzir o bug (Red), depois corrigir (Green).
- **Golden test é a bússola do roadmap:** cada milestone estende o exemplo da seção 4 —
  M1 roda a versão reduzida, M2 a versão completa. O golden é de ponta a ponta: exige
  `dot`, e pula com skip explícito (mesma disciplina dos testes de layout).
- **SVG é comparado por snapshot** (determinismo byte a byte da seção 7). Atualização de
  snapshot é ato consciente, com `--snapshot-update`, e revisado no diff.
- **Validações E01–E08 têm tabela de teste própria:** um teste por regra + o caso feliz.
- **Estrutura de `tests/` espelha `chen/`:** `tests/model/`, `tests/layout/`, `tests/render/`.
- **Cobertura** medida com `pytest-cov`; alvo explícito: 100% em `chen/model`. Nas outras
  camadas, o número é indicador — quem manda é o teste, não o percentual.
- `pytest` é o único runner; testes não exigem `dot` instalado exceto os de `tests/layout/`,
  que pulam com marcador próprio quando o executável não existe (skips explícitos, nunca erros).

### 11.3 Playground do agente — `.agent-playground/`

Experimentos fazem parte do processo (testar o `dot`, inspecionar a saída `-Tjson`,
prototipar uma regex, medir tamanhos de forma). Esses experimentos acontecem
**exclusivamente** na pasta oculta `.agent-playground/`, na raiz do projeto — nunca
esparramados pela árvore do repositório (o histórico `demo.dot` solto na raiz é o
anti-exemplo).

- **Experimentar ali é livre e encorajado**: sem precisar de teste, justificativa ou permissão.
- Nada de dentro dela entra no git (`.gitignore`, item do M0) — mas nada dela é
  importado pelo pacote ou referenciado por `tests/` tampouco.
- **Regra de ouro: a pasta termina a tarefa vazia.** Agente que cria `demo.dot` ali,
  apaga `demo.dot` quando o experimento conclui.
- **Experimento que valeu algo vira teste**, com nome de comportamento (11.2) — nunca
  arquivo solto na playground.
- Conclusões descobertas por experimento vão para **esta spec** (ex.: detalhe do
  `-Tjson` que só se descobre rodando), não para anotações na playground.

### 11.4 Acompanhamento — a spec é o quadro de tarefas

O agente trabalha **com o roadmap aberto** (seção 10) e o mantém vivo enquanto trabalha:

- **Antes de começar** qualquer sessão ou tarefa: ler o diário de bordo (seção 13) e o
  roadmap; identificar o milestone e o próximo item. Não se trabalha de memória.
- **Durante:** cada item completado é marcado `[x]` **no momento em que é verificado** —
  checkbox é registro do estado real, nunca intenção. Sem verificação feita (testes
  verdes, DoD cumprido), sem `[x]`.
- **Anotações:** descobertas, desvios e restrições encontrados no caminho viram anotação
  na spec — na seção pertinente (como a nota pendente do M0) ou no diário de bordo
  (seção 13). Nunca em arquivo externo, comentário de código ou memória da sessão.
- **Desvio de design:** se o trabalho revela que a spec está errada, atualiza-se a spec
  **antes** do código — o mesmo contrato de 11.2 vale para o roadmap.
- **Fechamento de milestone:** marcar o DoD, registrar no diário de bordo (data, versão,
  notas) e criar a tag correspondente, quando aplicável.

## 12. Convenções

- Pacote: `chen` (repositório: `chen-diagram-lang`). Python ≥ 3.10.
- Nomes públicos da API em inglês; documentação e mensagens de erro em inglês;
  discussão/spec em português.
- Testes: TDD com `pytest` — a **seção 11 é a autoridade**; nada aqui a sobrepõe.
- Estilo: docstrings em todo público, type hints obrigatórios, `ruff` para lint/format.

---

## 13. Diário de bordo

Registro vivo do trabalho, mantido pelo agente que executa (regra 11.4). Uma linha por
evento significativo: item concluído, decisão tomada, desvio de rota. A primeira leitura
de qualquer sessão é **seção 13 + seção 10**.

| Data | Evento | Notas |
|---|---|---|
| 2026-10-26 | Spec v0.1 criada — decisões de API, layout, escopo, roadmap | — |
| 2026-10-26 | Spec v0.2 — Zen como filosofia (seção 1), TDD + venv (seção 11), playground (11.3), acompanhamento (11.4) | — |
| 2026-10-26 | M0 executado pelo agente implementador (git, venv, pacote `chen/`, migração do protótipo) | Pendente: `.agent-playground/` no `.gitignore` e limpeza do `demo.dot` da raiz |
| 2026-10-26 | Tag `v0.1.0` criada no fechamento do M1 | — |
| 2026-10-26 | M2 iniciado — TDD camada model: flags de atributo, `WeakEntity`/`Owner` (E03/E04), `Composite`, participação total e atributos de relacionamento | — |
| 2026-10-26 | HANDOFF.md removido (conteúdo incorporado ao trabalho); item pendente do M0 fechado; `SPECS.md` v0.2 commitado | M0 ✅ |
| 2026-10-26 | M1 iniciado — TDD camada model: testes Red em `tests/model/` | — |
| 2026-10-26 | M1 model ✅ — `__init_subclass__` + `__set_name__` (não metaclass explícita; decisão do handoff confirmada no código), ids por diagrama (nós e arestas dividem a sequência), E05/E06/E08 | commit `741c098` |
| 2026-10-26 | M1 layout ✅ — `to_dot` + `compute_layout`; contrato `-Tjson` anotado em §7 (ymax é o 4º número — corrigido por experimento, protótipo/handoff dizia 3º); testes skipam sem `dot` (§11.2) | — |
| 2026-10-26 | M1 render ✅ — fragmentos + loader com escape + shapes + composer; desvios de template aprovados na spec §8 (cx/cy, points, variant→arquivo, EdgeLabel) | — |
| 2026-10-26 | M1 ✅ DoD verificado — `to_svg`/`save` com import lazy; golden v1 com snapshot syrupy (pacote no PyPI se chama `syrupy`, não `pytest-syrupy`); versão 0.1.0 | M1 fechado |
| 2026-10-26 | Revisão pós-M1: rotina verde (53 testes + snapshot), cobertura 100% total (alvo da §11.2 em `chen/model` cumprido); guard `TypeError` em `validate_diagram` removido sem teste — função interna, chamada indevida já falha alto com `AttributeError` | — |
| 2026-10-26 | **Nota operacional:** em shells abertos antes da instalação do Graphviz, prepend `$env:PATH = "C:\Program Files\Graphviz\bin;" + $env:PATH` antes do pytest (o `dot` fica em `C:\Program Files\Graphviz\bin\dot.exe`); sem `dot` no PATH, os testes de `tests/layout/` e o golden pulam com skip explícito, nunca erro | — |

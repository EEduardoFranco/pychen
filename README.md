# pychen

A Python DSL for drawing database conceptual diagrams in **Chen notation**,
rendered as deterministic SVG.

You declare **what** the diagram is — as plain Python classes, Django-models style.
The project decides **how** to draw it: the model is a pure graph, the layout comes
from Graphviz, and the SVG is composed from fragments. Same input → same pixels,
byte for byte.

```python
from pychen import Diagram, Entity, WeakEntity, Relationship, Attribute, Composite, Link, Owner

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
    data_emissao = Attribute(derived=True)   # dashed ellipse

class ItemPedido(WeakEntity):
    owner = Owner(Pedido)                    # double line, (1,1) by definition
    codigo = Attribute(partial_key=True)     # dashed underline
    quantidade = Attribute()

class Faz(Relationship):
    cliente = Link(Cliente, "1")             # partial participation (default)
    pedido  = Link(Pedido, "N", total=True)  # total participation (double line)
    valor_total = Attribute(derived=True)    # relationship attribute

diagram = Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz])
diagram.save("vendas.svg")
```

## Requirements

- Python **≥ 3.10**
- [Graphviz](https://graphviz.org/download/) — the `dot` executable must be on your
  `PATH` (used for geometry only, via `subprocess`).

## Install (from source)

The project is **not published to PyPI yet**. Clone the repository and install
editable + dev tools into a project-local venv:

```console
python -m venv .venv
.venv\Scripts\Activate.ps1                        # Windows (source .venv/bin/activate on POSIX)
pip install -e ".[dev]"
```

## Notation support (phase 1)

| Concept | Rendered as | |
|---|---|---|
| Strong entity | rectangle | ✅ |
| Weak entity | double rectangle | ✅ |
| Relationship | diamond | ✅ |
| Attribute | ellipse | ✅ |
| Key attribute | underline | ✅ |
| Partial key (weak) | dashed underline | ✅ |
| Composite attribute | mother ellipse + child ellipses | ✅ |
| Multivalued attribute | double ellipse | ✅ |
| Derived attribute | dashed ellipse | ✅ |
| Cardinality (1, N, M) | edge label | ✅ |
| Total / partial participation | double / single line | ✅ |
| Relationship attribute | ellipse attached to the diamond | ✅ |

Invalid diagrams raise `ChenError(ValidationError)` with the rule id (E01–E08) and
the culprit element — an invalid diagram never produces SVG. Strong entities
without a key raise a `UserWarning` (E02).

See [SPECS.md](SPECS.md) for the full project bible (Portuguese): design decisions,
rendering pipeline, TDD workflow and the living roadmap.

## Examples

Runnable scripts in [`examples/`](examples/) — run them from the repository root;
each one writes an `.svg` next to itself:

```console
python examples/vendas.py        # canonical example from the spec
python examples/biblioteca.py    # a second domain: library loans
```

## Development

- **Tests:** `pytest` is the only runner. Layout tests (and the end-to-end golden
  test) skip explicitly when `dot` is not on `PATH`.
- **Lint/format:** `ruff check .` and `ruff format .`
- **Process:** strict TDD (red → green → refactor). Every behavior lives in a
  test named after the rule; SVG snapshots are updated only consciously with
  `--snapshot-update` and reviewed in the diff.

## Ownership, process and AI use

pychen was developed with the assistance of an AI coding model to accelerate
the writing of code and documentation — not to make decisions for it. The
design decisions, the review of every change and the ownership of this project
are the author's, and they are kept honest by a process designed so that trust
is earned, not assumed:

- an explicit, living technical specification ([SPECS.md](SPECS.md)) — design
  disputes are resolved in the spec *before* the code;
- strict **TDD** (red → green → refactor): every behavior is born from a test
  named after the rule it pins;
- automated validation rules (E01–E08) and tests that verify the expected
  behavior — a golden end-to-end pipeline test, byte-for-byte SVG snapshots
  and idempotency checks;
- deterministic output: the same declaration always produces the same SVG.

The assistant used was **GLM-5.3-Flash**, provided free of charge by the
[OpenCode](https://opencode.ai) harness. The goal is a useful tool for
conceptual database modeling, with the architecture decisions documented and
the implementation evolving in steps.

**Author & maintainer:** Eduardo Franco
([@EEduardoFranco](https://github.com/EEduardoFranco)) — see
[DEMO.md](DEMO.md) for a short, honest walkthrough of the process in action.

# pychen — a short technical demo

A small, honest walkthrough of the engineering behind the project: declare a
conceptual model, validate it, render it, verify the behavior with tests, and
investigate/fix a defect. Sized for an interview conversation — nothing grand
here. Every number cited was verified against this very codebase
(`pytest -q --cov`: **147 tests · 100% coverage**).

## 1. Declaring a conceptual model

The declaration is idiomatic Python (Django-models style). You state **what**
the diagram is; the library decides **how** to draw it.

```python
from pychen import Diagram, Entity, Relationship, Attribute, Link

class Cliente(Entity):
    cpf = Attribute(primary_key=True)
    nome = Attribute()

class Pedido(Entity):
    numero = Attribute(primary_key=True)

class Faz(Relationship):
    cliente = Link(Cliente, "1")
    pedido  = Link(Pedido, "N")

diagram = Diagram("Vendas", elements=[Cliente, Pedido, Faz])
```

Class names become diagram element names (`class Meta: name = ...` overrides).
No global registration — `Diagram(elements=[...])` receives the classes
explicitly, and ordering is deterministic. The same `Entity` class may be
reused across different diagrams.

## 2. Validating the model

Chen notation is enforced by eight validation rules (E01–E08). Validation runs
**before** layout: an invalid diagram never produces SVG, and errors point at
the culprit element.

```python
from pychen import Diagram, WeakEntity

class Item(WeakEntity):
    pass  # weak entities require exactly one owner and a partial key

Diagram("Bag", elements=[Item])
# ValidationError: weak entity "Item" requires at least one partial key  (rule E03)
```

That is the actual message from `pychen/model/validate.py`. Strong entities
without a key raise a `UserWarning` (E02) instead of a hard failure — the
library warns loudly but lets you work.

## 3. Generating the diagram

The drawing is derived, never configured. Pipeline: pure graph model →
DOT source → `dot -Tjson` (Graphviz geometry) → node/edge positions → SVG
fragments composed into a single document.

```python
svg = diagram.to_svg()       # str
diagram.save("vendas.svg")   # file
```

Determinism is a stated project principle, not a hope: the same input produces
the same SVG — byte for byte — and tests enforce it.

## 4. How the tests protect the behavior

- **End-to-end golden test:** the canonical spec example runs the entire
  pipeline (model → layout → render) and is pinned by an SVG snapshot.
- **Byte-for-byte snapshots** (syrupy): a regression appears as an exact
  diff. Snapshot updates are conscious acts (`--snapshot-update`), reviewed
  in the diff.
- **Idempotency tests:** independent diagrams rendered twice → identical
  bytes, every time.
- **TDD as discipline (red → green → refactor):** each change starts from a
  failing test named after the rule it pins
  (`test_entidade_fraca_sem_chave_parcial_gera_E03`), then the minimum
  production code, then refactor.
- **Current verified state:** 147 tests green · 100% coverage (651
  statements) · `ruff` clean.

```console
pytest -q            # everything green; layout tests skip explicitly when `dot` is absent
pytest --cov=pychen  # coverage report
```

## 5. Investigating and fixing a defect (a real story, from the project log)

During the second milestone, a subtle bug was born and died in the same test
cycle: relationship **links** were receiving the wrong `tail` — the last node
created, not the entity they referenced.

1. **Reproduce first (Red):** the new behavior test for relationship
   attributes asserted on the built graph (`tail`/`head`) and failed for the
   right reason — exposing the defect before it shipped.
2. **Isolate:** the builder (`_build_links`) read `self.nodes[-1]` *after*
   copying the relationship's own attributes, so "the last node" belonged to
   the attribute, not to an entity.
3. **Fix minimally (Green):** restore the correct pairing in `_build_links`.
4. **Keep the regression:** the test that reproduced it stays in the suite
   forever.
5. **Check the neighborhood:** the golden test and the render snapshots
   passed again — no re-snapshot needed.

The defect was caught by the process, not by luck. The project log
(`SPECS.md` §13) records the episode, the fix and the reason it was caught by
TDD.

## On AI-assisted development

The codebase was written with the help of an AI model (GLM-5.3-Flash, provided
free of charge by the [OpenCode](https://opencode.ai) harness) to accelerate
the writing of code and documentation. What makes that responsible is the
process above: an explicit, living specification; tests that pin the expected
behavior; deterministic output; and human review of every change. The design
decisions and the ownership of this project are the author's. See the README
section "Ownership, process and AI use".

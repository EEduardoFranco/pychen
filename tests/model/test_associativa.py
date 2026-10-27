"""Entidade associativa (spec §2/§5, fase 2): relacionamento que participa de
outros relacionamentos — losango dentro de retângulo.

Decisão de API (registrada em §13, 2026-10-27): subclasse dedicada
`AssociativeRelationship`. Ela coleciona Links como `Relationship` e pode ser
**alvo** de `Link`; alvo inválido (relacionamento comum, atributo, etc.) é E08.
Um `Link` para associativa declarada depois na lista `elements` resolve no passe
de arestas pendentes (§5, invariante de backtracking).
"""

import pytest

from pychen.exceptions import ValidationError
from pychen.model import (
    AssociativeRelationship,
    Attribute,
    Diagram,
    Entity,
    Link,
    Relationship,
)


class TestAssociativeDeclaracao:
    def test_associativa_coleciona_links_e_atributos_como_relationship(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Produto(Entity):
            codigo = Attribute(primary_key=True)

        class VendaProduto(AssociativeRelationship):
            cliente = Link(Cliente, "1")
            produto = Link(Produto, "N")
            quantidade = Attribute()

        diagrama = Diagram("Vendas", elements=[Cliente, Produto, VendaProduto])

        nomes = [node.name for node in diagrama.nodes]
        associativa = [n for n in diagrama.nodes if isinstance(n, AssociativeRelationship)]
        assert "VendaProduto" in nomes
        assert len(associativa) == 1
        arestas = [(e.kind, e.label or "") for e in diagrama.edges]
        assert ("link", "1") in arestas and ("link", "N") in arestas

    def test_associativa_e_alvo_de_link_de_outro_relacionamento(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Produto(Entity):
            codigo = Attribute(primary_key=True)

        class VendaProduto(AssociativeRelationship):
            cliente = Link(Cliente, "1")
            produto = Link(Produto, "N")

        class Faturada(Relationship):
            venda = Link(VendaProduto, "N")
            nota = Link(Cliente, "1")  # segundo link para satisfazer E05

        diagrama = Diagram("Vendas", elements=[Cliente, Produto, VendaProduto, Faturada])

        venda = [n for n in diagrama.nodes if n.name == "VendaProduto"][0]
        aresta_faturada = [e for e in diagrama.edges if e.kind == "link" and e.tail != venda.obj_id]
        alvos = {e.head for e in aresta_faturada}
        assert venda.obj_id in alvos

    def test_link_para_associativa_listada_depois_na_lista_resolve(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Produto(Entity):
            codigo = Attribute(primary_key=True)

        class VendaProduto(AssociativeRelationship):
            cliente = Link(Cliente, "1")
            produto = Link(Produto, "N")

        class Faturada(Relationship):
            venda = Link(VendaProduto, "N")
            nota = Link(Cliente, "1")

        # Faturada PRIMEIRO na lista, o alvo associativo por último
        diagrama = Diagram("V", elements=[Cliente, Produto, Faturada, VendaProduto])

        assert len(diagrama.edges) == 6  # 2 attributed + 4 links
        vendas = [n for n in diagrama.nodes if n.name == "VendaProduto"]
        assert len(vendas) == 1

    def test_alvo_de_link_que_nao_e_entidade_nem_associativa_e_E08(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Consulta(Relationship):
            pass

        class Perturbadora(Relationship):
            cliente = Link(Cliente, "1")
            estranha = Link(Consulta, "N")  # relacionamento comum não pode ser alvo

        # Consulta ESTÁ na lista: o caso não é "fora do diagrama" (E08 clássico),
        # é de tipo de alvo (§5: alvo ∈ Entity | AssociativeRelationship)
        with pytest.raises(ValidationError, match="Link target"):
            Diagram("V", elements=[Cliente, Consulta, Perturbadora])

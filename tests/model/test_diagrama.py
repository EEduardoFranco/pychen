"""Diagram e construção do grafo (spec §4–§5): cópias por diagrama, ids sequenciais,
ordem determinística e arestas do grafo.
"""

from pychen.model import Attribute, Diagram, Entity, Link, Relationship


def _vendas_classes():
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    return Cliente, Pedido, Faz


class TestConstrucao:
    def test_diagrama_instancia_copias_por_diagrama(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        entidades = [n for n in diagrama.nodes if isinstance(n, Entity)]
        assert [n.name for n in entidades] == ["Cliente", "Pedido"]

    def test_ids_sao_sequenciais_por_diagrama(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        ids = [n.obj_id for n in diagrama.nodes]
        assert ids == sorted(ids)
        assert ids[0] == 1

    def test_mesma_classe_em_dois_diagramas_gera_instancias_diferentes(self):
        Cliente, Pedido, Faz = _vendas_classes()

        d1 = Diagram("A", elements=[Cliente, Pedido, Faz])
        d2 = Diagram("B", elements=[Cliente, Pedido, Faz])

        e1 = [n for n in d1.nodes if isinstance(n, Entity)][0]
        e2 = [n for n in d2.nodes if isinstance(n, Entity)][0]

        assert e1 is not e2
        assert e1.obj_id == 1 and e2.obj_id == 1

    def test_atributos_sao_copiados_com_valores_do_descritor(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        cliente = [n for n in diagrama.nodes if isinstance(n, Entity)][0]
        por_nome = {a.name: a for a in cliente.attributes}

        assert set(por_nome) == {"cpf", "nome"}
        assert por_nome["cpf"].primary_key is True

    def test_arestas_do_grafo(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        cliente = [n for n in diagrama.nodes if isinstance(n, Entity)][0]
        pedido = [n for n in diagrama.nodes if isinstance(n, Entity)][1]
        faz = [n for n in diagrama.nodes if isinstance(n, Relationship)][0]

        por_kind = {}
        for e in diagrama.edges:
            por_kind.setdefault(e.kind, []).append(e)

        tipos_atributo = {e.tail for e in por_kind["attributed_to"]}
        assert tipos_atributo == {a.obj_id for a in cliente.attributes} | {
            a.obj_id for a in pedido.attributes
        }

        links = por_kind["link"]
        pares = {(e.tail, e.head) for e in links}
        assert pares == {(faz.obj_id, cliente.obj_id), (faz.obj_id, pedido.obj_id)}

    def test_aresta_link_carrega_cardinalidade(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        links = [e for e in diagrama.edges if e.kind == "link"]
        cliente = [n for n in diagrama.nodes if isinstance(n, Entity)][0]
        pedido = [n for n in diagrama.nodes if isinstance(n, Entity)][1]

        rotulos = {}
        for e in links:
            rotulos[e.head] = e.label

        assert rotulos[cliente.obj_id] == "1"
        assert rotulos[pedido.obj_id] == "N"

    def test_entidades_vem_antes_dos_relacionamentos_nos_ids(self):
        Cliente, Pedido, Faz = _vendas_classes()

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        faz = [n for n in diagrama.nodes if isinstance(n, Relationship)][0]
        entidades = [n for n in diagrama.nodes if isinstance(n, Entity)]

        assert faz.obj_id > max(e.obj_id for e in entidades)

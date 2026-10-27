"""Composite (spec §4–§5, §8): elipse mãe ligada a sub-elipses.

Declarado como descritor no corpo da classe; os sub-atributos anexam ao composto,
não à entidade — a aresta mãeentidade→composto→filhas.
 Participação total (Link(total=True)) também é exercida aqui (spec §2).
"""

from chen import Attribute, Composite, Diagram, Entity, Link, Relationship


def _vendas_com_composto():
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        endereco = Composite(
            rua=Attribute(),
            numero=Attribute(),
            cidade=Attribute(),
        )

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N", total=True)

    return Cliente, Pedido, Faz


class TestDeclaracao:
    def test_composto_captura_o_nome_do_campo_e_os_subatributos(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            endereco = Composite(rua=Attribute(), numero=Attribute())

        assert Cliente.endereco.name == "endereco"
        assert [a.name for a in Cliente.endereco.sub_attributes] == ["rua", "numero"]


class TestGrafo:
    def test_composto_e_filhas_anexam_a_entidade_por_areastas_atributo(self):
        _Cliente, _Pedido, _Faz = _vendas_com_composto()

        diagrama = Diagram("Vendas", elements=[_Cliente, _Pedido, _Faz])

        cliente = [n for n in diagrama.nodes if n.name == "Cliente"][0]
        nomes = [n.name for n in diagrama.nodes]

        assert nomes.count("rua") == 1 and nomes.count("cidade") == 1
        atributos_do_cliente = {a.name for a in cliente.attributes}

        assert "cpf" in atributos_do_cliente
        assert "endereco" in atributos_do_cliente

    def test_subatributo_liga_ao_composto_mas_nao_a_entidade(self):
        _Cliente, _Pedido, _Faz = _vendas_com_composto()

        diagrama = Diagram("Vendas", elements=[_Cliente, _Pedido, _Faz])

        cliente = [n for n in diagrama.nodes if n.name == "Cliente"][0]
        endereco = cliente.attributes[1]  # segunda declaração
        mapa = {n.name: n.obj_id for n in diagrama.nodes}

        arestas_do_cliente = [
            e for e in diagrama.edges if e.head == cliente.obj_id and e.kind == "attributed_to"
        ]
        assert {e.tail for e in arestas_do_cliente} == {
            mapa["cpf"],
            mapa["endereco"],
        }

        arestas_do_composto = [e for e in diagrama.edges if e.head == endereco.obj_id]
        assert {e.tail for e in arestas_do_composto} == {a.obj_id for a in endereco.attributes}


class TestParticipacaoTotal:
    def test_link_com_total_guarda_a_participacao(self):
        _Cliente, _Pedido, _Faz = _vendas_com_composto()

        diagrama = Diagram("Vendas", elements=[_Cliente, _Pedido, _Faz])

        pedido = [n for n in diagrama.nodes if n.name == "Pedido"][0]
        link_total = [e for e in diagrama.edges if e.head == pedido.obj_id and e.kind == "link"]

        assert link_total[0].total is True

    def test_link_sem_total_e_parcial_por_padrao(self):
        _Cliente, Pedido, _Faz = _vendas_com_composto()

        class Parcial(Relationship):
            cliente = Link(_Cliente, "1")
            pedido = Link(Pedido, "1")

        diagrama = Diagram("V", elements=[_Cliente, Pedido, Parcial])

        assert all(e.total is False for e in diagrama.edges if e.kind == "link")


class TestAtributosDeRelacionamento:
    def test_atributo_do_relacionamento_anexa_ao_losango(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")
            valor_total = Attribute(derived=True)

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        faz = [n for n in diagrama.nodes if isinstance(n, Relationship)][0]
        valor = faz.attributes[0]

        assert valor.name == "valor_total"
        assert valor.derived is True
        arestas = [e for e in diagrama.edges if e.tail == valor.obj_id]
        assert [e.head for e in arestas] == [faz.obj_id]

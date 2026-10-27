"""Serialização — to_json()/from_json() canônicos (spec §9, fase 2).

Formato definido na própria §9: grafo plano, format: 1, flags/label/total omitidos
quando default; from_json revalida (validate_diagram), reatribui ids sequenciais
e remapeia tail/head. Round-trip é identidade.
"""

import pytest

from chen.exceptions import ValidationError
from chen.model import (
    Attribute,
    Composite,
    Diagram,
    Entity,
    Link,
    Owner,
    Relationship,
    WeakEntity,
)


def _vendas_reduzido_data() -> dict:
    """Dump canônico esperado de Cliente(cpf, nome) + Pedido(numero) + Faz(1, N).

    Ids no JSON são posições canônicas (§9): nós 1..6 na ordem de emissão,
    arestas 7..11 depois; tails/heads remapeados. to_json re-numera tanto quanto
    from_json — o round-trip é identidade.
    """
    return {
        "format": 1,
        "name": "Vendas",
        "nodes": [
            {"obj_id": 1, "kind": "entity", "name": "Cliente"},
            {
                "obj_id": 2,
                "kind": "attribute",
                "name": "cpf",
                "flags": {
                    "primary_key": True,
                    "multivalued": False,
                    "derived": False,
                    "partial_key": False,
                },
            },
            {"obj_id": 3, "kind": "attribute", "name": "nome"},
            {"obj_id": 4, "kind": "entity", "name": "Pedido"},
            {
                "obj_id": 5,
                "kind": "attribute",
                "name": "numero",
                "flags": {
                    "primary_key": True,
                    "multivalued": False,
                    "derived": False,
                    "partial_key": False,
                },
            },
            {"obj_id": 6, "kind": "relationship", "name": "Faz"},
        ],
        "edges": [
            {"obj_id": 7, "kind": "attributed_to", "tail": 2, "head": 1},
            {"obj_id": 8, "kind": "attributed_to", "tail": 3, "head": 1},
            {"obj_id": 9, "kind": "attributed_to", "tail": 5, "head": 4},
            {"obj_id": 10, "kind": "link", "tail": 6, "head": 1, "label": "1"},
            {"obj_id": 11, "kind": "link", "tail": 6, "head": 4, "label": "N"},
        ],
    }


def _vendas_reduzido() -> Diagram:
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    return Diagram("Vendas", elements=[Cliente, Pedido, Faz])


class TestToJson:
    def test_to_json_produz_o_dump_canonico_reduzido(self):
        diagrama = _vendas_reduzido()

        assert diagrama.to_json() == _vendas_reduzido_data()

    def test_to_json_omite_flags_quando_tudo_falso_e_label_quando_nulo(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()
            tele = Attribute(multivalued=True)

        diagrama = Diagram("V", elements=[Cliente])

        dump = diagrama.to_json()

        por_nome = {node["name"]: node for node in dump["nodes"]}
        assert "flags" not in por_nome["nome"]
        assert por_nome["tele"]["flags"]["multivalued"] is True
        assert all("label" not in e for e in dump["edges"] if e["kind"] == "attributed_to")

    def test_to_json_duas_chamadas_iguais_e_serializaveis_byte_a_byte(self):
        import json

        diagrama = _vendas_reduzido()

        primeira = json.dumps(diagrama.to_json())
        segunda = json.dumps(diagrama.to_json())

        assert primeira == segunda

    def test_to_json_parcial_e_total_vao_para_aresta(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N", total=True)

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        dump = diagrama.to_json()
        posicao = {node["name"]: node["obj_id"] for node in dump["nodes"]}
        links = [e for e in dump["edges"] if e["kind"] == "link"]

        por_head = {e["head"]: e for e in links}
        parcial = por_head[posicao["Cliente"]]
        total = por_head[posicao["Pedido"]]

        assert parcial["label"] == "1" and "total" not in parcial
        assert total["total"] is True


class TestFromJson:
    def test_from_json_lendo_a_propria_saida(self):
        dump = _vendas_reduzido_data()

        diagrama = Diagram.from_json(dump)

        assert diagrama.to_json() == dump

    def test_from_json_canonicaliza_ids_lacunados(self):
        dump = _vendas_reduzido_data()
        # produtor emitiu ids esparsos (+90) — referências consistentes, mas lacunadas
        for node in dump["nodes"]:
            node["obj_id"] += 90
        for edge in dump["edges"]:
            edge["tail"] += 90
            edge["head"] += 90
            edge["obj_id"] += 777

        diagrama = Diagram.from_json(dump)

        recanonic = diagrama.to_json()
        assert recanonic["nodes"][0]["obj_id"] == 1
        assert recanonic["edges"][0]["obj_id"] == 7
        # tail remapeado para a posição canônica do nó (cpf vira 2)
        assert recanonic["edges"][0]["tail"] == recanonic["nodes"][1]["obj_id"]

    def test_from_json_rejeita_atributo_sem_anexo_com_E01(self):
        import copy

        dump = _vendas_reduzido_data()
        quebrado = copy.deepcopy(dump)
        quebrado["edges"].pop(1)  # aresta nome→Cliente some (nome: sem flags)

        with pytest.raises(ValidationError, match="E01"):
            Diagram.from_json(quebrado)

    def test_from_json_rejeita_relacionamento_com_um_link_com_E05(self):
        import copy

        dump = _vendas_reduzido_data()
        quebrado = copy.deepcopy(dump)
        quebrado["edges"].pop()  # segundo link some

        with pytest.raises(ValidationError, match="E05"):
            Diagram.from_json(quebrado)


class TestRoundtripCompleto:
    def test_flags_entidade_fraca_e_composto_preservam_se(self):
        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Item(WeakEntity):
            do_pedido = Owner(Pedido)
            codigo = Attribute(partial_key=True)
            quantidade = Attribute()

        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            endereco = Composite(rua=Attribute(), cidade=Attribute())

        original = Diagram("V", elements=[Pedido, Item, Cliente])

        recarregado = Diagram.from_json(original.to_json())

        assert recarregado.to_json() == original.to_json()
        tipos = {node["kind"] for node in recarregado.to_json()["nodes"]}
        assert tipos == {"entity", "attribute", "weak_entity", "composite"}

    def test_from_json_de_arquivo_gerado_e_validado(self):
        dump = _vendas_reduzido_data()

        recarregado = Diagram.from_json(dump)

        assert recarregado.name == "Vendas"


class TestFormatoInvalido:
    """Malformação de payload é ValueError (não é regra E* — é formato)."""

    def test_formato_desconhecido(self):
        with pytest.raises(ValueError, match="format"):
            Diagram.from_json({"format": 2, "name": "V", "nodes": [], "edges": []})

    def test_kind_de_no_desconhecido(self):
        dump = _vendas_reduzido_data()
        dump["nodes"][0]["kind"] = "creature"

        with pytest.raises(ValueError, match="kind"):
            Diagram.from_json(dump)

    def test_kind_de_aresta_desconhecido(self):
        dump = _vendas_reduzido_data()
        dump["edges"][0]["kind"] = "vibes"

        with pytest.raises(ValueError, match="kind"):
            Diagram.from_json(dump)

    def test_aresta_referencia_no_inexistente(self):
        dump = _vendas_reduzido_data()
        dump["edges"][0]["tail"] = 404

        with pytest.raises(ValueError, match="unknown node obj_id"):
            Diagram.from_json(dump)


class TestNoKindDesconhecido:
    def test_node_kind_levanta_para_tipo_fora_do_modelo(self):
        from types import SimpleNamespace

        from chen.model.serialize import node_kind

        estranho = SimpleNamespace(name="?")

        with pytest.raises(ValueError, match="canonical kind"):
            node_kind(estranho)


class TestE04NoModeloCarregado:
    """O dono de um Owner deve ser fraco; o grafo carregado também obedece."""

    def test_owner_apontando_para_entidade_forta_levanta_E04(self):
        import copy

        dump = _vendas_reduzido_data()
        quebrado = copy.deepcopy(dump)
        # a aresta de anexo do nome vira dono: alguém "possui" a Cliente forte
        quebrado["edges"][1] = {"obj_id": 8, "kind": "owner", "tail": 4, "head": 1}

        with pytest.raises(ValidationError, match="E04"):
            Diagram.from_json(quebrado)

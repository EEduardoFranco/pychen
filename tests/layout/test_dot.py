"""Camada layout (spec §7): model → DOT → `dot -Tjson` → posições.

Regras testadas:
- `to_dot` produz texto determinístico e escapado (nós `n{obj_id}`, labels entre aspas).
- `compute_layout` devolve posições {x, y, w, h} em px SVG com o eixo Y flipado.
- Determinismo byte a byte também vale para o layout.
"""

import shutil

import pytest

from chen.layout.dot import DotNotFound, compute_layout, to_dot
from chen.model import Attribute, Diagram, Entity, Link, Relationship

pytestmark = [
    pytest.mark.requires_dot,
    pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz `dot` not found in PATH"),
]


def _vendas_diagrama():
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    return Diagram("Vendas", elements=[Cliente, Pedido, Faz])


# O diagrama de vendas (Cliente(cpf, nome) + Pedido(numero) + Faz(1, N))
# têm ids determinísticos e NÃO densos: nós e arestas dividem a mesma sequência
# (spec §5). Nós: 1=Cliente, 2=cpf, 4=nome, 6=Pedido, 7=numero, 9=Faz.
def _expected_dot_texto() -> str:
    return (
        'graph "Vendas" {\n'
        '  n1 [label="Cliente"];\n'
        '  n2 [label="cpf"];\n'
        '  n4 [label="nome"];\n'
        '  n6 [label="Pedido"];\n'
        '  n7 [label="numero"];\n'
        '  n9 [label="Faz"];\n'
        "  n2 -- n1;\n"
        "  n4 -- n1;\n"
        "  n7 -- n6;\n"
        '  n9 -- n1 [label="1"];\n'
        '  n9 -- n6 [label="N"];\n'
        "}\n"
    )


class TestToDot:
    def test_to_dot_produz_texto_exato_e_deterministico(self):
        diagrama = _vendas_diagrama()

        texto = to_dot(diagrama)

        assert texto == _expected_dot_texto()
        assert to_dot(diagrama) == texto


class TestComputeLayout:
    def test_layout_cobre_todos_os_nos_com_dimensoes_positivas(self):
        diagrama = _vendas_diagrama()

        layout = compute_layout(diagrama)

        assert set(layout.nodes) == {n.obj_id for n in diagrama.nodes}
        assert layout.width > 0 and layout.height > 0
        for geom in layout.nodes.values():
            assert geom.width > 0 and geom.height > 0

    def test_eixo_y_e_flipado_para_o_espaco_svg(self):
        import json
        import subprocess

        from chen.layout.dot import _resolve_dot, to_dot

        diagrama = _vendas_diagrama()
        raw = subprocess.run(
            [_resolve_dot(), "-Tjson"],
            input=to_dot(diagrama).encode("utf-8"),
            capture_output=True,
            check=True,
        )
        data = json.loads(raw.stdout.decode("utf-8"))
        ymax = float(data["bb"].split(",")[3])

        layout = compute_layout(diagrama)

        # regra da spec: y_svg = ymax - y, para todo nó — independente do ranking
        for obj in data["objects"]:
            node_y = float(obj["pos"].split(",")[1])
            obj_id = int(obj["name"][1:])
            assert layout.nodes[obj_id].y == pytest.approx(ymax - node_y)

    def test_arestas_de_link_carregam_label_e_posicao(self):
        diagrama = _vendas_diagrama()

        layout = compute_layout(diagrama)

        todas = [g for lst in layout.edges.values() for g in lst]
        labels = {g.label for g in todas if g.label}
        assert labels == {"1", "N"}
        for g in todas:
            assert len(g.points) >= 2
            if g.label:
                assert g.label_x > 0 and g.label_y > 0

    def test_dois_calculos_sucessivos_sao_byte_a_byte(self):
        diagrama = _vendas_diagrama()

        assert compute_layout(diagrama) == compute_layout(diagrama)


class TestParticipacaoTotal:
    def test_aresta_carrega_a_participacao_total_do_modelo(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N", total=True)

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        layout = compute_layout(diagrama)

        por_par = {(tail, head): geoms for (tail, head), geoms in layout.edges.items()}
        pedido = [n for n in diagrama.nodes if n.name == "Pedido"][0]
        [geom_total] = [
            geom
            for (tail, head), geoms in por_par.items()
            if head == pedido.obj_id
            for geom in geoms
            if geom.label is not None
        ]

        assert geom_total.total is True


class TestDotNaoEncontrado:
    def test_dot_ausente_levanta_DotNotFound(self, monkeypatch):
        from chen.layout import dot

        monkeypatch.setattr(dot, "_resolve_dot", lambda: None)

        with pytest.raises(DotNotFound, match="graphviz.org/download"):
            dot.compute_layout(_vendas_diagrama())

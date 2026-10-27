"""test_shapes — conceito do modelo → fragmento + parâmetros (spec §7–§8).

Regras:
- cada conceito sabe o seu fragmento e o seu conjunto de parâmetros;
- números do SVG saem sempre formatados com duas casas (determinismo byte a byte);
- losango → polígono; aresta → path; label → fragmento próprio.
"""

from chen.layout.dot import EdgeGeom, NodeGeom
from chen.render.shapes import attribute, edge, entity, relationship, weak_entity


class TestEntity:
    def test_entidade_vira_o_fragmento_Entity_com_retangulo_acima_da_esquerda(self):
        fragmento, params = entity(NodeGeom(x=50.0, y=40.0, width=80.0, height=20.0), "Cliente")

        assert fragmento == "Entity.svg"
        assert params == {
            "x": "10.00",  # topo-esquerda: centro − w/2
            "y": "30.00",  # centro − h/2
            "w": "80.00",
            "h": "20.00",
            "cx": "50.00",
            "cy": "40.00",
            "text": "Cliente",
        }


class TestRelationship:
    def test_relacionamento_vira_losango_com_quatro_pontos(self):
        fragmento, params = relationship(NodeGeom(x=50.0, y=40.0, width=60.0, height=30.0), "Faz")

        assert fragmento == "Relationship.svg"
        assert params["points"] == "20.00,40.00 50.00,25.00 80.00,40.00 50.00,55.00"
        assert params["cx"] == "50.00" and params["cy"] == "40.00"
        assert params["text"] == "Faz"


class TestAttribute:
    def test_atributo_simples_usa_o_fragmento_Attribute(self):
        fragmento, params = attribute(
            NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "nome", variant="simple"
        )

        assert fragmento == "Attribute.svg"
        assert params == {
            "x": "20.00",
            "y": "10.00",
            "rx": "15.00",
            "ry": "6.00",
            "text": "nome",
        }

    def test_atributo_chave_usa_o_fragmento_Attribute_key(self):
        fragmento, _ = attribute(
            NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "cpf", variant="key"
        )

        assert fragmento == "Attribute_key.svg"


class TestEdge:
    def test_aresta_vira_path_com_os_pontos_da_spline(self):
        fragmentos = [fragment for fragment, _ in edge(EdgeGeom(points=((0.0, 0.0), (10.0, 10.5))))]

        assert fragmentos == ["Edge.svg"]

    def test_path_d_formata_numeros_com_duas_casas(self):
        _, params = edge(EdgeGeom(points=((0.0, 0.0), (10.0, 10.5))))[0]

        assert params["d"] == "M 0.00,0.00 L 10.00,10.50"

    def test_aresta_com_label_gera_fragmento_de_label_com_a_sua_posicao(self):
        geometria = EdgeGeom(points=((0.0, 0.0), (10.0, 10.0)), label="1", label_x=5.0, label_y=2.5)

        fragmentos = edge(geometria)
        (_, params_path), (fragmento_label, params_label) = fragmentos

        assert fragmento_label == "EdgeLabel.svg"
        assert params_label == {"x": "5.00", "y": "2.50", "text": "1"}
        assert params_path["d"] == "M 0.00,0.00 L 10.00,10.00"

    def test_aresta_total_vira_linha_dupla(self):
        geometria = EdgeGeom(points=((0.0, 0.0), (10.0, 10.5)), total=True)

        [(fragmento, params)] = edge(geometria)

        assert fragmento == "EdgeDouble.svg"
        assert params["d"] == "M 0.00,0.00 L 10.00,10.50"


class TestWeakEntity:
    def test_entidade_fraca_vira_o_fragmento_WeakEntity_com_retangulo_interno(self):
        fragmento, params = weak_entity(
            NodeGeom(x=50.0, y=40.0, width=80.0, height=20.0), "ItemPedido"
        )

        assert fragmento == "WeakEntity.svg"
        # retângulo externo e interno afastado 3px nas quatro bordas
        assert params["x"] == "10.00" and params["y"] == "30.00"
        assert params["w"] == "80.00" and params["h"] == "20.00"
        assert params["x2"] == "13.00" and params["y2"] == "33.00"
        assert params["w2"] == "74.00" and params["h2"] == "14.00"
        assert params["cx"] == "50.00" and params["cy"] == "40.00"
        assert params["text"] == "ItemPedido"


class TestVarianteMultivaloradaEOutras:
    def test_variantes_novas_apontam_o_seu_fragmento(self):
        geometria = NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0)

        assert attribute(geometria, "tel", variant="multivalued")[0] == "Attribute_multivalued.svg"
        assert attribute(geometria, "tel", variant="derived")[0] == "Attribute_derived.svg"
        assert attribute(geometria, "tel", variant="partial_key")[0] == "Attribute_partial_key.svg"

    def test_multivalorado_calcula_a_elipse_interna(self):
        _, params = attribute(
            NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "tel", variant="multivalued"
        )

        assert params["rx"] == "15.00" and params["ry"] == "6.00"
        assert params["rx2"] == "12.00" and params["ry2"] == "3.00"

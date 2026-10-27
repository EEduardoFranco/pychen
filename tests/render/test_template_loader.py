"""test_template_loader — carregamento de fragmentos SVG (spec §8) e escape de texto."""

from pychen.render.template_loader import TEMPLATES_DIR, Template


class TestCarregamento:
    def test_templates_vivem_na_raiz_do_repositorio(self):
        assert TEMPLATES_DIR.name == "templates"

    def test_carrega_fragmento_e_descobre_placeholders(self):
        template = Template("Entity.svg")

        template.load()

        assert set(template.placeholders) == {"x", "y", "w", "h", "cx", "cy", "text"}


class TestRender:
    def test_render_substitui_todos_os_placeholders(self):
        template = Template("Entity.svg")
        template.load()

        fragmento = template.render(
            {
                "x": "10.00",
                "y": "20.00",
                "w": "80.00",
                "h": "40.00",
                "cx": "50.00",
                "cy": "40.00",
                "text": "Cliente",
            }
        )

        assert 'x="10.00"' in fragmento
        assert "Cliente" in fragmento
        assert "{%" not in fragmento

    def test_render_escapa_texto_do_usuario(self):
        template = Template("Entity.svg")
        template.load()

        fragmento = template.render(
            {
                "x": "0",
                "y": "0",
                "w": "1",
                "h": "1",
                "cx": "0",
                "cy": "0",
                "text": 'a&b<c>"d"',
            }
        )

        assert "a&amp;b" in fragmento
        assert "&lt;" in fragmento
        assert "&gt;" in fragmento
        assert "&quot;" in fragmento
        assert "a&b" not in fragmento

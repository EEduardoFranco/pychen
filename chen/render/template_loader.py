"""Carregador de fragmentos SVG (spec §8).

Cada arquivo em `templates/` é um fragmento `<g>`, não um documento: o documento
raiz é gerado pelo composer. Placeholders são descobertos por regex e preenchidos
por substituição pura — nenhum valor entra por `format` — e TODO texto que
representa conteúdo do usuário é escapado (`&`, `<`, `>`, `"`).
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

PLACEHOLDER = re.compile(r"{%(\w+)%}")


def escape_text(value: str) -> str:
    """Escapa o texto para o XML do SVG: `&`, `<`, `>`, `"`."""
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


class Template:
    def __init__(self, filename: str) -> None:
        self.path = TEMPLATES_DIR / filename
        self.content: str = ""

    def load(self) -> None:
        self.content = self.path.read_text(encoding="utf-8")

    @property
    def placeholders(self) -> set[str]:
        return set(PLACEHOLDER.findall(self.content))

    def render(self, parameters: dict[str, str]) -> str:
        """Substitui os placeholders pelos valores, escapando cada texto."""
        result = self.content
        for name, value in parameters.items():
            result = result.replace("{%" + name + "%}", escape_text(value))
        return result

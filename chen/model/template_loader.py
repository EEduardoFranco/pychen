"""Carregador de templates SVG (stub migrado do protótipo).

Evolução planejada (seção 8 da spec): carregar fragmento, descobrir placeholders
por regex `{%(\\w+)%}` e preencher com texto escapado (`&`, `<`, `>`, `"`).
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


class Template:
    def __init__(self, filename: str) -> None:
        self.path = TEMPLATES_DIR / filename
        self.parameters: dict[str, str] = {}
        self.content: str = ""

    def load(self) -> None:
        with self.path.open("r", encoding="utf-8") as arq:
            self.content = arq.read()
        # TODO: usar regex para determinar as variáveis que o template precisa

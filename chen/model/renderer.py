"""Renderização (stub migrado do protótipo; evolui para fragmentos SVG — seção 8)."""


class TextRectangle:
    def __init__(self, text: str) -> None:
        self.text = text

    def to_svg(self) -> str:
        raise NotImplementedError

"""Erros do projeto (mensagens em inglês — convenções da seção 12 da spec)."""


class ChenError(Exception):
    """Base de todos os erros do pychen."""


class ValidationError(ChenError):
    """Violação de notação de Chen, com id (E01–E08), mensagem e elemento culpado."""

    def __init__(self, rule_id: str, message: str) -> None:
        self.rule_id = rule_id
        self.message = message
        super().__init__(f"{rule_id}: {message}")


class DotNotFound(ChenError):
    """Executável `dot` do Graphviz não encontrado no PATH (instrução de instalar
    é dada em detalhes pelo M3 — seção 10 da spec)."""

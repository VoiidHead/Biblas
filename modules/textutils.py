"""Funções utilitárias de texto: normalização para comparação e formatação de dinheiro."""

from unicodedata import combining, normalize


def fold(text: str):
    """Normaliza um texto para comparação.

    Remove espaços nas pontas, acentos e diferença de maiúsculas/minúsculas.
    Ex.: fold('  José ') == fold('jose').

    Args:
        text: Texto a normalizar.

    Returns:
        Texto normalizado.
    """
    decomposed = normalize("NFKD", text.strip())
    return "".join(character for character in decomposed if not combining(character)).casefold()


def format_money(cents: int):
    """Formata um valor em centavos no padrão monetário brasileiro.

    Ex.: format_money(123456) devolve 'R$ 1.234,56'.

    Args:
        cents: Valor em centavos.

    Returns:
        Texto com símbolo, ponto como separador de milhar e vírgula nos centavos.
    """
    reais, remainder = divmod(cents, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{remainder:02d}"

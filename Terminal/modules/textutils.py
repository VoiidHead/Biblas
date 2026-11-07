from unicodedata import combining, normalize


def fold(text: str):
    decomposed = normalize("NFKD", text.strip())
    return "".join(character for character in decomposed if not combining(character)).casefold()


def format_money(cents: int):
    reais, remainder = divmod(cents, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{remainder:02d}"

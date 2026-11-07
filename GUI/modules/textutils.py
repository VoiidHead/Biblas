from datetime import date
from unicodedata import combining, normalize


def fold(text: str):
    decomposed = normalize("NFKD", text.strip())
    return "".join(character for character in decomposed if not combining(character)).casefold()


def format_money(cents: int):
    reais, remainder = divmod(cents, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{remainder:02d}"


def format_decimal(cents: int):
    reais, remainder = divmod(cents, 100)
    return f"{reais},{remainder:02d}"


def format_date(value: date | str):
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return f"{value:%d/%m/%Y}"


def format_cpf(cpf: str):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def year_text(year: int):
    return f"{abs(year)} AEC" if year < 0 else str(year)


def pluralize(count: int, singular: str, plural: str):
    return plural if count > 1 else singular

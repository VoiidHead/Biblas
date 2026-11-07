from re import fullmatch

from modules.errors import BiblasError
from modules.masks import only_digits
from modules.models import GENDERS
from modules.rules import is_valid_cpf

MAX_MONEY_CENTS = 10_000_000  # R$ 100.000,00


def clean(text: str | None):
    return (text or "").strip()


def required_text(text: str | None):
    value = clean(text)
    if not value:
        raise BiblasError("Este campo não pode ficar vazio")
    return value


def parse_int(text: str | None):
    required_text(text)
    try:
        return int(clean(text))
    except ValueError:
        raise BiblasError("Isso não é um número") from None


def parse_id(text: str | None):
    required_text(text)
    try:
        value = int(clean(text))
    except ValueError:
        raise BiblasError("Isso não é um ID") from None
    if value < 0:
        raise BiblasError("Número inválido")
    return value


def parse_positive_int(text: str | None):
    value = parse_int(text)
    if value <= 0:
        raise BiblasError("O valor precisa ser maior que zero")
    return value


def parse_year(text: str | None):
    value = parse_int(text)
    if value == 0:
        raise BiblasError("O ano 0 não existe")
    return value


def parse_username(text: str | None):
    return required_text(text).casefold()


def parse_password(text: str | None):
    value = clean(text)
    if not value:
        raise BiblasError("A senha não pode ficar vazia")
    return value


def parse_email(text: str | None):
    email = clean(text).casefold()
    if not fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise BiblasError("E-mail inválido")
    return email


def parse_cpf(text: str | None):
    cpf = only_digits(text)
    if not is_valid_cpf(cpf):
        raise BiblasError("CPF inválido")
    return cpf


def parse_gender(value: str | None):
    if value not in GENDERS:
        raise BiblasError("Escolha uma opção")
    return value


def parse_money(text: str | None):
    required_text(text)
    text = clean(text).replace("R$", "").strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    if not fullmatch(r"[0-9]+(\.[0-9]{1,2})?", text):
        raise BiblasError("Valor inválido. Exemplo: 1,50")
    integer, _, decimals = text.partition(".")
    cents = int(integer) * 100 + int(decimals.ljust(2, "0") or 0)
    if cents == 0:
        raise BiblasError("O valor precisa ser maior que zero")
    if cents > MAX_MONEY_CENTS:
        raise BiblasError("Valor muito alto")
    return cents

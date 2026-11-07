from getpass import getpass
from re import fullmatch

from modules.models import GENDERS
from modules.rules import is_valid_cpf
from modules.textutils import fold


def read_natural_number(message: str, isID: bool = False):
    while True:
        try:
            value = int(input(message))
            if value < 0:
                print("Número inválido")
                continue
            return value
        except ValueError:
            if not isID:
                print("Isso não é um número")
            else:
                print("Isso não é um ID")


def read_positive_int(message: str):
    value = read_natural_number(message)
    while value == 0:
        print("O valor precisa ser maior que zero")
        value = read_natural_number(message)
    return value


def read_text(message: str):
    text = input(message).strip()
    while not text:
        print("Este campo não pode ficar vazio")
        text = input(message).strip()
    return text


def read_year(message: str):
    while True:
        try:
            value = int(input(message))
        except ValueError:
            print("Isso não é um número")
            continue
        if value == 0:
            print("O ano 0 não existe")
            continue
        return value


def read_password(message: str):
    password = getpass(message).strip()
    while not password:
        print("A senha não pode ficar vazia")
        password = getpass(message).strip()
    return password


def read_email(message: str):
    while True:
        email = input(message).strip().casefold()
        if fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return email
        print("E-mail inválido")


def read_cpf(message: str):
    while True:
        cpf = "".join(character for character in input(message) if character.isdigit())
        if is_valid_cpf(cpf):
            return cpf
        print("CPF inválido")


def read_gender(message: str):
    numberedGenders = {str(number): gender for number, gender in enumerate(GENDERS, start=1)}
    optionsText = "\n".join(f"{number} - {GENDERS[gender].capitalize()}" for number, gender in numberedGenders.items())
    while True:
        selection = input(f"{message}\n{optionsText}\n").strip()
        if selection in numberedGenders:
            return numberedGenders[selection]
        print("Opção inválida")


def read_yes_no(message: str):
    while True:
        answer = fold(input(message))
        if answer in ("s", "sim"):
            return True
        if answer in ("n", "nao"):
            return False
        print("Resposta inválida. Digite s ou n")


def read_option(message: str, options: tuple):
    while True:
        selection = input(message).strip().casefold()
        if selection in options:
            return selection
        print("Opção inválida")


def read_positive_int_or_keep(message: str, current: int):
    while True:
        text = input(message).strip()
        if not text:
            return current
        try:
            value = int(text)
        except ValueError:
            print("Isso não é um número")
            continue
        if value > 0:
            return value
        print("O valor precisa ser maior que zero")


MAX_MONEY_CENTS = 10_000_000  # R$ 100.000,00


def read_money(message: str, default: int | None = None):
    while True:
        text = input(message).strip().replace("R$", "").strip()
        if not text and default is not None:
            return default
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        if not fullmatch(r"[0-9]+(\.[0-9]{1,2})?", text):
            print("Valor inválido. Exemplo: 1,50")
            continue
        integer, _, decimals = text.partition(".")
        cents = int(integer) * 100 + int(decimals.ljust(2, "0") or 0)
        if cents == 0:
            print("O valor precisa ser maior que zero")
        elif cents > MAX_MONEY_CENTS:
            print("Valor muito alto")
        else:
            return cents

from modules.errors import BiblasError
from modules.models import User, hash_password
from modules.rules import by_gender, pending_fines
from modules.state import (
    find_user_by_cpf, find_user_by_email, find_user_by_name, loanHistory, new_user_id, save_data, users,
)
from modules.storage import HISTORY_FILE, USERS_FILE


def check_username_free(username: str, current: User | None = None):
    owner = find_user_by_name(username)
    if owner and owner is not current:
        raise BiblasError(f"Nome de usuário em uso (conflita com '{owner.name}')")


def check_cpf_free(cpf: str, current: User | None = None):
    owner = find_user_by_cpf(cpf)
    if owner and owner is not current:
        raise BiblasError(f"CPF já cadastrado para o usuário '{owner.name}'")


def check_email_free(email: str, current: User | None = None):
    owner = find_user_by_email(email)
    if owner and owner is not current:
        raise BiblasError(f"E-mail já cadastrado para o usuário '{owner.name}'")


def add_user(username: str, gender: str, email: str, cpf: str, password: str):
    check_username_free(username)
    check_email_free(email)
    check_cpf_free(cpf)
    user = User(new_user_id(), username, gender, email, cpf, hash_password(password))
    users.append(user)
    save_data(USERS_FILE)
    return user


def edit_user(user: User, newUsername: str | None = None, gender: str | None = None,
              cpf: str | None = None, password: str | None = None, email: str | None = None):
    if all(value is None for value in (newUsername, gender, cpf, password, email)):
        raise BiblasError("Nenhuma alteração informada")

    if newUsername is not None:
        check_username_free(newUsername, current=user)
    if cpf is not None:
        check_cpf_free(cpf, current=user)
    if email is not None:
        check_email_free(email, current=user)

    if newUsername is not None:
        user.name = newUsername
    if gender is not None:
        user.gender = gender
    if cpf is not None:
        user.cpf = cpf
    if email is not None:
        user.email = email
    if password is not None:
        user.change_password(password)

    save_data(USERS_FILE)


def pay_fines(user: User):
    fines = pending_fines(user.id, loanHistory)
    if not fines:
        raise BiblasError("Nenhuma multa pendente")

    total = sum(loan.fine_cents for loan in fines)
    for loan in fines:
        loan.fine_paid = True
    save_data(HISTORY_FILE)
    return total


def reset_faults(user: User):
    if user.faults == 0:
        raise BiblasError(f"{by_gender(user, 'A usuária', 'O usuário')} não tem faltas")

    user.faults = 0
    save_data(USERS_FILE)

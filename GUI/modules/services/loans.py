from datetime import date, timedelta

from modules.errors import BiblasError
from modules.models import Copy, Loan, User
from modules.rules import by_gender, days_late, fine_for, is_banned, open_loans, suspend, suspension_end
from modules.state import (
    active_loan, config, find_copy, find_title, find_user, find_user_by_name, loanHistory, save_data,
)
from modules.storage import HISTORY_FILE, USERS_FILE
from modules.textutils import format_date, format_money, pluralize


def close_loan(loan: Loan, wasRemoved: bool = False):
    loan.return_date = date.today().isoformat()
    loan.was_removed = wasRemoved
    lateDays = days_late(loan)
    changedFiles = [HISTORY_FILE]
    messages = []

    user = find_user(loan.user_id)
    if lateDays and user:
        actionName = "Remoção" if wasRemoved else "Devolução"
        messages.append(f"{actionName} com {lateDays} {pluralize(lateDays, 'dia', 'dias')} de atraso.")

        wasBanned = is_banned(user, config)
        user.faults += 1

        if config['late_penalty'] == 'fine':
            loan.fine_cents = fine_for(lateDays, config)
            messages.append(f"Multa: {format_money(loan.fine_cents)} "
                            f"({lateDays} x {format_money(config['fine_per_day_cents'])})")
        else:
            suspensionEnd = suspend(user, lateDays)
            messages.append(f"{user.name} não poderá fazer empréstimos até {format_date(suspensionEnd)}")

        if not wasBanned and is_banned(user, config):
            messages.append(f"{user.name} chegou a {user.faults} faltas e foi {by_gender(user, 'banida', 'banido')} "
                            f"da biblioteca. Novos empréstimos estão bloqueados")
        changedFiles.append(USERS_FILE)

    return messages, changedFiles


def check_user_can_borrow(user: User):
    if is_banned(user, config):
        raise BiblasError(f"{by_gender(user, 'Usuária banida', 'Usuário banido')} da biblioteca "
                          f"({user.faults} faltas). Empréstimos bloqueados")

    suspensionEnd = suspension_end(user)
    if suspensionEnd:
        raise BiblasError(f"{by_gender(user, 'Usuária suspensa', 'Usuário suspenso')} de empréstimos "
                          f"até {format_date(suspensionEnd)}")

    userLoans = open_loans(user.id, loanHistory)

    if any(days_late(loan) > 0 for loan in userLoans):
        raise BiblasError(f"{by_gender(user, 'Usuária', 'Usuário')} tem livro atrasado. "
                          f"Devolva antes de pegar outro")

    maxLoans = config['max_loans']
    if len(userLoans) >= maxLoans:
        raise BiblasError(f"Limite de {maxLoans} {pluralize(maxLoans, 'livro', 'livros')} por usuário atingido")


def check_copy_available(copy: Copy):
    if active_loan(copy):
        raise BiblasError("Esse livro já foi emprestado")


def check_copy_borrowed(copy: Copy):
    if not active_loan(copy):
        raise BiblasError("Esse livro não estava emprestado")


def borrow(copyId: int, username: str, password: str):
    user = find_user_by_name(username)
    if not user:
        raise BiblasError("Usuário não encontrado")

    if not user.check_password(password):
        raise BiblasError("Senha incorreta")

    check_user_can_borrow(user)

    copy = find_copy(copyId)
    if not copy:
        raise BiblasError("Livro não encontrado")

    check_copy_available(copy)

    loanDate = date.today()
    dueDate = loanDate + timedelta(days=config['loan_days'])
    loanHistory.append(Loan(copy.id, copy.title_id, find_title(copy.title_id).name, user.id,
                            loanDate.isoformat(), dueDate.isoformat()))
    save_data(HISTORY_FILE)
    return dueDate


def give_back(copyId: int):
    copy = find_copy(copyId)
    if not copy:
        raise BiblasError("Livro não encontrado")

    check_copy_borrowed(copy)

    messages, changedFiles = close_loan(active_loan(copy))
    save_data(*changedFiles)
    return messages

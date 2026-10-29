"""Serviços de empréstimo: retirada e devolução de exemplares, com as punições por atraso."""

from datetime import date, timedelta

from modules.models import Loan
from modules.rules import by_gender, days_late, fine_for, is_banned, suspend, suspension_end
from modules.state import (
    active_loan, config, find_copy, find_title, find_user, find_user_by_name, loanHistory, save_data,
)
from modules.storage import HISTORY_FILE, USERS_FILE
from modules.textutils import format_money


def close_loan(loan: Loan, wasRemoved: bool = False):
    """Encerra um empréstimo e aplica a punição por atraso, se houver.

    Marca a data de devolução como hoje. Se estava atrasado, conta uma falta
    para o usuário e aplica a punição configurada (multa ou suspensão), avisando
    na tela inclusive quando a falta leva ao banimento. Não grava em disco:
    quem chama deve passar o resultado para save_data.

    Args:
        loan: Empréstimo a encerrar.
        wasRemoved: True se o encerramento é causado pela remoção do exemplar
            do acervo, e não por uma devolução.

    Returns:
        Lista dos arquivos alterados: sempre o histórico e, se houve punição,
        também o de usuários.
    """
    loan.return_date = date.today().isoformat()
    loan.was_removed = wasRemoved
    lateDays = days_late(loan)
    changedFiles = [HISTORY_FILE]

    user = find_user(loan.user_id)
    if lateDays and user:
        actionName = "Remoção" if wasRemoved else "Devolução"
        dayWord = "dias" if lateDays > 1 else "dia"
        print(f"{actionName} com {lateDays} {dayWord} de atraso.")

        wasBanned = is_banned(user, config)
        user.faults += 1

        if config['late_penalty'] == 'fine':
            loan.fine_cents = fine_for(lateDays, config)
            print(f"Multa: {format_money(loan.fine_cents)} "
                  f"({lateDays} x {format_money(config['fine_per_day_cents'])})\n")
        else:
            suspensionEnd = suspend(user, lateDays)
            print(f"{user.name} não poderá fazer empréstimos até {suspensionEnd:%d/%m/%Y}\n")

        if not wasBanned and is_banned(user, config):
            print(f"{user.name} chegou a {user.faults} faltas e foi {by_gender(user, 'banida', 'banido')} "
                  f"da biblioteca. Novos empréstimos estão bloqueados\n")
        changedFiles.append(USERS_FILE)

    return changedFiles


def borrow(copyId: int, username: str, password: str):
    """Registra o empréstimo de um exemplar a um usuário.

    Verifica, nesta ordem: se o usuário existe, se a senha confere, se não
    está banido nem suspenso, se não tem livro atrasado, se não atingiu o
    limite de empréstimos, se o exemplar existe e se está disponível. Ao
    primeiro problema, avisa na tela e não registra nada. Se tudo estiver
    certo, grava o empréstimo com prazo de loan_days e mostra a data máxima.

    Args:
        copyId: ID do exemplar.
        username: Nome do usuário.
        password: Senha do usuário.
    """
    user = find_user_by_name(username)
    if not user:
        print("Usuário não encontrado")
        return

    if not user.check_password(password):
        print("Senha incorreta\n")
        return

    isFemale = user.gender == "female"

    if is_banned(user, config):
        print(f"{by_gender(user, 'Usuária banida', 'Usuário banido')} da biblioteca "
              f"({user.faults} faltas). Empréstimos bloqueados\n")
        return

    suspensionEnd = suspension_end(user)
    if suspensionEnd:
        userWord = "Usuária suspensa" if isFemale else "Usuário suspenso"
        print(f"{userWord} de empréstimos até {suspensionEnd:%d/%m/%Y}\n")
        return

    userLoans = [loan for loan in loanHistory if loan.user_id == user.id and loan.return_date is None]

    if any(days_late(loan) > 0 for loan in userLoans):
        userWord = "Usuária" if isFemale else "Usuário"
        print(f"{userWord} tem livro atrasado. Devolva antes de pegar outro\n")
        return

    maxLoans = config['max_loans']
    if len(userLoans) >= maxLoans:
        bookWord = "livros" if maxLoans > 1 else "livro"
        print(f"Limite de {maxLoans} {bookWord} por usuário atingido\n")
        return

    copy = find_copy(copyId)
    if not copy:
        print("Livro não encontrado\n")
        return

    if active_loan(copy):
        print("Esse livro já foi emprestado\n")
        return

    loanDate = date.today()
    dueDate = loanDate + timedelta(days=config['loan_days'])
    loanHistory.append(Loan(copy.id, copy.title_id, find_title(copy.title_id).name, user.id,
                            loanDate.isoformat(), dueDate.isoformat()))
    save_data(HISTORY_FILE)
    print(f"Data máxima de devolução: {dueDate:%d/%m/%Y}\n")


def give_back(copyId: int):
    """Registra a devolução de um exemplar.

    Avisa na tela se o exemplar não existe ou não estava emprestado. Caso
    contrário encerra o empréstimo (com punição, se atrasado) e grava.

    Args:
        copyId: ID do exemplar devolvido.
    """
    copy = find_copy(copyId)
    if not copy:
        print("Livro não encontrado\n")
        return

    loan = active_loan(copy)
    if not loan:
        print("Esse livro não estava emprestado\n")
        return

    save_data(*close_loan(loan))

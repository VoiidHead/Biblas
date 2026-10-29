"""Regras de negócio da biblioteca: atrasos, suspensões, banimento, multas e CPF.

As funções daqui apenas calculam e decidem. Não leem do teclado nem gravam
em disco (quem muda um objeto precisa depois chamar save_data).
"""

from datetime import date, timedelta

from modules.models import Loan, User
from modules.textutils import format_money


def days_late(loan: Loan):
    """Calcula quantos dias um empréstimo está (ou ficou) atrasado.

    Se já foi devolvido, conta até a data de devolução; se não, até hoje.

    Args:
        loan: Empréstimo a analisar.

    Returns:
        Dias de atraso, nunca negativo (0 se estiver no prazo).
    """
    endDate = date.fromisoformat(loan.return_date) if loan.return_date else date.today()
    return max(0, (endDate - date.fromisoformat(loan.due_date)).days)


def loan_status(loan: Loan):
    """Descreve a situação de um empréstimo em texto.

    Args:
        loan: Empréstimo a descrever.

    Returns:
        'em andamento', 'devolvido em DD/MM/AAAA' ou 'removido do acervo em DD/MM/AAAA'.
    """
    if loan.return_date is None:
        return "em andamento"
    action = "removido do acervo" if loan.was_removed else "devolvido"
    return f"{action} em {date.fromisoformat(loan.return_date):%d/%m/%Y}"


def loan_summary(loan: Loan):
    """Monta a linha de resumo de um empréstimo para exibição.

    Inclui data do empréstimo, data máxima, situação, atraso (se houver) e
    multa (se houver, indicando se está paga ou pendente).

    Args:
        loan: Empréstimo a resumir.

    Returns:
        Texto com os campos separados por ' | '.
    """
    loanDate = date.fromisoformat(loan.loan_date)
    dueDate = date.fromisoformat(loan.due_date)
    lateDays = days_late(loan)
    dayWord = "dias" if lateDays > 1 else "dia"
    text = f"emprestado em {loanDate:%d/%m/%Y} | data máxima de devolução: {dueDate:%d/%m/%Y} | {loan_status(loan)}"
    if lateDays and loan.return_date is None:
        text += f" (ATRASADO há {lateDays} {dayWord})"
    elif lateDays:
        text += f" ({lateDays} {dayWord} de atraso)"
    if loan.fine_cents:
        text += f" | multa: {format_money(loan.fine_cents)} ({'paga' if loan.fine_paid else 'pendente'})"
    return text


def suspension_end(user: User):
    """Devolve o fim da suspensão do usuário, se ela ainda estiver valendo.

    Args:
        user: Usuário a consultar.

    Returns:
        Data de fim da suspensão se for posterior a hoje; None se o usuário não
        tem suspensão ou ela já terminou.
    """
    if user.suspended_until and date.fromisoformat(user.suspended_until) > date.today():
        return date.fromisoformat(user.suspended_until)
    return None


def suspend(user: User, days: int):
    """Suspende o usuário por um número de dias.

    Se já houver suspensão vigente, os dias são somados ao fim dela; senão,
    contam a partir de hoje. Altera user.suspended_until, mas não grava em disco.

    Args:
        user: Usuário a suspender.
        days: Quantidade de dias a acrescentar.

    Returns:
        Nova data de fim da suspensão.
    """
    startDate = suspension_end(user) or date.today()
    endDate = startDate + timedelta(days=days)
    user.suspended_until = endDate.isoformat()
    return endDate


def by_gender(user: User, feminine: str, masculine: str):
    """Escolhe entre a forma feminina e a masculina de uma palavra.

    Args:
        user: Usuário cujo gênero decide a flexão.
        feminine: Texto usado se o gênero for 'female'.
        masculine: Texto usado nos demais casos ('male' e 'other').

    Returns:
        O texto correspondente ao gênero.
    """
    return feminine if user.gender == "female" else masculine


def is_banned(user: User, config: dict):
    """Indica se o usuário está banido pelas regras atuais.

    Args:
        user: Usuário a verificar.
        config: Configuração do sistema (usa ban_enabled e ban_after_faults).

    Returns:
        True se o banimento está ativado e o usuário atingiu o limite de faltas.
    """
    return config['ban_enabled'] and user.faults >= config['ban_after_faults']


def fine_for(lateDays: int, config: dict):
    """Calcula o valor da multa por atraso.

    Args:
        lateDays: Dias de atraso.
        config: Configuração do sistema (usa fine_per_day_cents).

    Returns:
        Valor da multa em centavos.
    """
    return lateDays * config['fine_per_day_cents']


def pending_fines(userId: int, history: list):
    """Lista os empréstimos de um usuário com multa ainda não paga.

    Args:
        userId: ID do usuário.
        history: Lista de empréstimos onde procurar.

    Returns:
        Empréstimos com multa maior que zero e não quitada.
    """
    return [loan for loan in history if loan.user_id == userId and loan.fine_cents and not loan.fine_paid]


def is_valid_cpf(cpf: str):
    """Valida um CPF pelo tamanho e pelos dois dígitos verificadores.

    Rejeita CPFs com todos os dígitos iguais (ex.: 11111111111). Pressupõe
    que a entrada já foi reduzida a dígitos.

    Args:
        cpf: CPF sem pontuação.

    Returns:
        True se o CPF for válido.
    """
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for length in (9, 10):
        total = sum(int(digit) * weight for digit, weight in zip(cpf[:length], range(length + 1, 1, -1)))
        if (total * 10) % 11 % 10 != int(cpf[length]):
            return False
    return True

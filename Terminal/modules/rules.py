from datetime import date, timedelta

from modules.models import Loan, User
from modules.textutils import format_money


def days_late(loan: Loan):
    endDate = date.fromisoformat(loan.return_date) if loan.return_date else date.today()
    return max(0, (endDate - date.fromisoformat(loan.due_date)).days)


def loan_status(loan: Loan):
    if loan.return_date is None:
        return "em andamento"
    action = "removido do acervo" if loan.was_removed else "devolvido"
    return f"{action} em {date.fromisoformat(loan.return_date):%d/%m/%Y}"


def loan_summary(loan: Loan):
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
    if user.suspended_until and date.fromisoformat(user.suspended_until) > date.today():
        return date.fromisoformat(user.suspended_until)
    return None


def suspend(user: User, days: int):
    startDate = suspension_end(user) or date.today()
    endDate = startDate + timedelta(days=days)
    user.suspended_until = endDate.isoformat()
    return endDate


def by_gender(user: User, feminine: str, masculine: str):
    return feminine if user.gender == "female" else masculine


def is_banned(user: User, config: dict):
    return config['ban_enabled'] and user.faults >= config['ban_after_faults']


def fine_for(lateDays: int, config: dict):
    return lateDays * config['fine_per_day_cents']


def pending_fines(userId: int, history: list):
    return [loan for loan in history if loan.user_id == userId and loan.fine_cents and not loan.fine_paid]


def is_valid_cpf(cpf: str):
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for length in (9, 10):
        total = sum(int(digit) * weight for digit, weight in zip(cpf[:length], range(length + 1, 1, -1)))
        if (total * 10) % 11 % 10 != int(cpf[length]):
            return False
    return True

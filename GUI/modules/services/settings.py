from modules.errors import BiblasError
from modules.rules import is_banned
from modules.state import CHOICES, config, save_data, users
from modules.storage import CONFIG_FILE


def ban_impact(enabled: bool, limit: int):
    before = {user.id for user in users if is_banned(user, config)}
    after = {user.id for user in users if enabled and user.faults >= limit}
    return len(after - before), len(before - after)


def update_settings(maxLoans: int, loanDays: int, latePenalty: str, fineCents: int,
                    banEnabled: bool, banAfterFaults: int, theme: str):
    if latePenalty not in CHOICES['late_penalty']:
        raise BiblasError("Punição por atraso inválida")
    if theme not in CHOICES['theme']:
        raise BiblasError("Tema inválido")

    config['max_loans'] = maxLoans
    config['loan_days'] = loanDays
    config['late_penalty'] = latePenalty
    config['fine_per_day_cents'] = fineCents
    config['ban_enabled'] = banEnabled
    config['ban_after_faults'] = banAfterFaults
    config['theme'] = theme
    save_data(CONFIG_FILE)

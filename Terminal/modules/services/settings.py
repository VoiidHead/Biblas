from modules.inputs import read_money, read_option, read_positive_int, read_positive_int_or_keep, read_yes_no
from modules.rules import is_banned
from modules.state import config, save_data, users
from modules.storage import CONFIG_FILE
from modules.textutils import format_money


def ban_impact(enabled: bool, limit: int):
    before = {user.id for user in users if is_banned(user, config)}
    after = {user.id for user in users if enabled and user.faults >= limit}
    return len(after - before), len(before - after)


def apply_ban_settings(enabled: bool, limit: int):
    newlyBanned, released = ban_impact(enabled, limit)
    if newlyBanned:
        print(f"{newlyBanned} usuário(s) já têm {limit} falta(s) ou mais e passariam a ficar banidos agora.")
    if released:
        print(f"{released} usuário(s) deixariam de estar banidos.")
    if (newlyBanned or released) and not read_yes_no("Confirmar a alteração? (s/n)\n"):
        print("Alteração cancelada\n")
        return False

    config['ban_enabled'] = enabled
    config['ban_after_faults'] = limit
    save_data(CONFIG_FILE)
    return True


def enable_ban():
    current = config['ban_after_faults']
    limit = read_positive_int_or_keep(f"Número de faltas para banir (Enter mantém {current}): ", current)
    if apply_ban_settings(True, limit):
        print(f"Banimento ativado: quem tiver {limit} falta(s) ou mais fica impedido de pegar livros\n")


def toggle_ban():
    if config['ban_enabled']:
        if apply_ban_settings(False, config['ban_after_faults']):
            print("Banimento desativado. As faltas continuam sendo contadas\n")
    else:
        enable_ban()


def change_ban_limit():
    if not config['ban_enabled']:
        print("O número de faltas só vale quando o banimento está ativado.")
        if read_yes_no("Ativar o banimento agora? (s/n)\n"):
            enable_ban()
        return
    enable_ban()


def prompt_fine_value():
    current = config['fine_per_day_cents']
    return read_money(f"Valor da multa por dia de atraso (Enter mantém {format_money(current)}): ", default=current)


def choose_penalty():
    selection = read_option(
        "Punição por atraso:\n1 - Suspensão (1 dia de suspensão por dia de atraso)\n"
        "2 - Multa (valor por dia de atraso)\n3 - Cancelar\n", ("1", "2", "3"))
    if selection == "3":
        return

    if selection == "1":
        config['late_penalty'] = 'suspension'
        message = "Punição alterada para suspensão. Multas já registradas continuam pendentes\n"
    else:
        config['late_penalty'] = 'fine'
        config['fine_per_day_cents'] = prompt_fine_value()
        message = "Punição alterada para multa. Usuários já suspensos continuam suspensos até o fim da suspensão\n"
    save_data(CONFIG_FILE)
    print(message)


def change_fine_value():
    if config['late_penalty'] != 'fine':
        print('O valor da multa só vale quando a punição por atraso é "multa".')
        if not read_yes_no("Mudar a punição para multa agora? (s/n)\n"):
            return
        config['late_penalty'] = 'fine'
    config['fine_per_day_cents'] = prompt_fine_value()
    save_data(CONFIG_FILE)
    print("Configuração salva\n")


def config_menu_text():
    loanDays = config['loan_days']
    dayWord = "dias" if loanDays > 1 else "dia"
    isFine = config['late_penalty'] == 'fine'
    penalty = "multa por dia de atraso" if isFine else "suspensão (1 dia por dia de atraso)"
    fineNote = "" if isFine else ' (inativo: só vale com a punição "multa")'
    banEnabled = config['ban_enabled']
    limitNote = "" if banEnabled else " (inativo: só vale com o banimento ativado)"
    return f'''
                Configurações atuais:
                A - Máximo de empréstimos por usuário: {config['max_loans']}
                B - Prazo de devolução: {loanDays} {dayWord}
                C - Punição por atraso: {penalty}
                D - Valor da multa por dia: {format_money(config['fine_per_day_cents'])}{fineNote}
                E - Banimento: {"ativado" if banEnabled else "desativado"}
                F - Faltas para banir: {config['ban_after_faults']}{limitNote}
                G - Voltar ao menu
                        \n'''


def change_config():
    while True:
        selection = input(config_menu_text()).strip().casefold()
        match selection:
            case "a":
                config['max_loans'] = read_positive_int("Novo máximo de empréstimos por usuário: ")
                save_data(CONFIG_FILE)
                print("Configuração salva\n")
            case "b":
                config['loan_days'] = read_positive_int("Novo prazo de devolução (em dias): ")
                save_data(CONFIG_FILE)
                print("Configuração salva. Vale apenas para os próximos empréstimos\n")
            case "c":
                choose_penalty()
            case "d":
                change_fine_value()
            case "e":
                toggle_ban()
            case "f":
                change_ban_limit()
            case "g":
                return

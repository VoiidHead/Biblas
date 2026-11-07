import flet as ft

from modules.errors import BiblasError
from modules.services.settings import ban_impact, update_settings
from modules.state import config
from modules.textutils import format_decimal
from modules.ui.components import (
    action_button, apply_theme, card, confirm, empty_note, error_label, heading, indented, notify,
    scroll_column, show_error, show_message, subheading,
)
from modules.ui.fields import ValidatedField, chain_focus, validate_all
from modules.validators import parse_money, parse_positive_int


def manual_theme():
    return config['theme'] if config['theme'] != "system" else "light"


def differs(parse, text, saved):
    try:
        return parse(text) != saved
    except BiblasError:
        return True


def settings_view(page):
    maxLoansField = ValidatedField(page, "Máximo de empréstimos por usuário", parse_positive_int,
                                   value=str(config['max_loans']), inputKind="digits", onChange=lambda: refresh_notice())
    loanDaysField = ValidatedField(page, "Prazo de devolução (dias)", parse_positive_int,
                                   value=str(config['loan_days']), inputKind="digits", onChange=lambda: refresh_notice())
    penaltyGroup = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="suspension", label="Suspensão (1 dia de suspensão por dia de atraso)"),
            ft.Radio(value="fine", label="Multa (valor por dia de atraso)"),
        ]),
        value=config['late_penalty'],
        on_change=lambda e: sync_state(e),
    )
    fineField = ValidatedField(page, "Valor da multa por dia (R$)", parse_money,
                               value=format_decimal(config['fine_per_day_cents']), inputKind="money", onChange=lambda: refresh_notice())
    banSwitch = ft.Switch(label="Banimento", value=config['ban_enabled'], on_change=lambda e: sync_state(e))
    banFaultsField = ValidatedField(page, "Faltas para banir", parse_positive_int,
                                    value=str(config['ban_after_faults']), inputKind="digits", onChange=lambda: refresh_notice())
    themeSwitch = ft.Switch(label="Seguir o tema do sistema", value=config['theme'] == "system",
                            on_change=lambda e: sync_state(e))
    lightRadio = ft.Radio(value="light", label="Claro")
    darkRadio = ft.Radio(value="dark", label="Escuro")
    themeGroup = ft.RadioGroup(content=ft.Row([lightRadio, darkRadio]), value=manual_theme(),
                               on_change=lambda e: sync_state(e))
    errorLabel = error_label()

    unsavedNotice = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ON_TERTIARY_CONTAINER),
            ft.Text("Você alterou configurações, mas elas ainda não foram salvas. Clique em Salvar para aplicá-las.",
                    color=ft.Colors.ON_TERTIARY_CONTAINER, expand=True),
        ]),
        bgcolor=ft.Colors.TERTIARY_CONTAINER,
        border_radius=8,
        padding=12,
        # fixo na base da área de conteúdo: fica no Stack, fora da coluna que rola
        left=0,
        right=0,
        bottom=0,
        # escondido abaixo da borda (o Stack corta o que passa dela) e invisível; sobe com um fade ao aparecer
        offset=ft.Offset(0, 1),
        opacity=0,
        animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )

    def current_theme():
        return "system" if themeSwitch.value else themeGroup.value

    def is_dirty():
        return (
            differs(parse_positive_int, maxLoansField.value, config['max_loans'])
            or differs(parse_positive_int, loanDaysField.value, config['loan_days'])
            or penaltyGroup.value != config['late_penalty']
            or (penaltyGroup.value == "fine" and differs(parse_money, fineField.value, config['fine_per_day_cents']))
            or bool(banSwitch.value) != config['ban_enabled']
            or (bool(banSwitch.value) and differs(parse_positive_int, banFaultsField.value, config['ban_after_faults']))
            or current_theme() != config['theme']
        )

    def refresh_notice(update=True):
        dirty = is_dirty()
        if (unsavedNotice.opacity == 1) != dirty:
            unsavedNotice.opacity = 1 if dirty else 0
            unsavedNotice.offset = ft.Offset(0, 0) if dirty else ft.Offset(0, 1)
            if update:
                unsavedNotice.update()

    # o tema escolhido aparece na hora, mas só é gravado ao salvar (app.py desfaz a prévia ao sair da tela)
    def sync_state(e=None):
        fineField.set_disabled(penaltyGroup.value != "fine")
        banFaultsField.set_disabled(not banSwitch.value)
        lightRadio.disabled = bool(themeSwitch.value)
        darkRadio.disabled = bool(themeSwitch.value)
        apply_theme(page, current_theme())
        refresh_notice(update=False)
        if e is not None:
            page.update()

    def reload(e=None):
        maxLoansField.value = str(config['max_loans'])
        loanDaysField.value = str(config['loan_days'])
        penaltyGroup.value = config['late_penalty']
        fineField.value = format_decimal(config['fine_per_day_cents'])
        banSwitch.value = config['ban_enabled']
        banFaultsField.value = str(config['ban_after_faults'])
        themeSwitch.value = config['theme'] == "system"
        themeGroup.value = manual_theme()
        show_error(errorLabel, "")
        sync_state()
        if e is not None:
            page.update()

    def apply(maxLoans, loanDays, latePenalty, fineCents, banEnabled, banAfter, theme):
        previousPenalty = config['late_penalty']
        try:
            update_settings(maxLoans, loanDays, latePenalty, fineCents, banEnabled, banAfter, theme)
        except BiblasError as error:
            show_error(errorLabel, str(error))
            page.update()
            return

        apply_theme(page, theme)
        refresh_notice(update=False)
        page.update()

        notes = []
        if latePenalty != previousPenalty:
            if latePenalty == "suspension":
                notes.append("Punição alterada para suspensão. Multas já registradas continuam pendentes.")
            else:
                notes.append("Punição alterada para multa. Usuários já suspensos continuam suspensos até o fim da suspensão.")
        if notes:
            show_message(page, "Configurações salvas", notes)
        else:
            notify(page, "Configurações salvas")

    def save(e):
        show_error(errorLabel, "")
        if not validate_all(maxLoansField, loanDaysField, fineField, banFaultsField):
            page.update()
            return

        latePenalty = penaltyGroup.value
        fineCents = fineField.result if latePenalty == "fine" else config['fine_per_day_cents']
        banEnabled = bool(banSwitch.value)
        banAfter = banFaultsField.result if banEnabled else config['ban_after_faults']
        theme = "system" if themeSwitch.value else themeGroup.value
        page.update()

        newlyBanned, released = ban_impact(banEnabled, banAfter)
        values = (maxLoansField.result, loanDaysField.result, latePenalty, fineCents, banEnabled, banAfter, theme)
        if not (newlyBanned or released):
            apply(*values)
            return

        lines = []
        if newlyBanned:
            lines.append(f"{newlyBanned} usuário(s) já têm {banAfter} falta(s) ou mais e passariam a ficar banidos agora.")
        if released:
            lines.append(f"{released} usuário(s) deixariam de estar banidos.")
        lines.append("Confirmar a alteração?")
        confirm(page, "Alterar banimento", "\n".join(lines), lambda: apply(*values))

    saveButton = action_button("Salvar", ft.Icons.SAVE, save)
    chain_focus(page, [maxLoansField, loanDaysField, fineField, banFaultsField], lastTarget=saveButton)

    form = ft.Column([
        maxLoansField.control,
        loanDaysField.control,
        empty_note("O prazo vale apenas para os próximos empréstimos."),
        ft.Text("Punição por atraso"),
        penaltyGroup,
        indented(fineField.control),
        banSwitch,
        indented(banFaultsField.control),
        ft.Divider(),
        subheading("Aparência"),
        themeSwitch,
        indented(themeGroup),
        errorLabel,
        ft.Row([saveButton, ft.TextButton("Descartar alterações", on_click=reload)]),
    ], spacing=12)

    sync_state()
    # o espaço no fim da coluna evita que o aviso cubra o botão Salvar quando a tela está rolada até o final
    content = scroll_column([heading("Configurações"), card(form), ft.Container(height=96)])
    return ft.Stack([content, unsavedNotice], expand=True)

import flet as ft

from modules.errors import BiblasError
from modules.models import GENDERS
from modules.queries import USER_HEADERS, USER_HISTORY_HEADERS, user_details, user_history_rows, user_row
from modules.rules import by_gender, pending_fines
from modules.services.users import add_user, edit_user, pay_fines, reset_faults
from modules.state import loanHistory, users
from modules.textutils import fold, format_cpf, format_money
from modules.ui.components import (
    action_button, back_button, card, confirm, data_table, empty_note, error_label, heading,
    info_rows, notify, password_field, scroll_column, show_error, subheading, text_field,
)
from modules.ui.fields import ValidatedField, chain_focus, unique_email, unique_username, validate_all
from modules.validators import clean, parse_cpf, parse_gender, parse_password


def gender_group(value=None, onChange=None):
    options = [ft.Radio(value=key, label=label.capitalize()) for key, label in GENDERS.items()]
    return ft.RadioGroup(content=ft.Row(options), value=value, on_change=onChange)


def validate_gender(genderGroup, genderError):
    try:
        gender = parse_gender(genderGroup.value)
    except BiblasError as error:
        show_error(genderError, str(error))
        return None
    show_error(genderError, "")
    return gender


def users_view(page):
    root = scroll_column()
    filterField = text_field("Filtrar por nome", width=300)
    tableHolder = ft.Column()

    def fill_table():
        key = fold(filterField.value or "")
        found = [user for user in users if key in fold(user.name)]
        if not users:
            tableHolder.controls = [empty_note("Não existem usuários registrados no sistema")]
        elif not found:
            tableHolder.controls = [empty_note("Nenhum usuário encontrado")]
        else:
            tableHolder.controls = [data_table(USER_HEADERS, [user_row(user) for user in found],
                                               onAction=lambda index: show_detail(found[index]),
                                               actionIcon=ft.Icons.VISIBILITY_OUTLINED,
                                               actionTooltip="Ver ficha e histórico")]

    def on_filter(e):
        fill_table()
        page.update()

    filterField.on_change = on_filter

    def show_list(e=None, update=True):
        toolbar = ft.Row([filterField, action_button("Novo usuário", ft.Icons.PERSON_ADD, show_new_user)],
                         wrap=True, spacing=12)
        root.controls = [heading("Usuários"), toolbar, tableHolder]
        fill_table()
        if update:
            page.update()

    def show_new_user(e=None):
        nameField = ValidatedField(page, "Nome de usuário", unique_username())
        genderError = error_label()
        genderGroup = gender_group(onChange=lambda e: (show_error(genderError, ""), page.update()))
        emailField = ValidatedField(page, "E-mail", unique_email())
        cpfField = ValidatedField(page, "CPF", parse_cpf, inputKind="cpf")
        passwordField = password_field("Senha")
        errorLabel = error_label()

        def save(e):
            show_error(errorLabel, "")
            isValid = validate_all(nameField, emailField, cpfField)
            gender = validate_gender(genderGroup, genderError)
            try:
                password = parse_password(passwordField.value)
            except BiblasError as error:
                show_error(errorLabel, str(error))
                isValid = False
            if not isValid or gender is None:
                page.update()
                return

            try:
                user = add_user(nameField.result, gender, emailField.result, cpfField.result, password)
            except BiblasError as error:
                show_error(errorLabel, str(error))
                page.update()
                return
            show_list()
            notify(page, f"Usuário cadastrado: {user.name}")

        saveButton = action_button("Cadastrar", ft.Icons.SAVE, save)
        chain_focus(page, [nameField, emailField, cpfField, passwordField], lastTarget=saveButton)

        form = ft.Column([
            nameField.control, ft.Text("Gênero"), genderGroup, genderError, emailField.control, cpfField.control,
            passwordField, errorLabel,
            ft.Row([saveButton, ft.TextButton("Cancelar", on_click=show_list)]),
        ], spacing=12)
        root.controls = [back_button(show_list), heading("Novo usuário"), card(form)]
        page.update()

    def show_edit(user):
        nameField = ValidatedField(page, "Nome de usuário", unique_username(user), value=user.name)
        genderError = error_label()
        genderGroup = gender_group(user.gender, onChange=lambda e: (show_error(genderError, ""), page.update()))
        emailField = ValidatedField(page, "E-mail", unique_email(user), value=user.email)
        cpfField = ValidatedField(page, "CPF", parse_cpf, value=format_cpf(user.cpf), inputKind="cpf")
        passwordField = password_field("Nova senha (deixe vazio para manter a atual)")
        errorLabel = error_label()

        def save(e):
            show_error(errorLabel, "")
            isValid = validate_all(nameField, emailField, cpfField)
            gender = validate_gender(genderGroup, genderError)
            if not isValid or gender is None:
                page.update()
                return

            try:
                edit_user(user,
                          newUsername=nameField.result if nameField.result != user.name else None,
                          gender=gender if gender != user.gender else None,
                          cpf=cpfField.result if cpfField.result != user.cpf else None,
                          password=clean(passwordField.value) or None,
                          email=emailField.result if emailField.result != user.email else None)
            except BiblasError as error:
                show_error(errorLabel, str(error))
                page.update()
                return
            show_detail(user)
            notify(page, f"Dados atualizados: {user.name}")

        saveButton = action_button("Salvar", ft.Icons.SAVE, save)
        chain_focus(page, [nameField, emailField, cpfField, passwordField], lastTarget=saveButton)

        form = ft.Column([
            nameField.control, ft.Text("Gênero"), genderGroup, genderError, emailField.control, cpfField.control,
            passwordField, errorLabel,
            ft.Row([saveButton,
                    ft.TextButton("Cancelar", on_click=lambda e: show_detail(user))]),
        ], spacing=12)
        root.controls = [back_button(lambda e: show_detail(user)), heading(f"Editar {user.name}"), card(form)]
        page.update()

    def ask_pay_fines(user):
        fines = pending_fines(user.id, loanHistory)
        lines = [f"{loan.title_name} (exemplar {loan.copy_id}): {format_money(loan.fine_cents)}" for loan in fines]
        lines.append(f"Total: {format_money(sum(loan.fine_cents for loan in fines))}")
        confirm(page, "Quitar multas pendentes", "\n".join(lines), lambda: pay(user), "Confirmar pagamento")

    def pay(user):
        try:
            total = pay_fines(user)
        except BiblasError as error:
            notify(page, str(error), isError=True)
            return
        show_detail(user)
        notify(page, f"Multas quitadas ({format_money(total)})")

    def ask_reset_faults(user):
        confirm(page, "Zerar faltas", f"Zerar as {user.faults} faltas de {user.name}?",
                lambda: reset(user), "Zerar")

    def reset(user):
        try:
            reset_faults(user)
        except BiblasError as error:
            notify(page, str(error), isError=True)
            return
        show_detail(user)
        notify(page, "Faltas zeradas")

    def show_detail(user):
        hasFines = bool(pending_fines(user.id, loanHistory))
        historyRows = user_history_rows(user)

        actions = ft.Row([
            action_button("Editar dados", ft.Icons.EDIT, lambda e: show_edit(user)),
            action_button("Quitar multas", ft.Icons.PAYMENTS_OUTLINED, lambda e: ask_pay_fines(user),
                          disabled=not hasFines),
            action_button("Zerar faltas", ft.Icons.RESTART_ALT, lambda e: ask_reset_faults(user),
                          disabled=user.faults == 0),
        ], wrap=True, spacing=12)

        controls = [back_button(show_list), heading(user.name), info_rows(user_details(user)), actions,
                    subheading("Histórico de empréstimos")]
        if historyRows:
            controls.append(data_table(USER_HISTORY_HEADERS, historyRows))
        else:
            controls.append(empty_note(f"{by_gender(user, 'A usuária', 'O usuário')} não possui empréstimos registrados"))
        root.controls = controls
        page.update()

    show_list(update=False)
    return root

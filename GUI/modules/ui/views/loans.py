import flet as ft

from modules.errors import BiblasError
from modules.services.loans import borrow, give_back
from modules.state import copies
from modules.textutils import format_date
from modules.ui.components import (
    action_button, card, empty_note, error_label, heading, notify, password_field, scroll_column,
    show_error, show_message, subheading,
)
from modules.ui.fields import (
    ValidatedField, available_copy, borrowed_copy, borrowing_username, chain_focus, validate_all,
)
from modules.validators import clean, parse_password


def loans_view(page):
    noCopies = not copies

    borrowCopyField = ValidatedField(page, "ID do exemplar", available_copy, width=200, inputKind="digits")
    borrowUserField = ValidatedField(page, "Nome do usuário", borrowing_username)
    borrowPasswordField = password_field("Senha")
    borrowError = error_label()

    returnCopyField = ValidatedField(page, "ID do exemplar", borrowed_copy, width=200, inputKind="digits")
    returnError = error_label()

    # um empréstimo ou devolução muda o que é válido nos campos do outro formulário
    def revalidate_filled():
        for field in (borrowCopyField, borrowUserField, returnCopyField):
            if clean(field.value):
                field.validate()

    def borrow_click(e):
        show_error(borrowError, "")
        isValid = validate_all(borrowCopyField, borrowUserField)
        try:
            password = parse_password(borrowPasswordField.value)
        except BiblasError as error:
            show_error(borrowError, str(error))
            isValid = False
        if not isValid:
            page.update()
            return

        try:
            dueDate = borrow(borrowCopyField.result, borrowUserField.result, password)
        except BiblasError as error:
            show_error(borrowError, str(error))
            page.update()
            return

        borrowCopyField.value = ""
        borrowUserField.value = ""
        borrowPasswordField.value = ""
        revalidate_filled()
        page.update()
        notify(page, f"Empréstimo registrado. Data máxima de devolução: {format_date(dueDate)}")

    def return_click(e):
        show_error(returnError, "")
        if not validate_all(returnCopyField):
            page.update()
            return

        try:
            messages = give_back(returnCopyField.result)
        except BiblasError as error:
            show_error(returnError, str(error))
            page.update()
            return

        returnCopyField.value = ""
        revalidate_filled()
        page.update()
        if messages:
            show_message(page, "Devolução registrada", messages)
        else:
            notify(page, "Devolução registrada")

    borrowButton = action_button("Registrar empréstimo", ft.Icons.OUTPUT, borrow_click, disabled=noCopies)
    returnButton = action_button("Registrar devolução", ft.Icons.INPUT, return_click, disabled=noCopies)
    chain_focus(page, [borrowCopyField, borrowUserField, borrowPasswordField], lastTarget=borrowButton)
    chain_focus(page, [returnCopyField], lastTarget=returnButton)

    borrowForm = ft.Column([
        subheading("Empréstimo"),
        borrowCopyField.control, borrowUserField.control, borrowPasswordField, borrowError,
        borrowButton,
    ], spacing=12)

    returnForm = ft.Column([
        subheading("Devolução"),
        returnCopyField.control, returnError,
        returnButton,
    ], spacing=12)

    controls = [heading("Empréstimos e devoluções")]
    if noCopies:
        controls.append(empty_note("O acervo está vazio. Adicione livros para registrar empréstimos."))
    controls.append(ft.Row([card(borrowForm), card(returnForm)], wrap=True, spacing=16,
                           vertical_alignment=ft.CrossAxisAlignment.START))
    return scroll_column(controls)

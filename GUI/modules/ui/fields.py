import flet as ft

from modules.errors import BiblasError
from modules.masks import cpf_mask, money_mask, only_digits, signed_digits
from modules.services.loans import check_copy_available, check_copy_borrowed, check_user_can_borrow
from modules.services.users import check_email_free, check_username_free
from modules.state import find_copy, find_user_by_name
from modules.ui.components import show_error
from modules.validators import clean, parse_email, parse_id, parse_username

# tipo de entrada: função que corrige o texto enquanto se digita
MASKS = {
    "digits": only_digits,
    "signed": signed_digits,
    "cpf": cpf_mask,
    "money": money_mask,
}


class ValidatedField:
    def __init__(self, page, label, validator=None, width=320, value="", inputKind=None, onChange=None, **options):
        self.page = page
        self.onChange = onChange
        self.validator = validator
        self.mask = MASKS[inputKind] if inputKind else None
        self.result = None
        self.textField = ft.TextField(label=label, width=width, value=value, on_change=self.on_change, **options)
        self.message = ft.Text("", color=ft.Colors.ERROR, size=12, visible=False)
        self.control = ft.Column([self.textField, self.message], spacing=2)

    @property
    def value(self):
        return self.textField.value

    @value.setter
    def value(self, newValue):
        self.textField.value = newValue
        show_error(self.message, "")

    def set_disabled(self, disabled):
        self.textField.disabled = disabled
        self.validate()

    def validate(self):
        if self.textField.disabled:
            self.result = None
            show_error(self.message, "")
            return True
        if not self.validator:
            self.result = clean(self.textField.value)
            return True
        try:
            self.result = self.validator(self.textField.value)
        except BiblasError as error:
            self.result = None
            show_error(self.message, str(error))
            return False
        show_error(self.message, "")
        return True

    # só atualiza o que mudou: reenviar o campo a cada tecla atrapalha quem está digitando ou apagando
    def on_change(self, e):
        textChanged = False
        if self.mask:
            current = self.textField.value or ""
            fixed = self.mask(current)
            if fixed != current:
                self.textField.value = fixed
                textChanged = True

        messageBefore = (self.message.value, self.message.visible)
        self.validate()
        if textChanged:
            self.textField.update()
        if (self.message.value, self.message.visible) != messageBefore:
            self.message.update()
        if self.onChange:
            self.onChange()


def validate_all(*fields):
    # sem all() sobre o gerador, para que todos os campos mostrem seu erro de uma vez
    results = [field.validate() for field in fields]
    return all(results)


def chain_focus(page, fields, lastTarget=None):
    controls = [field.textField if isinstance(field, ValidatedField) else field for field in fields]

    def focus_after(index):
        for nextControl in controls[index + 1:]:
            if not nextControl.disabled:
                page.run_task(nextControl.focus)
                return
        if lastTarget:
            page.run_task(lastTarget.focus)

    for index, control in enumerate(controls):
        control.on_submit = lambda e, index=index: focus_after(index)


def optional(validator):
    return lambda text: validator(text) if clean(text) else None


def unique_username(current=None):
    def validate(text):
        username = parse_username(text)
        check_username_free(username, current)
        return username
    return validate


def unique_email(current=None):
    def validate(text):
        email = parse_email(text)
        check_email_free(email, current)
        return email
    return validate


def existing_copy(text):
    copyId = parse_id(text)
    copy = find_copy(copyId)
    if not copy:
        raise BiblasError("Livro não encontrado")
    return copyId, copy


def available_copy(text):
    copyId, copy = existing_copy(text)
    check_copy_available(copy)
    return copyId


def borrowed_copy(text):
    copyId, copy = existing_copy(text)
    check_copy_borrowed(copy)
    return copyId


def borrowing_username(text):
    username = parse_username(text)
    user = find_user_by_name(username)
    if not user:
        raise BiblasError("Usuário não encontrado")
    check_user_can_borrow(user)
    return username

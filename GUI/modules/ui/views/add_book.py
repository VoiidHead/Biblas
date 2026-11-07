import flet as ft

from modules.errors import BiblasError
from modules.services.books import add_book
from modules.textutils import pluralize
from modules.ui.components import action_button, card, error_label, heading, scroll_column, show_error, show_message
from modules.ui.fields import ValidatedField, chain_focus, validate_all
from modules.validators import parse_positive_int, parse_year, required_text


def add_book_view(page):
    nameField = ValidatedField(page, "Nome do livro", required_text, width=420)
    authorField = ValidatedField(page, "Nome do autor", required_text, width=420)
    publisherField = ValidatedField(page, "Nome da editora", required_text, width=420)
    genreField = ValidatedField(page, "Gênero", required_text, width=420)
    pagesField = ValidatedField(page, "Número de páginas", parse_positive_int, width=200, inputKind="digits")
    yearField = ValidatedField(page, "Ano de lançamento (negativo para AEC)", parse_year, inputKind="signed")
    amountField = ValidatedField(page, "Quantidade de exemplares", parse_positive_int, width=200, value="1", inputKind="digits")
    errorLabel = error_label()
    allFields = [nameField, authorField, publisherField, genreField, pagesField, yearField, amountField]

    def submit(e):
        if not validate_all(*allFields):
            page.update()
            return

        try:
            title, isNewTitle, newCopies = add_book(
                nameField.result, authorField.result, publisherField.result, genreField.result,
                pagesField.result, yearField.result, amountField.result,
            )
        except BiblasError as error:
            show_error(errorLabel, str(error))
            page.update()
            return

        show_error(errorLabel, "")
        for field in allFields:
            field.value = ""
        amountField.value = "1"
        page.update()

        amount = len(newCopies)
        lines = []
        if not isNewTitle:
            lines.append("Título já cadastrado. Os exemplares foram adicionados a ele.")
        lines.append(f"{amount} {pluralize(amount, 'exemplar adicionado', 'exemplares adicionados')} de \"{title.name}\".")
        lines.append(f"{pluralize(amount, 'ID', 'IDs')}: {', '.join(str(copy.id) for copy in newCopies)}")
        show_message(page, "Livro adicionado", lines)

    submitButton = action_button("Adicionar ao acervo", ft.Icons.LIBRARY_ADD, submit)
    chain_focus(page, allFields, lastTarget=submitButton)

    form = ft.Column([field.control for field in allFields] + [errorLabel, submitButton], spacing=12)
    return scroll_column([heading("Adicionar livro ao acervo"), card(form)])

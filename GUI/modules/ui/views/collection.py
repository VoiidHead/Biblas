import flet as ft

from modules.errors import BiblasError
from modules.queries import (
    COPY_HEADERS, SEARCH_FIELDS, TITLE_HEADERS, TITLE_HISTORY_HEADERS,
    copy_row, search_titles, title_counts, title_details, title_history_rows, title_row,
)
from modules.services.books import remove_book
from modules.state import active_loan, copies, copies_of, find_title, username_of
from modules.textutils import pluralize
from modules.ui.components import (
    action_button, back_button, card, confirm, data_table, empty_note, heading,
    info_rows, notify, scroll_column, show_message, subheading,
)
from modules.ui.fields import ValidatedField, chain_focus, optional, validate_all
from modules.validators import parse_id


def collection_view(page):
    root = scroll_column()
    searchFields = {
        attribute: ValidatedField(page, label, optional(parse_id) if attribute == "id" else None, width=200,
                       inputKind="digits" if attribute == "id" else None)
        for attribute, label in SEARCH_FIELDS
    }
    resultHolder = ft.Column(spacing=12)

    def current_filters():
        if not validate_all(*searchFields.values()):
            return None
        return {attribute: field.result for attribute, field in searchFields.items() if field.result not in (None, "")}

    def fill_results(openSingle=False):
        filters = current_filters()
        if filters is None:
            resultHolder.controls = []
            return

        found = search_titles(filters)
        if openSingle and filters and len(found) == 1:
            show_detail(found[0])
            return

        if not found:
            note = "Nenhum livro encontrado" if filters else "O acervo está vazio. Use “Adicionar livro” para cadastrar o primeiro."
            resultHolder.controls = [empty_note(note)]
            return

        count = len(found)
        summary = f"{count} {pluralize(count, 'título', 'títulos')}"
        if not filters:
            summary += f" | {len(copies)} {pluralize(len(copies), 'exemplar', 'exemplares')} no total"
        resultHolder.controls = [
            ft.Text(summary),
            data_table(TITLE_HEADERS, [title_row(title) for title in found],
                       onAction=lambda index: show_detail(found[index]),
                       actionIcon=ft.Icons.VISIBILITY_OUTLINED, actionTooltip="Ver exemplares e histórico"),
        ]

    def search(e):
        fill_results(openSingle=True)
        page.update()

    searchButton = action_button("Buscar", ft.Icons.SEARCH, search)
    chain_focus(page, list(searchFields.values()), lastTarget=searchButton)

    def clear(e):
        for field in searchFields.values():
            field.value = ""
        fill_results()
        page.update()

    def show_list(e=None, update=True):
        searchRow = ft.Row([field.control for field in searchFields.values()], wrap=True, spacing=12,
                           vertical_alignment=ft.CrossAxisAlignment.START)
        buttons = ft.Row([searchButton,
                          ft.TextButton("Limpar", icon=ft.Icons.CLEAR, on_click=clear)])
        root.controls = [heading("Acervo"), card(ft.Column([searchRow, buttons], spacing=12)), resultHolder]
        fill_results()
        if update:
            page.update()

    def ask_remove(title, copy):
        loan = active_loan(copy)
        if loan:
            message = (f"O exemplar {copy.id} está emprestado a {username_of(loan)}. Removê-lo encerra o empréstimo "
                       f"e pode gerar punição por atraso. Remover mesmo assim?")
        else:
            message = f"Remover o exemplar {copy.id} de \"{title.name}\" do acervo?"
        confirm(page, "Remover exemplar", message, lambda: remove(title, copy), "Remover")

    def remove(title, copy):
        try:
            messages = remove_book(copy.id)
        except BiblasError as error:
            notify(page, str(error), isError=True)
            return

        if find_title(title.id):
            show_detail(title)
        else:
            show_list()
        if messages:
            show_message(page, "Exemplar removido", messages)
        else:
            notify(page, f"Exemplar {copy.id} removido")

    def show_detail(title):
        titleCopies = copies_of(title)
        total, available = title_counts(title)
        historyRows = title_history_rows(title)

        controls = [
            back_button(show_list),
            heading(title.name),
            info_rows(title_details(title)),
            subheading(f"Exemplares: {total} | Disponíveis: {available}"),
            data_table(COPY_HEADERS, [copy_row(copy) for copy in titleCopies],
                       onAction=lambda index: ask_remove(title, titleCopies[index]),
                       actionIcon=ft.Icons.DELETE_OUTLINE, actionTooltip="Remover exemplar"),
            subheading("Histórico de empréstimos"),
        ]
        if historyRows:
            controls.append(data_table(TITLE_HISTORY_HEADERS, historyRows))
        else:
            controls.append(empty_note("Nenhum empréstimo registrado"))
        root.controls = controls
        page.update()

    show_list(update=False)
    return root

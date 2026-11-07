import flet as ft


def apply_theme(page, theme):
    modes = {"system": ft.ThemeMode.SYSTEM, "light": ft.ThemeMode.LIGHT, "dark": ft.ThemeMode.DARK}
    page.theme_mode = modes.get(theme, ft.ThemeMode.SYSTEM)


def indented(*controls, level=1):
    return ft.Row([ft.Container(width=32 * level), ft.Column(list(controls), spacing=4)],
                  vertical_alignment=ft.CrossAxisAlignment.START)


def notify(page, message, isError=False):
    color = ft.Colors.RED_700 if isError else ft.Colors.GREEN_700
    page.show_dialog(ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=color))


def show_message(page, title, lines):
    def close(e):
        page.pop_dialog()

    dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Column([ft.Text(line, selectable=True) for line in lines], tight=True, spacing=8),
        actions=[ft.TextButton("OK", on_click=close)],
    )
    page.show_dialog(dialog)


def confirm(page, title, message, onConfirm, confirmText="Confirmar"):
    def cancel(e):
        page.pop_dialog()

    def accept(e):
        page.pop_dialog()
        onConfirm()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[ft.TextButton("Cancelar", on_click=cancel), ft.Button(confirmText, on_click=accept)],
    )
    page.show_dialog(dialog)


def text_field(label, width=320, value="", **options):
    return ft.TextField(label=label, width=width, value=value, **options)


def password_field(label, width=320, **options):
    return ft.TextField(label=label, width=width, value="", password=True, can_reveal_password=True, **options)


def heading(text):
    return ft.Text(text, size=26, weight=ft.FontWeight.BOLD)


def subheading(text):
    return ft.Text(text, size=18, weight=ft.FontWeight.BOLD)


def error_label():
    return ft.Text("", color=ft.Colors.ERROR, visible=False)


def show_error(label, message):
    label.value = message
    label.visible = bool(message)


def empty_note(text):
    return ft.Text(text, italic=True, color=ft.Colors.ON_SURFACE_VARIANT)


def action_button(text, icon, onClick, disabled=False):
    return ft.Button(text, icon=icon, on_click=onClick, disabled=disabled)


def back_button(onClick, text="Voltar"):
    return ft.TextButton(text, icon=ft.Icons.ARROW_BACK, on_click=onClick)


def card(content):
    return ft.Card(content=ft.Container(content=content, padding=16))


def scroll_column(controls=None):
    return ft.Column(controls or [], expand=True, scroll=ft.ScrollMode.AUTO, spacing=16)


def info_rows(pairs):
    return ft.Column(
        [ft.Row([ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=170),
                 ft.Text(str(value), selectable=True)]) for label, value in pairs],
        spacing=4,
    )


def data_table(headers, rows, onAction=None, actionIcon=None, actionTooltip=""):
    columns = [ft.DataColumn(ft.Text(header, weight=ft.FontWeight.BOLD)) for header in headers]
    if onAction:
        columns.append(ft.DataColumn(ft.Text("")))

    tableRows = []
    for index, row in enumerate(rows):
        cells = [ft.DataCell(ft.Text(str(value))) for value in row]
        if onAction:
            button = ft.IconButton(icon=actionIcon, tooltip=actionTooltip,
                                   on_click=lambda e, index=index: onAction(index))
            cells.append(ft.DataCell(button))
        tableRows.append(ft.DataRow(cells=cells))

    return ft.Row([ft.DataTable(columns=columns, rows=tableRows)], scroll=ft.ScrollMode.AUTO)

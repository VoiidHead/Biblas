from pathlib import Path

import flet as ft

from modules.state import config
from modules.storage import startupWarnings
from modules.ui.components import apply_theme, show_message
from modules.ui.views.add_book import add_book_view
from modules.ui.views.collection import collection_view
from modules.ui.views.loans import loans_view
from modules.ui.views.settings import settings_view
from modules.ui.views.users import users_view

ICONS_DIR = Path(__file__).resolve().parent / "icons"
WINDOW_ICON = "icon_windows.ico"  # caminho relativo à pasta de assets (ICONS_DIR)

# rótulo, ícone, ícone selecionado, função que monta a tela
DESTINATIONS = [
    ("Acervo", ft.Icons.MENU_BOOK_OUTLINED, ft.Icons.MENU_BOOK, collection_view),
    ("Adicionar livro", ft.Icons.LIBRARY_ADD_OUTLINED, ft.Icons.LIBRARY_ADD, add_book_view),
    ("Empréstimos", ft.Icons.SWAP_HORIZ_OUTLINED, ft.Icons.SWAP_HORIZ, loans_view),
    ("Usuários", ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, users_view),
    ("Configurações", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS, settings_view),
]


def main(page: ft.Page):
    page.title = "Biblas"
    if not page.web:
        page.window.icon = WINDOW_ICON
    page.padding = 0
    apply_theme(page, config['theme'])
    content = ft.Container(expand=True, padding=24)
    sidebar = ft.Column(spacing=8)

    # itens feitos de Container sem "ink" não recebem foco do teclado: o Tab percorre só o conteúdo
    def build_sidebar(selectedIndex: int):
        items = []
        for index, (label, icon, selectedIcon, _) in enumerate(DESTINATIONS):
            isSelected = index == selectedIndex
            color = ft.Colors.ON_SECONDARY_CONTAINER if isSelected else ft.Colors.ON_SURFACE_VARIANT
            items.append(ft.Container(
                content=ft.Column(
                    [ft.Icon(selectedIcon if isSelected else icon, color=color),
                     ft.Text(label, size=12, color=color, text_align=ft.TextAlign.CENTER)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                ),
                width=92,
                padding=10,
                border_radius=12,
                bgcolor=ft.Colors.SECONDARY_CONTAINER if isSelected else None,
                on_click=lambda e, index=index: open_view(index),
            ))
        return items

    # a tela é montada de novo a cada navegação, então sempre mostra os dados atuais
    def open_view(index: int):
        apply_theme(page, config['theme'])  # desfaz a prévia de um tema que não foi salvo
        sidebar.controls = build_sidebar(index)
        content.content = DESTINATIONS[index][3](page)
        page.update()

    def on_key(e):
        if e.ctrl and len(e.key) == 1 and e.key.isdigit() and 1 <= int(e.key) <= len(DESTINATIONS):
            open_view(int(e.key) - 1)

    page.on_keyboard_event = on_key

    page.add(ft.Row([ft.Container(sidebar, padding=8), ft.VerticalDivider(width=1), content], expand=True))
    open_view(0)

    if startupWarnings:
        show_message(page, "Aviso", startupWarnings)

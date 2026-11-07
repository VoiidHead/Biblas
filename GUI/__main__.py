import flet as ft

from modules.ui.app import ICONS_DIR, main

if __name__ == '__main__':
    ft.run(main, assets_dir=str(ICONS_DIR))

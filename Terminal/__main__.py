from modules.menus import EMPTY_MENU, FULL_MENU, menu_text
from modules.state import copies

PAUSE_MESSAGE = "Digite qualquer coisa para retornar ao menu\n"


def main():
    while True:
        options = FULL_MENU if copies else EMPTY_MENU
        selection = input(menu_text(options)).strip()
        if selection == "/":
            break

        if selection in options:
            _, action, pause = options[selection]
            action()
            if pause:
                input(PAUSE_MESSAGE)


if __name__ == '__main__':
    main()

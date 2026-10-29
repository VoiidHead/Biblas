"""Ponto de entrada do Biblas, sistema de biblioteca em linha de comando.

Mostra o menu principal em loop e executa a ação escolhida pelo operador.
Para rodar, execute a pasta do projeto (ex.: `python biblas`) a partir do diretório pai.
"""

from modules.menus import EMPTY_MENU, FULL_MENU, menu_text
from modules.state import copies

PAUSE_MESSAGE = "Digite qualquer coisa para retornar ao menu\n"


def main():
    """Executa o loop do menu principal até o operador digitar '/'.

    A cada volta escolhe o menu (completo se já existem exemplares no acervo,
    reduzido caso contrário), lê a opção e chama a ação associada. Se a opção
    pede pausa, espera o operador apertar Enter antes de redesenhar o menu.
    Opções que não existem no menu são ignoradas e o menu reaparece.
    """
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

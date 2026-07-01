"""
MicroOff - Приложение для управления микрофоном.
Главный файл запуска.
"""

import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from src.main_window import MicrophoneGUI

# Отключаем ошибки DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


def main():
    """
    Главная функция запуска приложения.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle('Fusion')

    # Отключаем полосы прокрутки глобально
    app.setStyleSheet("""
        QScrollBar {
            width: 0px;
            height: 0px;
        }
        QScrollBar::handle {
            width: 0px;
            height: 0px;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            width: 0px;
            height: 0px;
        }
        QScrollBar::add-page, QScrollBar::sub-page {
            width: 0px;
            height: 0px;
        }
    """)

    window = MicrophoneGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
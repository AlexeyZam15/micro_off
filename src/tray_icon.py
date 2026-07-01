"""
Модуль системного трея для приложения MicroOff.
Обеспечивает иконку в системном трее с контекстным меню.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from src.logger import Logger


class SystemTrayIcon(QSystemTrayIcon):
    """
    Иконка в системном трее с контекстным меню.
    """

    def __init__(self, parent=None):
        """
        Инициализация иконки системного трея.

        Args:
            parent: Родительское окно
        """
        super().__init__(parent)
        self.parent = parent
        self.create_tray_icon()
        self.create_menu()
        self.activated.connect(self.on_activated)

    def create_tray_icon(self):
        """
        Создает иконку для системного трея.
        """
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            color = QColor(155, 89, 255)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))

            painter.drawRoundedRect(24, 8, 16, 24, 8, 8)
            painter.drawRoundedRect(28, 32, 8, 12, 4, 4)
            painter.drawArc(16, 4, 32, 32, 30 * 16, 120 * 16)

            painter.end()
            self.setIcon(QIcon(pixmap))
        except Exception as e:
            Logger.log_error("Ошибка создания иконки трея", e)
            self.setIcon(QIcon())

    def create_menu(self):
        """
        Создает контекстное меню для системного трея.
        """
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #9b59ff;
                padding: 8px;
                border-radius: 10px;
            }
            QMenu::item {
                padding: 10px 30px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background: #2d1b4e;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(155, 89, 255, 0.3);
                margin: 5px 10px;
            }
        """)

        show_action = QAction("✨ Показать", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        mute_action = QAction("🔇 Выключить", self)
        mute_action.triggered.connect(self.parent.mute_microphone)
        tray_menu.addAction(mute_action)

        unmute_action = QAction("🎤 Включить", self)
        unmute_action.triggered.connect(self.parent.unmute_microphone)
        tray_menu.addAction(unmute_action)

        tray_menu.addSeparator()

        quit_action = QAction("🚀 Выход", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.setContextMenu(tray_menu)

    def on_activated(self, reason):
        """
        Обработка активации иконки в трее.

        Args:
            reason: Причина активации
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """
        Показывает главное окно приложения.
        """
        self.parent.show()
        self.parent.activateWindow()
        self.parent.raise_()

    def quit_app(self):
        """
        Закрывает приложение.
        """
        self.parent.controller.close()
        QApplication.quit()
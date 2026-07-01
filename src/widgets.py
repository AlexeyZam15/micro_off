"""
Модуль пользовательских виджетов для приложения MicroOff.
Содержит кастомные кнопки, комбобоксы и виджеты горячих клавиш.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class GlassButton(QPushButton):
    """
    Стеклянная кнопка с градиентным фоном и фиолетовой тематикой.
    """

    def __init__(self, text, color="#9b59ff"):
        """
        Инициализация стеклянной кнопки.

        Args:
            text: Текст кнопки
            color: Основной цвет в формате CSS
        """
        super().__init__(text)
        self.color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.3), stop: 1 rgba(155, 89, 255, 0.1));
                color: #ffffff;
                border: 1px solid rgba(155, 89, 255, 0.5);
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
                min-height: 40px;
            }}
            QPushButton:disabled {{
                background: rgba(50, 50, 50, 0.5);
                color: #666666;
                border: 1px solid #333333;
            }}
        """)


class ModernComboBox(QComboBox):
    """
    Современный комбобокс с фиолетовой тематикой и кастомным оформлением.
    """

    def __init__(self):
        """
        Инициализация современного комбобокса.
        """
        super().__init__()
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QComboBox {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.2), stop: 1 rgba(155, 89, 255, 0.05));
                color: #ffffff;
                border: 1px solid rgba(155, 89, 255, 0.4);
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                min-height: 40px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #9b59ff;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #ffffff;
                border: 1px solid #9b59ff;
                border-radius: 8px;
                selection-background-color: #2d1b4e;
                selection-color: #ffffff;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox:disabled {
                background: rgba(50, 50, 50, 0.3);
                color: #666666;
                border-color: #333333;
            }
        """)


class HotkeyWidget(QWidget):
    """
    Адаптивный виджет для отображения информации о горячей клавише.
    Автоматически подстраивается под размер текста и контейнера.
    """

    def __init__(self, key_text, action_text, color):
        """
        Инициализация виджета горячей клавиши.

        Args:
            key_text: Текст клавиши (например, "F4")
            action_text: Текст действия (например, "Переключить")
            color: Цвет текста действия в формате CSS
        """
        super().__init__()

        # Убираем фиксированный размер, делаем адаптивным
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setMinimumHeight(80)

        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.15), stop: 1 rgba(155, 89, 255, 0.05));
                border-radius: 10px;
                border: 2px solid rgba(155, 89, 255, 0.2);
                padding: 8px;
            }}
        """)

        # Основной layout с выравниванием по центру
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignCenter)

        # Метка с клавишей - крупный шрифт
        key_label = QLabel(key_text)
        key_label.setAlignment(Qt.AlignCenter)
        key_label.setStyleSheet("""
            color: #a78bfa;
            font-size: 24px;
            font-weight: 900;
            background: transparent;
        """)
        key_label.setWordWrap(True)
        layout.addWidget(key_label)

        # Метка с действием - более мелкий шрифт
        action_label = QLabel(action_text)
        action_label.setAlignment(Qt.AlignCenter)
        action_label.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
            font-weight: 700;
            background: transparent;
        """)
        action_label.setWordWrap(True)
        layout.addWidget(action_label)

        # Сохраняем ссылки для возможного обновления
        self.key_label = key_label
        self.action_label = action_label

    def set_text(self, key_text, action_text):
        """
        Обновление текста в виджете.

        Args:
            key_text: Новый текст клавиши
            action_text: Новый текст действия
        """
        self.key_label.setText(key_text)
        self.action_label.setText(action_text)
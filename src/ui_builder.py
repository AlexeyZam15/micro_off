"""
Модуль построителя пользовательского интерфейса для MicroOff.
Содержит класс UIBuilder для создания всех элементов интерфейса.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from src.widgets import GlassButton, ModernComboBox, HotkeyWidget


class UIBuilder:
    """
    Класс для построения пользовательского интерфейса главного окна.
    """

    @staticmethod
    def build_title_bar(parent):
        """
        Создает верхнюю панель с заголовком и кнопками управления окном.

        Args:
            parent: Родительское окно

        Returns:
            QWidget: Виджет заголовка
        """
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3b0a6b, stop: 0.5 #4c1d95, stop: 1 #3b0a6b);
                border-radius: 10px 10px 0 0;
            }
        """)
        title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(12, 0, 8, 0)
        title_bar_layout.setSpacing(0)

        # Иконка и заголовок
        title_icon = QLabel()
        title_icon.setPixmap(parent.create_microphone_icon().pixmap(20, 20))
        title_bar_layout.addWidget(title_icon)
        title_bar_layout.addSpacing(8)

        title_label = QLabel("MicroOff - Управление микрофоном")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        # Кнопки управления окном с курсором-указателем
        btn_minimize = QPushButton("─")
        btn_minimize.setFixedSize(32, 28)
        btn_minimize.setCursor(Qt.PointingHandCursor)
        btn_minimize.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        btn_minimize.clicked.connect(parent.showMinimized)
        title_bar_layout.addWidget(btn_minimize)

        btn_maximize = QPushButton("□")
        btn_maximize.setFixedSize(32, 28)
        btn_maximize.setCursor(Qt.PointingHandCursor)
        btn_maximize.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        btn_maximize.clicked.connect(parent.toggle_maximize)
        title_bar_layout.addWidget(btn_maximize)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 28)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 0.3);
                border-radius: 4px;
                color: #ffffff;
            }
        """)
        btn_close.clicked.connect(parent.close)
        title_bar_layout.addWidget(btn_close)

        return title_bar

    @staticmethod
    def build_header(parent):
        """
        Создает заголовок приложения с иконкой и названием.

        Args:
            parent: Родительское окно

        Returns:
            QWidget: Виджет заголовка
        """
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(12)
        title_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setPixmap(parent.create_microphone_icon().pixmap(32, 32))
        icon_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(icon_label)

        title_label = QLabel("MicroOff")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 26px; 
            font-weight: 800; 
            color: #a78bfa;
            letter-spacing: 2px;
            background: transparent;
        """)
        title_layout.addWidget(title_label)

        subtitle = QLabel("Управление микрофоном")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 11px; 
            color: rgba(155, 89, 255, 0.5);
            letter-spacing: 3px;
            background: transparent;
        """)
        title_layout.addWidget(subtitle)

        return title_widget

    @staticmethod
    def build_status_panel(parent):
        """
        Создает панель статуса с индикатором состояния.

        Args:
            parent: Родительское окно

        Returns:
            QFrame: Панель статуса
        """
        status_card = QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.12), stop: 1 rgba(155, 89, 255, 0.04));
                border-radius: 12px;
                padding: 16px;
                border: 1px solid rgba(155, 89, 255, 0.15);
            }
        """)
        status_layout = QHBoxLayout(status_card)
        status_layout.setAlignment(Qt.AlignCenter)
        status_layout.setSpacing(12)
        status_layout.setContentsMargins(0, 0, 0, 0)

        parent.status_label = QLabel("⏳ Загрузка...")
        parent.status_label.setStyleSheet("""
            font-size: 22px; 
            font-weight: 700; 
            color: #a78bfa;
            background: transparent;
        """)
        status_layout.addWidget(parent.status_label)

        parent.status_indicator = QLabel()
        parent.status_indicator.setFixedSize(20, 20)
        parent.status_indicator.setStyleSheet("""
            QLabel {
                border-radius: 10px;
                background-color: #a78bfa;
                border: 2px solid #9b59ff;
            }
        """)
        status_layout.addWidget(parent.status_indicator)

        return status_card

    @staticmethod
    def build_control_buttons(parent):
        """
        Создает кнопки управления микрофоном.

        Args:
            parent: Родительское окно

        Returns:
            QWidget: Контейнер с кнопками
        """
        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        parent.mute_btn = GlassButton("🔇 Выключить")
        parent.mute_btn.clicked.connect(parent.mute_microphone)
        parent.mute_btn.setEnabled(False)
        btn_layout.addWidget(parent.mute_btn)

        parent.unmute_btn = GlassButton("🎤 Включить")
        parent.unmute_btn.clicked.connect(parent.unmute_microphone)
        parent.unmute_btn.setEnabled(False)
        btn_layout.addWidget(parent.unmute_btn)

        parent.toggle_btn = GlassButton("🔄 Переключить")
        parent.toggle_btn.clicked.connect(parent.toggle_microphone)
        parent.toggle_btn.setEnabled(False)
        btn_layout.addWidget(parent.toggle_btn)

        return btn_container

    @staticmethod
    def build_separator():
        """
        Создает разделительную линию.

        Returns:
            QFrame: Разделитель
        """
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("""
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 transparent, stop: 0.5 rgba(155, 89, 255, 0.2), stop: 1 transparent);
            max-height: 1px;
            margin: 5px 0;
        """)
        return line

    @staticmethod
    def build_device_selector(parent):
        """
        Создает выпадающий список устройств.

        Args:
            parent: Родительское окно

        Returns:
            QWidget: Контейнер с выбором устройств
        """
        device_container = QWidget()
        device_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.06), stop: 1 rgba(155, 89, 255, 0.02));
                border-radius: 10px;
                padding: 10px;
                border: 1px solid rgba(155, 89, 255, 0.08);
            }
        """)
        device_layout = QHBoxLayout(device_container)
        device_layout.setSpacing(10)
        device_layout.setContentsMargins(12, 6, 12, 6)

        device_label = QLabel("🎤 Устройство")
        device_label.setStyleSheet("""
            font-weight: 600; 
            font-size: 11px; 
            color: #9b59ff;
            letter-spacing: 1px;
            background: transparent;
        """)
        device_layout.addWidget(device_label)

        parent.device_combo = ModernComboBox()
        parent.device_combo.addItem("⏳ Загрузка...")
        parent.device_combo.setEnabled(False)
        parent.device_combo.currentIndexChanged.connect(parent.on_device_changed)
        device_layout.addWidget(parent.device_combo)

        parent.refresh_btn = QPushButton("⟳")
        parent.refresh_btn.setFixedSize(38, 38)
        parent.refresh_btn.setCursor(Qt.PointingHandCursor)
        parent.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.3), stop: 1 rgba(155, 89, 255, 0.1));
                color: #9b59ff;
                border: 1px solid rgba(155, 89, 255, 0.3);
                border-radius: 8px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.5), stop: 1 rgba(155, 89, 255, 0.2));
                border-color: rgba(155, 89, 255, 0.6);
            }
            QPushButton:disabled {
                background: rgba(50, 50, 50, 0.3);
                color: #444444;
                border-color: #333333;
            }
        """)
        parent.refresh_btn.clicked.connect(parent.load_devices_async)
        parent.refresh_btn.setEnabled(False)
        parent.refresh_btn.setToolTip("Обновить")
        device_layout.addWidget(parent.refresh_btn)

        return device_container

    @staticmethod
    def build_hotkeys_panel():
        """
        Создает панель с горячими клавишами.

        Returns:
            QFrame: Панель горячих клавиш
        """
        hotkey_card = QFrame()
        hotkey_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(155, 89, 255, 0.06), stop: 1 rgba(155, 89, 255, 0.02));
                border-radius: 12px;
                padding: 20px 18px 18px 18px;
                border: 1px solid rgba(155, 89, 255, 0.08);
            }
        """)
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setSpacing(0)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок блока горячих клавиш
        hotkey_title = QLabel("⌨️ Горячие клавиши")
        hotkey_title.setAlignment(Qt.AlignCenter)
        hotkey_title.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: rgba(155, 89, 255, 0.6);
            letter-spacing: 2px;
            background: transparent;
            padding-bottom: 8px;
        """)
        hotkey_layout.addWidget(hotkey_title)

        # Контейнер для клавиш
        hotkey_container = QWidget()
        hotkey_container.setStyleSheet("background: transparent;")
        hotkey_container_layout = QHBoxLayout(hotkey_container)
        hotkey_container_layout.setSpacing(12)
        hotkey_container_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_container_layout.setAlignment(Qt.AlignCenter)

        # Создаем виджеты для всех трех клавиш
        hotkey_widgets = [
            HotkeyWidget("F4", "Переключить", "#f59e0b"),
            HotkeyWidget("F2", "Выключить", "#ef4444"),
            HotkeyWidget("F3", "Включить", "#22c55e")
        ]

        # Добавляем виджеты в контейнер с растяжением для равномерного распределения
        for i, widget in enumerate(hotkey_widgets):
            hotkey_container_layout.addWidget(widget)
            if i < len(hotkey_widgets) - 1:
                hotkey_container_layout.addStretch()

        hotkey_layout.addWidget(hotkey_container)
        return hotkey_card
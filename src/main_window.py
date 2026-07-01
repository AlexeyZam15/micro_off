"""
Модуль главного окна приложения MicroOff.
Содержит основное окно с элементами управления микрофоном.
"""

import sys
import threading
import time
import os
import json
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from src.logger import Logger
from src.microphone_controller import MicrophoneController
from src.widgets import GlassButton, ModernComboBox, HotkeyWidget
from src.tray_icon import SystemTrayIcon
from src.hotkey_manager import HotkeyManager
from src.workers import MicrophoneWorker, DeviceLoader
from src.ui_builder import UIBuilder


class MicrophoneGUI(QMainWindow):
    """
    Главное окно приложения MicroOff.
    Содержит все элементы управления и взаимодействует с контроллером.
    """

    # Сигнал для обновления UI из другого потока (на уровне класса)
    update_devices_ui_signal = pyqtSignal(list)

    def __init__(self):
        """
        Инициализация главного окна.
        """
        super().__init__()
        self.controller = MicrophoneController()
        self.worker = None
        self.device_loader = None
        self.is_loading = False
        self.ui_initialized = False

        # Подключаем сигнал к слоту
        self.update_devices_ui_signal.connect(self.update_devices_ui)

        # Отключаем стандартную рамку окна
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Отключаем полосы прокрутки
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: transparent;
            }
            QScrollBar {
                width: 0px;
                height: 0px;
            }
            QScrollBar::handle {
                width: 0px;
                height: 0px;
            }
        """)

        self.init_ui()
        self.setup_tray()

        # Настройка горячих клавиш - F4, F2, F3
        self.hotkey_manager = HotkeyManager(
            self.toggle_microphone,
            self.mute_microphone,
            self.unmute_microphone
        )
        self.hotkey_manager.register_hotkeys()

        self.start_status_updater()

        # Асинхронная загрузка кэша с задержкой для получения active_device_id
        QTimer.singleShot(300, self.load_cache_async)

        # Загружаем устройства с задержкой чтобы активное устройство успело определиться
        QTimer.singleShot(500, self.load_devices_async)

    def load_devices_async(self):
        """
        Асинхронная загрузка устройств.
        Принудительно обновляет список, сбрасывая кэш.
        """
        if self.is_loading:
            return

        self.is_loading = True
        self.ui_initialized = False  # Сбрасываем флаг для принудительного обновления
        self.device_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.device_combo.clear()
        self.device_combo.addItem("⏳ Загрузка...")
        self.mute_btn.setEnabled(False)
        self.unmute_btn.setEnabled(False)
        self.toggle_btn.setEnabled(False)

        # Принудительно очищаем кэш в контроллере, чтобы получить свежий список
        self.controller.devices_loaded = False
        self.controller.devices_cache = []
        self.controller.devices = []

        self.device_loader = DeviceLoader(self.controller)
        self.device_loader.devices_loaded.connect(self.on_devices_loaded)
        self.device_loader.start()

    def on_devices_loaded(self, devices):
        """
        Обработка загруженных устройств.

        Args:
            devices: Список устройств
        """
        if devices:
            self.update_devices_ui(devices)
        else:
            # Если устройств нет, показываем сообщение
            self.device_combo.clear()
            self.device_combo.addItem("❌ Устройства не найдены")
            self.device_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.show_loading_status("❌ Устройства не найдены", "#ef4444")
            self.show_notification("Ошибка", "Устройства записи не найдены")

        self.is_loading = False
        if self.device_loader:
            self.device_loader = None

    def update_devices_ui(self, devices):
        """
        Обновление UI с устройствами.
        Вызывается из главного потока через сигнал.

        Args:
            devices: Список устройств
        """
        self.device_combo.clear()

        if devices:
            for i, (name, id) in enumerate(devices, 1):
                display_name = name
                if len(display_name) > 50:
                    display_name = display_name[:47] + "..."
                self.device_combo.addItem(f"{i}. {display_name}", id)

            selected_index = 0
            if self.controller.active_device_id:
                found = False
                for i, (name, id) in enumerate(devices):
                    if id == self.controller.active_device_id:
                        selected_index = i
                        self.controller.selected_device_id = id
                        found = True
                        break

            self.device_combo.setCurrentIndex(selected_index)
            self.device_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.mute_btn.setEnabled(True)
            self.unmute_btn.setEnabled(True)
            self.toggle_btn.setEnabled(True)

            self.ui_initialized = True
            self.update_status_display()
            self.show_notification("Устройства", f"Загружено {len(devices)} микрофонов")
        else:
            self.device_combo.addItem("⏳ Загрузка...")
            self.device_combo.setEnabled(False)
            self.refresh_btn.setEnabled(True)  # Включаем кнопку обновления даже если устройств нет
            self.show_loading_status("⏳ Загрузка устройств...", "#a78bfa")

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        Использует UIBuilder для создания всех элементов.
        """
        self.setWindowTitle("MicroOff")
        self.setMinimumSize(540, 660)
        self.resize(580, 690)

        self.setWindowIcon(self.create_microphone_icon())

        # Создаем центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0a0a14, stop: 0.5 #1a1a2e, stop: 1 #0a0a14);
                border-radius: 10px;
            }
        """)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Строим интерфейс с помощью UIBuilder
        main_layout.addWidget(UIBuilder.build_title_bar(self))

        # Контейнер с содержимым
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(25, 20, 25, 20)

        # Добавляем все элементы интерфейса
        content_layout.addWidget(UIBuilder.build_header(self))
        content_layout.addWidget(UIBuilder.build_status_panel(self))
        content_layout.addWidget(UIBuilder.build_control_buttons(self))
        content_layout.addWidget(UIBuilder.build_separator())
        content_layout.addWidget(UIBuilder.build_device_selector(self))
        content_layout.addWidget(UIBuilder.build_separator())
        content_layout.addWidget(UIBuilder.build_hotkeys_panel())

        # Кнопка сворачивания в трей
        self.tray_btn = GlassButton("📥 Свернуть в системный трей")
        self.tray_btn.clicked.connect(self.hide_to_tray)
        content_layout.addWidget(self.tray_btn)

        # Добавляем растяжение
        content_layout.addStretch()

        main_layout.addWidget(content_widget)
        self.setCentralWidget(central_widget)

    def toggle_maximize(self):
        """
        Переключает режим развернутого окна.
        """
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def create_microphone_icon(self):
        """
        Создает иконку микрофона.

        Returns:
            QIcon: Иконка микрофона
        """
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
        return QIcon(pixmap)

    def load_cache_async(self):
        """
        Асинхронная загрузка кэша устройств из файла.
        Запускается в отдельном потоке, чтобы не блокировать интерфейс.
        Проверяет, определен ли active_device_id перед обновлением UI.
        """

        def load_cache_task():
            try:
                # Ждем, пока определится active_device_id
                timeout = 2
                start_time = time.time()
                while not self.controller.active_device_id and time.time() - start_time < timeout:
                    time.sleep(0.1)

                cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          'devices_cache.json')
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        devices = data.get('devices', [])
                        if devices:
                            self.controller.devices_cache = devices
                            self.controller.devices = devices
                            self.controller.devices_loaded = True
                            # Обновляем UI через сигнал с уже определенным active_device_id
                            self.update_devices_ui_signal.emit(devices)
                        else:
                            print("⚠️ Кэш пуст, будет выполнена полная загрузка")
                else:
                    print("ℹ️ Файл кэша не найден, будет выполнена полная загрузка")
            except Exception as e:
                Logger.log_error("Ошибка асинхронной загрузки кэша", e)
                print(f"❌ Ошибка загрузки кэша: {e}")

        threading.Thread(target=load_cache_task, daemon=True).start()

    def on_device_changed(self, index):
        """
        Обработка изменения выбранного устройства.

        Args:
            index: Индекс в комбобоксе
        """
        if index >= 0 and self.device_combo.isEnabled():
            device_id = self.device_combo.itemData(index)
            if device_id:
                self.device_combo.setEnabled(False)
                success = self.controller.set_device_fast(device_id)
                self.device_combo.setEnabled(True)
                if success:
                    self.update_status_display()
                    current_text = self.device_combo.currentText()
                    self.show_notification("Микрофон", f"Выбран: {current_text}")
                else:
                    self.show_notification("Ошибка", "Не удалось выбрать микрофон")

    def show_loading_status(self, text, color="#a78bfa"):
        """
        Отображает статус загрузки.

        Args:
            text: Текст статуса
            color: Цвет статуса
        """
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {color};
            background: transparent;
        """)
        self.status_indicator.setStyleSheet(f"""
            QLabel {{
                border-radius: 10px;
                background-color: {color};
                border: 2px solid {color};
            }}
        """)

    def setup_tray(self):
        """
        Настраивает системный трей.
        """
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()

    def start_status_updater(self):
        """
        Запускает поток обновления статуса.
        """
        self.worker = MicrophoneWorker(self.controller)
        self.worker.signals.status_updated.connect(self.on_status_updated)
        self.worker.start()

    def on_status_updated(self, status):
        """
        Обработка обновления статуса.

        Args:
            status: Новый статус mute
        """
        self.controller.mute_status = status
        if self.device_combo.isEnabled():
            self.update_status_display()

    def update_status_display(self):
        """
        Обновляет отображение статуса микрофона.
        """
        try:
            if self.controller.mute_status:
                self.status_label.setText("🔇 ВЫКЛЮЧЕН")
                self.status_label.setStyleSheet("""
                    font-size: 22px; 
                    font-weight: 700; 
                    color: #ef4444;
                    background: transparent;
                """)
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        border-radius: 10px;
                        background-color: #ef4444;
                        border: 2px solid #ef4444;
                    }
                """)
                self.tray_icon.setToolTip("Микрофон выключен")
            else:
                self.status_label.setText("🎤 ВКЛЮЧЕН")
                self.status_label.setStyleSheet("""
                    font-size: 22px; 
                    font-weight: 700; 
                    color: #22c55e;
                    background: transparent;
                """)
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        border-radius: 10px;
                        background-color: #22c55e;
                        border: 2px solid #22c55e;
                    }
                """)
                self.tray_icon.setToolTip("Микрофон включен")
        except Exception as e:
            Logger.log_error("Ошибка обновления статуса", e)

    def toggle_microphone(self):
        """
        Переключает состояние микрофона.
        """
        try:
            status = self.controller.toggle()
            self.update_status_display()
            self.show_notification("Микрофон", "ВКЛЮЧЕН" if not status else "ВЫКЛЮЧЕН")
        except Exception as e:
            Logger.log_error("Ошибка переключения", e)

    def mute_microphone(self):
        """
        Выключает микрофон.
        """
        try:
            self.controller.mute()
            self.update_status_display()
            self.show_notification("Микрофон", "ВЫКЛЮЧЕН")
        except Exception as e:
            Logger.log_error("Ошибка выключения", e)

    def unmute_microphone(self):
        """
        Включает микрофон.
        """
        try:
            self.controller.unmute()
            self.update_status_display()
            self.show_notification("Микрофон", "ВКЛЮЧЕН")
        except Exception as e:
            Logger.log_error("Ошибка включения", e)

    def hide_to_tray(self):
        """
        Скрывает окно в системный трей.
        """
        self.hide()
        self.tray_icon.showMessage(
            "MicroOff",
            "Приложение свернуто в системный трей",
            QSystemTrayIcon.Information,
            2000
        )

    def show_notification(self, title, message):
        """
        Показывает уведомление.

        Args:
            title: Заголовок уведомления
            message: Текст уведомления
        """
        try:
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                2000
            )
        except Exception as e:
            Logger.log_error("Ошибка показа уведомления", e)

    def mousePressEvent(self, event):
        """
        Обработка нажатия мыши для перетаскивания окна.

        Args:
            event: Событие мыши
        """
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Обработка движения мыши для перетаскивания окна.

        Args:
            event: Событие мыши
        """
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event):
        """
        Перехват клавиш F2-F6, чтобы не дублировать горячие клавиши.
        Полностью блокируем все события для этих клавиш в приложении.

        Args:
            event: Событие клавиатуры
        """
        if event.key() in (Qt.Key_F2, Qt.Key_F3, Qt.Key_F4, Qt.Key_F5, Qt.Key_F6):
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        Перехват отпускания клавиш F2-F6.
        Полностью блокируем все события для этих клавиш в приложении.

        Args:
            event: Событие клавиатуры
        """
        if event.key() in (Qt.Key_F2, Qt.Key_F3, Qt.Key_F4, Qt.Key_F5, Qt.Key_F6):
            event.accept()
            return
        super().keyReleaseEvent(event)

    def closeEvent(self, event):
        """
        Обработка закрытия окна.
        Полностью завершает приложение.

        Args:
            event: Событие закрытия
        """
        print("Закрытие программы")

        # Останавливаем рабочий поток
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None

        # Останавливаем загрузчик устройств
        if hasattr(self, 'device_loader') and self.device_loader:
            self.device_loader.quit()
            self.device_loader.wait()
            self.device_loader = None

        # Закрываем контроллер
        if hasattr(self, 'controller'):
            self.controller.close()

        # Отключаем горячие клавиши
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.unregister_hotkeys()

        event.accept()
        QApplication.quit()

    def __del__(self):
        """
        Деструктор для очистки ресурсов.
        """
        try:
            if hasattr(self, 'worker') and self.worker:
                self.worker.stop()
                self.worker.wait()
            if hasattr(self, 'device_loader') and self.device_loader:
                self.device_loader.quit()
                self.device_loader.wait()
            if hasattr(self, 'controller'):
                self.controller.close()
            if hasattr(self, 'hotkey_manager'):
                self.hotkey_manager.unregister_hotkeys()
        except Exception as e:
            Logger.log_error("Ошибка в деструкторе", e)
"""
Модуль с рабочими потоками для фоновых задач.
Содержит классы для обновления статуса и загрузки устройств.
"""

import time
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from src.logger import Logger


class WorkerSignals(QObject):
    """
    Сигналы для потока обновления статуса.
    """
    status_updated = pyqtSignal(bool)


class MicrophoneWorker(QThread):
    """
    Поток для фонового обновления статуса микрофона.
    """

    def __init__(self, controller):
        """
        Инициализация рабочего потока.

        Args:
            controller: Контроллер микрофона
        """
        super().__init__()
        self.controller = controller
        self.running = True
        self.signals = WorkerSignals()

    def run(self):
        """
        Основной цикл обновления статуса.
        """
        while self.running:
            try:
                if self.controller.is_initialized:
                    status = self.controller.update_status_fast()
                    self.signals.status_updated.emit(status)
                time.sleep(0.5)
            except Exception as e:
                Logger.log_error("Ошибка в потоке обновления статуса", e)
                time.sleep(0.5)

    def stop(self):
        """
        Останавливает рабочий поток.
        """
        self.running = False


class DeviceLoader(QThread):
    """
    Поток для асинхронной загрузки устройств.
    """
    devices_loaded = pyqtSignal(list)

    def __init__(self, controller):
        """
        Инициализация загрузчика устройств.

        Args:
            controller: Контроллер микрофона
        """
        super().__init__()
        self.controller = controller

    def run(self):
        """
        Загружает устройства в фоновом режиме.
        """
        try:
            # Ждем инициализации PowerShell
            timeout = 10
            start_time = time.time()
            while not self.controller.is_initialized and time.time() - start_time < timeout:
                time.sleep(0.3)

            # Принудительно получаем свежий список устройств
            devices = self.controller.get_devices()

            # Если устройств нет, пробуем еще раз с полной перезагрузкой
            if not devices:
                # Сбрасываем кэш и пробуем снова
                self.controller.devices_loaded = False
                self.controller.devices_cache = []
                devices = self.controller.get_devices()

            self.devices_loaded.emit(devices)
        except Exception as e:
            Logger.log_error("Ошибка загрузки устройств", e)
            self.devices_loaded.emit([])
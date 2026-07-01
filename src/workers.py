"""
Модуль с рабочими потоками для фоновых задач.
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
    Получает реальный статус из системы с периодическим опросом.
    """

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True
        self.signals = WorkerSignals()
        self.last_status = None

    def run(self):
        """
        Основной цикл - опрашивает статус микрофона.
        """
        while self.running:
            try:
                # Получаем реальный статус из системы
                status = self.controller.get_mute_status()
                if self.last_status != status:
                    self.last_status = status
                    self.signals.status_updated.emit(status)
                time.sleep(0.3)
            except Exception as e:
                Logger.log_error("Ошибка в потоке обновления статуса", e)
                time.sleep(1)

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
        super().__init__()
        self.controller = controller

    def run(self):
        """
        Загружает устройства в фоновом режиме.
        """
        try:
            devices = self.controller.get_devices(force_refresh=True)
            self.devices_loaded.emit(devices)
        except Exception as e:
            Logger.log_error("Ошибка загрузки устройств", e)
            self.devices_loaded.emit([])
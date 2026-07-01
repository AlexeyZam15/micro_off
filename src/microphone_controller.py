"""
Модуль контроллера микрофона.
Управляет устройствами записи через PowerShell и AudioDeviceCmdlets.
"""

import subprocess
import threading
import json
import os
import time
from datetime import datetime
from src.logger import Logger

# Файл кэша
CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devices_cache.json')


class MicrophoneController:
    """
    Контроллер для управления микрофоном через PowerShell.
    Позволяет получать список устройств, переключать их и управлять mute.
    """

    def __init__(self):
        """
        Инициализация контроллера микрофона.
        Запускает фоновые потоки для предзагрузки устройств и инициализации PowerShell.
        """
        self.process = None
        self.mute_status = False
        self.current_device = None
        self.devices = []
        self.selected_device_id = None
        self.lock = threading.Lock()
        self.is_initialized = False
        self.init_error = None
        self.devices_loaded = False
        self.devices_cache = []
        self.active_device_id = None

        print("Запуск контроллера")
        threading.Thread(target=self.preload_devices, daemon=True).start()
        threading.Thread(target=self.init_powershell, daemon=True).start()

    def get_active_device(self):
        """
        Получает ID активного устройства записи.

        Returns:
            str: ID активного устройства или None в случае ошибки
        """
        try:
            command = 'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; (Get-AudioDevice -Recording).ID'
            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            Logger.log_error("Ошибка получения активного устройства", e)
            return None

    def preload_devices(self):
        """
        Предзагрузка устройств в фоновом режиме.
        Использует кэш или получает список через PowerShell.
        """
        try:
            print("Начинаем предзагрузку устройств...")

            # Получаем активное устройство
            self.active_device_id = self.get_active_device()
            print(f"Активное устройство ID: {self.active_device_id}")

            # Проверяем наличие кэша
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.devices_cache = data.get('devices', [])
                        if self.devices_cache:
                            self.devices = self.devices_cache
                            self.devices_loaded = True
                            print(f"Загружен кэш: {len(self.devices_cache)} устройств")
                            return
                except Exception as e:
                    Logger.log_error("Ошибка загрузки кэша", e)

            # Одна команда получает сразу и имена и ID
            command = 'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; Get-AudioDevice -List | Where-Object {$_.Type -eq "Recording"} | ForEach-Object { $_.Name + "|||" + $_.ID }'

            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            devices = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if '|||' in line:
                        name, id = line.split('|||', 1)
                        devices.append((name.strip(), id.strip()))

            if devices:
                self.devices_cache = devices
                self.devices = devices
                self.devices_loaded = True
                self.save_cache()
                print(f"Предзагружено устройств: {len(devices)}")
        except Exception as e:
            Logger.log_error("Ошибка предзагрузки", e)

    def save_cache(self):
        """
        Сохраняет список устройств в кэш-файл.
        """
        try:
            data = {
                'devices': self.devices_cache,
                'timestamp': time.time()
            }
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            Logger.log_error("Ошибка сохранения кэша", e)

    def init_powershell(self):
        """
        Инициализирует процесс PowerShell для работы с аудиоустройствами.

        Returns:
            bool: True если инициализация успешна, иначе False
        """
        try:
            cmd = 'powershell -NoExit -Command "chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; $script:dev = Get-AudioDevice -Recording"'
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(0.3)
            self.update_status()
            self.is_initialized = True
            print("PowerShell инициализирован")
            return True
        except Exception as e:
            self.init_error = str(e)
            Logger.log_error("Ошибка запуска PowerShell", e)
            return False

    def send_command(self, command):
        """
        Отправляет команду в процесс PowerShell.

        Args:
            command: Команда для выполнения

        Returns:
            bool: True если команда отправлена успешно
        """
        try:
            with self.lock:
                if self.process and self.process.stdin:
                    self.process.stdin.write(command + "\n")
                    self.process.stdin.flush()
                    return True
            return False
        except Exception as e:
            Logger.log_error("Ошибка отправки команды", e)
            return False

    def get_devices(self):
        """
        Получает список всех устройств записи.

        Returns:
            list: Список кортежей (имя_устройства, id_устройства)
        """
        if self.devices_loaded and self.devices_cache:
            return self.devices_cache

        try:
            # Одна команда получает сразу и имена и ID
            command = 'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; Get-AudioDevice -List | Where-Object {$_.Type -eq "Recording"} | ForEach-Object { $_.Name + "|||" + $_.ID }'

            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            devices = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if '|||' in line:
                        name, id = line.split('|||', 1)
                        devices.append((name.strip(), id.strip()))

            if devices:
                self.devices = devices
                self.devices_cache = devices
                self.devices_loaded = True
                self.save_cache()
                return devices

            return []
        except Exception as e:
            Logger.log_error("Ошибка получения устройств", e)
            return []

    def set_device_fast(self, device_id):
        """
        Быстрое переключение на указанное устройство.

        Args:
            device_id: ID устройства

        Returns:
            bool: True если переключение успешно
        """
        try:
            self.selected_device_id = device_id
            self.current_device = device_id

            command = f'Set-AudioDevice -ID "{device_id}" -Recording'

            if self.process and self.process.stdin:
                with self.lock:
                    self.process.stdin.write(
                        f'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; {command}\n')
                    self.process.stdin.flush()

            self.update_status_fast()
            return True
        except Exception as e:
            Logger.log_error("Ошибка установки устройства", e)
            return False

    def update_status_fast(self):
        """
        Быстрое обновление статуса mute.

        Returns:
            bool: Текущий статус mute
        """
        try:
            if self.selected_device_id:
                command = f'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; $dev = Get-AudioDevice -Recording | Where-Object {{$_.ID -eq "{self.selected_device_id}"}}; if ($dev) {{ $dev.Device.AudioEndpointVolume.Mute }}'
            else:
                command = 'chcp 65001 > $null; Import-Module AudioDeviceCmdlets -Force; $dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute'

            result = subprocess.run(
                ['powershell', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0 and result.stdout.strip():
                self.mute_status = result.stdout.strip() == "True"
            return self.mute_status
        except Exception as e:
            Logger.log_error("Ошибка обновления статуса", e)
            return self.mute_status

    def update_status(self):
        """
        Обновляет статус mute.

        Returns:
            bool: Текущий статус mute
        """
        return self.update_status_fast()

    def toggle(self):
        """
        Переключает состояние mute.

        Returns:
            bool: Новый статус mute
        """
        self.mute_status = not self.mute_status
        if self.selected_device_id:
            cmd = f'$dev = Get-AudioDevice -Recording | Where-Object {{$_.ID -eq "{self.selected_device_id}"}}; if ($dev) {{ $dev.Device.AudioEndpointVolume.Mute = ${str(self.mute_status).lower()} }}'
        else:
            cmd = f'$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = ${str(self.mute_status).lower()}'
        self.send_command(cmd)
        return self.mute_status

    def mute(self):
        """
        Выключает микрофон.

        Returns:
            bool: True
        """
        self.mute_status = True
        if self.selected_device_id:
            cmd = f'$dev = Get-AudioDevice -Recording | Where-Object {{$_.ID -eq "{self.selected_device_id}"}}; if ($dev) {{ $dev.Device.AudioEndpointVolume.Mute = $true }}'
        else:
            cmd = '$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = $true'
        self.send_command(cmd)
        return True

    def unmute(self):
        """
        Включает микрофон.

        Returns:
            bool: False
        """
        self.mute_status = False
        if self.selected_device_id:
            cmd = f'$dev = Get-AudioDevice -Recording | Where-Object {{$_.ID -eq "{self.selected_device_id}"}}; if ($dev) {{ $dev.Device.AudioEndpointVolume.Mute = $false }}'
        else:
            cmd = '$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = $false'
        self.send_command(cmd)
        return False

    def close(self):
        """
        Закрывает процесс PowerShell.
        """
        try:
            if self.process:
                self.process.terminate()
                self.process = None
            print("PowerShell закрыт")
        except Exception as e:
            Logger.log_error("Ошибка закрытия PowerShell", e)
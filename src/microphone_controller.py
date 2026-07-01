"""
Модуль контроллера микрофона.

Управляет устройствами записи через PowerShell и AudioDeviceCmdlets.
"""

import subprocess
import threading
import json
import os
import time
import base64
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
        self.powershell_process = None
        self.device_list_lock = threading.Lock()
        self.module_available = False

        print("Запуск контроллера")

        # Проверяем наличие модуля синхронно
        self._check_module_sync()

        # Запускаем долгоживущий PowerShell процесс
        threading.Thread(target=self._init_powershell, daemon=True).start()

    def _check_module_sync(self):
        """
        Синхронная проверка наличия модуля AudioDeviceCmdlets.
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 'if (Get-Module -ListAvailable -Name AudioDeviceCmdlets) { Write-Output "true" } else { Write-Output "false" }'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.module_available = result.stdout.strip().lower() == 'true'

            if self.module_available:
                print("✅ Модуль AudioDeviceCmdlets найден")
            else:
                print(
                    "⚠️ Модуль AudioDeviceCmdlets не найден, нужно установить: Install-Module AudioDeviceCmdlets -Force")
        except Exception as e:
            print(f"❌ Ошибка проверки модуля: {e}")
            self.module_available = False

    def _init_powershell(self):
        """
        Инициализирует долгоживущий процесс PowerShell.
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.powershell_process = subprocess.Popen(
                ['powershell', '-NoProfile', '-Command',
                 'Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue -Force; while ($true) { $cmd = Read-Host; if ($cmd -eq "EXIT") { break }; Invoke-Expression $cmd }'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self.is_initialized = True
            print("✅ PowerShell инициализирован")

            # Запускаем поток чтения вывода (чтобы не блокировать)
            threading.Thread(target=self._read_output, daemon=True).start()

        except Exception as e:
            self.init_error = str(e)
            Logger.log_error("Ошибка инициализации PowerShell", e)
            print(f"❌ Ошибка инициализации: {e}")

    def _read_output(self):
        """
        Читает вывод PowerShell в фоне.
        """
        while self.powershell_process and self.powershell_process.poll() is None:
            try:
                line = self.powershell_process.stdout.readline()
                if not line:
                    break
                if line.strip():
                    print(f"PowerShell: {line.strip()}")
            except:
                break

    def _send_command_async(self, command):
        """
        Отправляет команду в PowerShell асинхронно (мгновенно).
        """
        if not self.is_initialized or not self.powershell_process:
            self._send_command_sync(command)
            return

        try:
            with self.lock:
                if self.powershell_process and self.powershell_process.stdin:
                    self.powershell_process.stdin.write(command + "\n")
                    self.powershell_process.stdin.flush()
        except Exception as e:
            Logger.log_error("Ошибка отправки команды", e)
            self._send_command_sync(command)

    def _send_command_sync(self, command):
        """
        Синхронное выполнение команды (запасной вариант).
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            full_command = f'Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue -Force; {command}'

            subprocess.run(
                ['powershell', '-NoProfile', '-Command', full_command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            Logger.log_error("Ошибка синхронного выполнения", e)

    def get_active_device(self):
        """
        Получает ID активного устройства записи.
        """
        if not self.module_available:
            return None

        try:
            command = 'Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue -Force; (Get-AudioDevice -Recording).ID'

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except Exception as e:
            Logger.log_error("Ошибка получения активного устройства", e)
            return None

    def load_from_cache(self):
        """
        Загружает устройства из кэша.

        Returns:
            bool: True если кэш загружен, False если нет
        """
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cached_devices = data.get('devices', [])
                    if cached_devices:
                        with self.device_list_lock:
                            self.devices_cache = cached_devices
                            self.devices = cached_devices
                            self.devices_loaded = True
                        print(f"✅ Загружен кэш: {len(self.devices_cache)} устройств")
                        return True
            return False
        except Exception as e:
            Logger.log_error("Ошибка загрузки кэша", e)
            return False

    def get_devices_from_powershell(self):
        """
        Получает список устройств записи через PowerShell с Base64 для русских букв.
        """
        if not self.module_available:
            print("⚠️ Модуль AudioDeviceCmdlets не установлен")
            return []

        try:
            # Используем Base64 для сохранения русских букв
            command = '''
            Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue -Force;
            $devices = Get-AudioDevice -List | Where-Object {$_.Type -eq "Recording"};
            $result = @();
            foreach ($dev in $devices) {
                $nameBytes = [System.Text.Encoding]::UTF8.GetBytes($dev.Name);
                $nameBase64 = [Convert]::ToBase64String($nameBytes);
                $idBytes = [System.Text.Encoding]::UTF8.GetBytes($dev.ID);
                $idBase64 = [Convert]::ToBase64String($idBytes);
                $result += "$nameBase64|||$idBase64";
            }
            Write-Output ($result -join "`n");
            '''

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            devices = []
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')

                for line in lines:
                    if not line.strip():
                        continue

                    if '|||' in line:
                        parts = line.split('|||', 1)
                        if len(parts) == 2:
                            name_base64 = parts[0].strip()
                            id_base64 = parts[1].strip()
                            if name_base64 and id_base64:
                                try:
                                    name_bytes = base64.b64decode(name_base64)
                                    name = name_bytes.decode('utf-8')

                                    id_bytes = base64.b64decode(id_base64)
                                    device_id = id_bytes.decode('utf-8')

                                    devices.append((name, device_id))
                                except Exception as e:
                                    continue

            if devices:
                print(f"✅ Найдено устройств: {len(devices)}")
                return devices

            print("⚠️ Устройства не найдены")
            return []
        except Exception as e:
            Logger.log_error("Ошибка получения устройств", e)
            print(f"❌ Ошибка получения устройств: {e}")
            return []

    def save_cache(self):
        """
        Сохраняет кэш устройств в UTF-8.
        """
        try:
            with self.device_list_lock:
                data = {
                    'devices': self.devices_cache,
                    'timestamp': time.time()
                }
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Кэш сохранен: {len(self.devices_cache)} устройств")
        except Exception as e:
            Logger.log_error("Ошибка сохранения кэша", e)

    def get_devices(self, force_refresh=False):
        """
        Получает список всех устройств записи.

        Args:
            force_refresh: Принудительное обновление (игнорирует кэш)
        """
        with self.device_list_lock:
            if not force_refresh and self.devices_loaded and self.devices_cache:
                return self.devices_cache

        if not self.module_available:
            print("⚠️ Модуль не доступен, используем кэш")
            return self.devices_cache if self.devices_cache else []

        devices = self.get_devices_from_powershell()
        if devices:
            with self.device_list_lock:
                self.devices = devices
                self.devices_cache = devices
                self.devices_loaded = True
            self.save_cache()
            return devices

        if self.devices_cache:
            print("⚠️ Используем сохраненный кэш")
            return self.devices_cache

        return []

    def set_device_fast(self, device_id):
        """
        Мгновенное переключение на указанное устройство.
        """
        try:
            with self.device_list_lock:
                self.selected_device_id = device_id
                self.current_device = device_id

            command = f'Set-AudioDevice -ID "{device_id}"'
            self._send_command_async(command)

            return True
        except Exception as e:
            Logger.log_error("Ошибка установки устройства", e)
            return False

    def toggle(self):
        """
        Мгновенное переключение состояния mute.
        """
        self.mute_status = not self.mute_status
        command = f'$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = ${str(self.mute_status).lower()}'
        self._send_command_async(command)
        return self.mute_status

    def mute(self):
        """
        Мгновенное выключение микрофона.
        """
        self.mute_status = True
        command = '$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = $true'
        self._send_command_async(command)
        return True

    def unmute(self):
        """
        Мгновенное включение микрофона.
        """
        self.mute_status = False
        command = '$dev = Get-AudioDevice -Recording; $dev.Device.AudioEndpointVolume.Mute = $false'
        self._send_command_async(command)
        return False

    def unmute_all_devices(self):
        """
        Быстрое включение всех устройств записи (сброс).
        """
        try:
            devices = self.get_devices()
            if not devices:
                return False

            for name, device_id in devices:
                try:
                    self.set_device_fast(device_id)
                    self.unmute()
                except:
                    continue

            if self.active_device_id:
                self.set_device_fast(self.active_device_id)

            print("✅ Все устройства включены")
            return True
        except Exception as e:
            Logger.log_error("Ошибка включения всех устройств", e)
            return False

    def get_mute_status(self):
        """
        Получает текущий статус MUTE.
        """
        if not self.module_available:
            return self.mute_status

        try:
            command = '(Get-AudioDevice -Recording).Device.AudioEndpointVolume.Mute'

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 f'Import-Module AudioDeviceCmdlets -ErrorAction SilentlyContinue -Force; {command}'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0 and result.stdout.strip():
                self.mute_status = result.stdout.strip().lower() == "true"
            return self.mute_status
        except Exception as e:
            Logger.log_error("Ошибка получения статуса", e)
            return self.mute_status

    def update_status_display(self):
        """
        Возвращает текущий статус для отображения в интерфейсе.
        НЕ ОБРАЩАЕТСЯ К СИСТЕМЕ!
        """
        return self.mute_status

    def close(self):
        """
        Закрывает ресурсы.
        """
        try:
            if self.powershell_process:
                try:
                    self.powershell_process.stdin.write("EXIT\n")
                    self.powershell_process.stdin.flush()
                except:
                    pass
                self.powershell_process.terminate()
                self.powershell_process = None
            print("✅ Контроллер закрыт")
        except Exception as e:
            Logger.log_error("Ошибка закрытия", e)
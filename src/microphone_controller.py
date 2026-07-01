"""
Модуль контроллера микрофона.

Управляет устройствами записи через библиотеку pycaw (Windows Core Audio API).
Обеспечивает быстрое и надежное управление микрофоном без PowerShell.
"""

import os
import json
import time
import threading
from datetime import datetime
from comtypes import CoInitialize, CoUninitialize, cast, POINTER
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume,
    EDataFlow,
    ERole,
    IMMDeviceEnumerator,
    IMMDevice
)

from src.logger import Logger


class MicrophoneController:
    """
    Контроллер для управления микрофоном через pycaw.
    Позволяет получать список устройств, переключать их и управлять mute.
    """

    def __init__(self):
        """
        Инициализация контроллера микрофона.
        """
        self.mute_status = False
        self.current_device = None
        self.devices = []
        self.selected_device_id = None
        self.active_device_id = None
        self.active_device_name = None
        self.devices_loaded = False
        self.device_list_lock = threading.Lock()
        self._com_lock = threading.Lock()
        self._com_initialized = False
        self._default_device_cache = None
        self._default_device_name_cache = None

        print("Запуск контроллера микрофона (pycaw)")

        # Инициализируем COM в основном потоке
        self._init_com()

    def _init_com(self):
        """
        Инициализирует COM в текущем потоке.
        """
        with self._com_lock:
            try:
                CoInitialize()
                self._com_initialized = True
                print("✅ COM инициализирован")
            except Exception as e:
                if "already initialized" in str(e).lower():
                    self._com_initialized = True
                else:
                    print(f"❌ Ошибка инициализации COM: {e}")
                    Logger.log_error("Ошибка инициализации COM", e)

    def _ensure_com_for_thread(self):
        """
        Гарантирует, что COM инициализирован для текущего потока.
        """
        try:
            CoInitialize()
            return True
        except Exception as e:
            if "already initialized" in str(e).lower():
                return True
            return False

    def _get_device_friendly_name(self, device):
        """
        Получает дружественное имя устройства из IMMDevice или AudioDevice.

        Args:
            device: IMMDevice или AudioDevice объект

        Returns:
            str: Имя устройства
        """
        try:
            # Если это AudioDevice из pycaw
            if hasattr(device, 'FriendlyName'):
                return device.FriendlyName

            # Если это IMMDevice - пробуем через PropertyStore
            if hasattr(device, 'OpenPropertyStore'):
                try:
                    from comtypes import GUID
                    from pycaw.pycaw import PROPERTYKEY
                    store = device.OpenPropertyStore(0)

                    pkey = PROPERTYKEY()
                    pkey.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
                    pkey.pid = 14

                    prop_value = store.GetValue(pkey)
                    if prop_value:
                        if hasattr(prop_value, 'value'):
                            return str(prop_value.value)
                        return str(prop_value)
                except Exception as e:
                    pass

            # Пробуем через GetId
            if hasattr(device, 'GetId'):
                try:
                    device_id = device.GetId()
                    import re
                    match = re.search(r'#{([^}]+)}', device_id)
                    if match:
                        return match.group(1)[:30]
                    return device_id.split('\\')[-1][:30]
                except:
                    pass

            return "Unknown Device"

        except Exception as e:
            return "Unknown Device"

    def _get_device_id(self, device):
        """
        Получает ID устройства из IMMDevice или AudioDevice.

        Args:
            device: IMMDevice или AudioDevice объект

        Returns:
            str: ID устройства
        """
        try:
            if hasattr(device, 'id'):
                return device.id

            if hasattr(device, 'GetId'):
                return device.GetId()

            return None
        except Exception as e:
            return None

    def _get_device_volume_interface_from_device(self, device):
        """
        Получает интерфейс громкости из IMMDevice или AudioDevice.

        Args:
            device: IMMDevice или AudioDevice объект

        Returns:
            IAudioEndpointVolume или None
        """
        try:
            if hasattr(device, 'EndpointVolume') and device.EndpointVolume:
                return device.EndpointVolume

            if hasattr(device, 'Activate'):
                try:
                    interface = device.Activate(
                        IAudioEndpointVolume._iid_,
                        0,
                        None
                    )
                    return cast(interface, POINTER(IAudioEndpointVolume))
                except Exception as e:
                    return None

            return None
        except Exception as e:
            return None

    def get_all_devices(self):
        """
        Получает все активные устройства записи через pycaw.

        Returns:
            list: Список объектов устройств (AudioDevice или IMMDevice)
        """
        try:
            if not self._ensure_com_for_thread():
                return []

            # Пробуем получить устройства через GetAllDevices
            try:
                devices = AudioUtilities.GetAllDevices(
                    data_flow=EDataFlow.eCapture.value,
                    device_state=1
                )
                if devices and len(devices) > 0:
                    return devices
            except Exception as e:
                pass

            # Пробуем через DeviceEnumerator
            try:
                device_enumerator = AudioUtilities.GetDeviceEnumerator()
                collection = device_enumerator.EnumAudioEndpoints(
                    EDataFlow.eCapture.value,
                    0x00000001
                )
                count = collection.GetCount()

                if count > 0:
                    devices = []
                    for i in range(count):
                        device = collection.Item(i)
                        devices.append(device)
                    return devices
            except Exception as e:
                pass

            return []

        except Exception as e:
            Logger.log_error("Ошибка получения устройств", e)
            return []

    def _get_default_microphone_device(self):
        """
        Получает устройство микрофона по умолчанию (с кэшированием).

        Returns:
            IMMDevice или AudioDevice объект, или None
        """
        try:
            if not self._ensure_com_for_thread():
                return None

            # Пробуем через GetMicrophone (AudioDevice)
            try:
                device = AudioUtilities.GetMicrophone()
                if device:
                    return device
            except Exception as e:
                pass

            # Пробуем через DeviceEnumerator
            try:
                device_enumerator = AudioUtilities.GetDeviceEnumerator()
                device = device_enumerator.GetDefaultAudioEndpoint(
                    EDataFlow.eCapture.value,
                    ERole.eMultimedia.value
                )
                if device:
                    return device
            except Exception as e:
                pass

            return None

        except Exception as e:
            Logger.log_error("Ошибка получения дефолтного микрофона", e)
            return None

    def get_active_microphone_info(self):
        """
        Получает информацию об активном микрофоне по умолчанию.
        Использует кэширование для предотвращения спама.

        Returns:
            tuple: (имя_устройства, id_устройства) или None
        """
        try:
            # Проверяем кэш
            if self._default_device_cache is not None:
                return (self._default_device_name_cache, self._default_device_cache)

            device = self._get_default_microphone_device()
            if not device:
                # Если нет дефолтного, берем первое устройство
                devices = self.get_all_devices()
                if devices:
                    device = devices[0]
                else:
                    return None

            name = self._get_device_friendly_name(device)
            device_id = self._get_device_id(device)

            if name and device_id:
                # Сохраняем в кэш
                self._default_device_cache = device_id
                self._default_device_name_cache = name
                return (name, device_id)

            return None

        except Exception as e:
            Logger.log_error("Ошибка получения активного микрофона", e)
            return None

    def clear_default_device_cache(self):
        """
        Очищает кэш дефолтного устройства.
        Вызывается при обновлении устройств.
        """
        self._default_device_cache = None
        self._default_device_name_cache = None

    def get_device_by_id(self, device_id):
        """
        Находит устройство по ID.

        Args:
            device_id: ID устройства

        Returns:
            Устройство (AudioDevice или IMMDevice) или None
        """
        try:
            if not self._ensure_com_for_thread():
                return None

            devices = self.get_all_devices()
            for device in devices:
                dev_id = self._get_device_id(device)
                if dev_id == device_id:
                    return device
            return None
        except Exception as e:
            Logger.log_error("Ошибка поиска устройства по ID", e)
            return None

    def get_device_volume_interface(self, device_id=None):
        """
        Получает интерфейс IAudioEndpointVolume для устройства.

        Args:
            device_id: ID устройства (если None, используется активное)

        Returns:
            IAudioEndpointVolume или None
        """
        try:
            if not self._ensure_com_for_thread():
                return None

            # Если device_id не указан, используем сохраненный активный
            if device_id is None:
                device_id = self.active_device_id

            if device_id:
                device = self.get_device_by_id(device_id)
            else:
                # Пытаемся получить дефолтное устройство
                device = self._get_default_microphone_device()
                if not device:
                    # Берем первое устройство из списка
                    devices = self.get_all_devices()
                    if devices:
                        device = devices[0]
                    else:
                        return None

            if not device:
                return None

            return self._get_device_volume_interface_from_device(device)

        except Exception as e:
            Logger.log_error("Ошибка получения интерфейса громкости", e)
            return None

    def get_devices(self, force_refresh=False):
        """
        Получает список всех устройств записи.

        Args:
            force_refresh: Принудительное обновление

        Returns:
            list: Список кортежей (имя_устройства, id_устройства)
        """
        # При принудительном обновлении очищаем кэш дефолтного устройства
        if force_refresh:
            self.clear_default_device_cache()

        devices = self.get_devices_from_pycaw()

        if devices:
            with self.device_list_lock:
                self.devices = devices
                self.devices_loaded = True

            # Получаем активный микрофон только при первом запуске или принудительном обновлении
            if force_refresh or not self.active_device_id:
                active_info = self.get_active_microphone_info()
                if active_info:
                    active_name, active_id = active_info
                    self.active_device_id = active_id
                    self.active_device_name = active_name
                    print(f"✅ Активный микрофон: {active_name}")

            return devices

        print("❌ Устройства не найдены")
        return []

    def get_devices_from_pycaw(self):
        """
        Получает список устройств записи через pycaw.

        Returns:
            list: Список кортежей (имя_устройства, id_устройства)
        """
        try:
            devices = self.get_all_devices()
            result = []

            if not devices:
                return []

            for device in devices:
                name = self._get_device_friendly_name(device)
                device_id = self._get_device_id(device)

                if name and device_id:
                    result.append((name, device_id))
                elif name:
                    result.append((name, str(device)))

            if result:
                print(f"✅ Найдено устройств: {len(result)}")
                for i, (name, device_id) in enumerate(result, 1):
                    print(f"  {i}. {name}")
                return result

            return []

        except Exception as e:
            Logger.log_error("Ошибка получения устройств из pycaw", e)
            return []

    def set_device_fast(self, device_id):
        """
        Устанавливает активное устройство.

        Args:
            device_id: ID устройства

        Returns:
            bool: True если успешно
        """
        try:
            self.active_device_id = device_id
            with self.device_list_lock:
                self.selected_device_id = device_id
                self.current_device = device_id

            print(f"✅ Выбрано устройство: {device_id}")
            return True
        except Exception as e:
            Logger.log_error("Ошибка установки устройства", e)
            return False

    def toggle(self):
        """
        Переключает состояние mute.

        Returns:
            bool: Новый статус (True - выключен, False - включен)
        """
        try:
            volume = self.get_device_volume_interface()
            if volume:
                current = volume.GetMute()
                new_status = not current
                volume.SetMute(new_status, None)
                self.mute_status = new_status
                print(f"🔄 Микрофон переключен: {'ВЫКЛЮЧЕН' if new_status else 'ВКЛЮЧЕН'}")
                return new_status
            else:
                print("❌ Не удалось получить интерфейс громкости")
                return self.mute_status
        except Exception as e:
            Logger.log_error("Ошибка переключения", e)
            return self.mute_status

    def mute(self):
        """
        Выключает микрофон.

        Returns:
            bool: True если успешно
        """
        try:
            volume = self.get_device_volume_interface()
            if volume:
                volume.SetMute(True, None)
                self.mute_status = True
                print("🔇 Микрофон выключен")
                return True
            else:
                print("❌ Не удалось получить интерфейс громкости")
                return False
        except Exception as e:
            Logger.log_error("Ошибка выключения", e)
            return False

    def unmute(self):
        """
        Включает микрофон.

        Returns:
            bool: True если успешно
        """
        try:
            volume = self.get_device_volume_interface()
            if volume:
                volume.SetMute(False, None)
                self.mute_status = False
                print("🎤 Микрофон включен")
                return True
            else:
                print("❌ Не удалось получить интерфейс громкости")
                return False
        except Exception as e:
            Logger.log_error("Ошибка включения", e)
            return False

    def unmute_all_devices(self):
        """
        Включает все устройства записи (сброс).

        Returns:
            bool: True если хотя бы одно устройство включено
        """
        try:
            devices = self.get_devices()
            if not devices:
                return False

            success_count = 0
            for name, device_id in devices:
                try:
                    volume = self.get_device_volume_interface(device_id)
                    if volume:
                        volume.SetMute(False, None)
                        success_count += 1
                        print(f"  ✅ Включен: {name}")
                except Exception as e:
                    print(f"  ❌ Ошибка при включении {name}: {e}")
                    continue

            print(f"Включено устройств: {success_count} из {len(devices)}")
            return success_count > 0
        except Exception as e:
            Logger.log_error("Ошибка включения всех устройств", e)
            return False

    def get_mute_status(self):
        """
        Получает текущий статус MUTE.

        Returns:
            bool: True если выключен, False если включен
        """
        try:
            # Добавляем небольшую задержку между вызовами
            if hasattr(self, '_last_mute_call'):
                elapsed = time.time() - self._last_mute_call
                if elapsed < 0.3:  # Не чаще чем раз в 300 мс
                    return self.mute_status

            self._last_mute_call = time.time()

            volume = self.get_device_volume_interface()
            if volume:
                self.mute_status = volume.GetMute()
                return self.mute_status
            return self.mute_status
        except Exception as e:
            Logger.log_error("Ошибка получения статуса", e)
            return self.mute_status

    def update_status_display(self):
        """
        Возвращает текущий статус для отображения в интерфейсе.

        Returns:
            bool: Статус mute
        """
        return self.mute_status

    def set_volume(self, volume_level):
        """
        Устанавливает громкость устройства.

        Args:
            volume_level: Уровень громкости (0-100)

        Returns:
            bool: True если успешно
        """
        try:
            volume = self.get_device_volume_interface()
            if volume:
                scalar = max(0, min(100, volume_level)) / 100.0
                volume.SetMasterVolumeLevelScalar(scalar, None)
                print(f"🔊 Громкость установлена на {volume_level}%")
                return True
            return False
        except Exception as e:
            Logger.log_error("Ошибка установки громкости", e)
            return False

    def get_volume(self):
        """
        Получает текущую громкость устройства.

        Returns:
            float: Громкость (0-100) или None
        """
        try:
            volume = self.get_device_volume_interface()
            if volume:
                return volume.GetMasterVolumeLevelScalar() * 100
            return None
        except Exception as e:
            Logger.log_error("Ошибка получения громкости", e)
            return None

    def close(self):
        """
        Закрывает ресурсы.
        """
        try:
            print("✅ Контроллер закрыт")
        except Exception as e:
            Logger.log_error("Ошибка закрытия", e)
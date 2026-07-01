"""
Модуль менеджера горячих клавиш для приложения MicroOff.
Обрабатывает глобальные горячие клавиши через библиотеку keyboard.
"""

import keyboard
import time
from src.logger import Logger


class HotkeyManager:
    """
    Менеджер для управления глобальными горячими клавишами.
    """

    def __init__(self, toggle_callback, mute_callback, unmute_callback):
        """
        Инициализация менеджера горячих клавиш.

        Args:
            toggle_callback: Функция для переключения микрофона
            mute_callback: Функция для выключения микрофона
            unmute_callback: Функция для включения микрофона
        """
        self.toggle_callback = toggle_callback
        self.mute_callback = mute_callback
        self.unmute_callback = unmute_callback
        self.hotkeys_registered = False
        # Состояние клавиш (нажата или нет)
        self.key_states = {
            'f4': False,
            'f2': False,
            'f3': False
        }

    def _handle_key_press(self, key_name, callback, event):
        """
        Обработчик нажатия клавиши.
        Срабатывает только при переходе из состояния "не нажата" в "нажата".

        Args:
            key_name: Имя клавиши
            callback: Функция для вызова
            event: Событие клавиатуры
        """
        # Проверяем, что клавиша была отпущена перед этим нажатием
        if self.key_states.get(key_name, False):
            # Клавиша уже нажата - игнорируем повторное срабатывание
            return

        # Отмечаем, что клавиша нажата
        self.key_states[key_name] = True

        try:
            callback()
        except Exception as e:
            Logger.log_error(f"Ошибка в обработчике клавиши {key_name}", e)

    def _handle_key_release(self, key_name, event):
        """
        Обработчик отпускания клавиши.
        Сбрасывает состояние клавиши.

        Args:
            key_name: Имя клавиши
            event: Событие клавиатуры
        """
        self.key_states[key_name] = False

    def register_hotkeys(self):
        """
        Регистрирует глобальные горячие клавиши.
        """
        try:
            # Регистрируем обработчики нажатия и отпускания для каждой клавиши
            keyboard.on_press_key('f4', lambda e: self._handle_key_press('f4', self.toggle_callback, e), suppress=True)
            keyboard.on_release_key('f4', lambda e: self._handle_key_release('f4', e), suppress=True)

            keyboard.on_press_key('f2', lambda e: self._handle_key_press('f2', self.mute_callback, e), suppress=True)
            keyboard.on_release_key('f2', lambda e: self._handle_key_release('f2', e), suppress=True)

            keyboard.on_press_key('f3', lambda e: self._handle_key_press('f3', self.unmute_callback, e), suppress=True)
            keyboard.on_release_key('f3', lambda e: self._handle_key_release('f3', e), suppress=True)

            self.hotkeys_registered = True
            print("Горячие клавиши зарегистрированы (F4 - переключить, F2 - выключить, F3 - включить)")
        except Exception as e:
            Logger.log_error("Ошибка настройки горячих клавиш", e)

    def unregister_hotkeys(self):
        """
        Удаляет регистрацию горячих клавиш.
        """
        try:
            keyboard.unhook_all()
            self.hotkeys_registered = False
            # Сбрасываем все состояния
            for key in self.key_states:
                self.key_states[key] = False
            print("Горячие клавиши удалены")
        except Exception as e:
            Logger.log_error("Ошибка удаления горячих клавиш", e)
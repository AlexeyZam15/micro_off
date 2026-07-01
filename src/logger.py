"""
Модуль логирования для приложения MicroOff.
Обеспечивает запись ошибок и отладочной информации в файл.
"""

import os
from datetime import datetime

# Файл логов
ERROR_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'error_log.txt')


class Logger:
    """
    Класс для логирования ошибок и событий.
    """

    @staticmethod
    def log_error(message, exception=None):
        """
        Записывает сообщение об ошибке в файл лога.

        Args:
            message: Текст сообщения
            exception: Объект исключения (опционально)
        """
        try:
            with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] ERROR: {message}\n")
                if exception:
                    f.write(f"Exception: {str(exception)}\n")
                    import traceback
                    f.write(traceback.format_exc())
                f.write("-" * 60 + "\n")
        except:
            pass
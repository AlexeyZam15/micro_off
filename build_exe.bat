@echo off

chcp 65001 >nul

title Сборка MicroOff

echo ========================================
echo   СБОРКА MicroOff
echo ========================================
echo.

:: Проверяем наличие pyinstaller
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo ❌ PyInstaller не найден!
    echo Установите: pip install pyinstaller
    pause
    exit /b 1
)

echo Очистка старых сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

echo Очистка кэша Python...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q src\__pycache__ 2>nul

echo Сборка исполняемого файла...
pyinstaller --onefile --windowed --name="MicroOff" --add-data "src;src" --hidden-import=PyQt5 --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets --hidden-import=keyboard --hidden-import=src --hidden-import=src.microphone_controller --hidden-import=src.main_window --hidden-import=src.logger --hidden-import=src.widgets --hidden-import=src.tray_icon --hidden-import=src.hotkey_manager --hidden-import=src.workers --hidden-import=src.ui_builder --hidden-import=subprocess --hidden-import=json --hidden-import=base64 --hidden-import=threading --hidden-import=time --collect-all PyQt5 --collect-all keyboard --clean --noconfirm --runtime-tmpdir="%TEMP%" micro_off.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка сборки!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ СБОРКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Исполняемый файл: dist\MicroOff.exe
echo.

pause
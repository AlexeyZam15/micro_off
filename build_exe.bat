@echo off

chcp 65001 >nul

title Сборка MicroOff (Single File)

echo ========================================
echo   СБОРКА MicroOff
echo ========================================
echo.

echo Очистка старых сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

echo Очистка кэша...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q src\__pycache__ 2>nul
rmdir /s /q src\controllers\__pycache__ 2>nul
rmdir /s /q src\models\__pycache__ 2>nul
rmdir /s /q src\views\__pycache__ 2>nul
rmdir /s /q src\utils\__pycache__ 2>nul

echo Сборка исполняемого файла...
pyinstaller --onefile --windowed --name="MicroOff" --add-data "src;src" --hidden-import=PyQt5 --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets --hidden-import=keyboard --hidden-import=ctypes --hidden-import=json --hidden-import=os --hidden-import=sys --hidden-import=threading --hidden-import=time --hidden-import=subprocess --hidden-import=datetime --hidden-import=src.logger --hidden-import=src.microphone_controller --hidden-import=src.widgets --hidden-import=src.tray_icon --hidden-import=src.hotkey_manager --hidden-import=src.workers --hidden-import=src.ui_builder --hidden-import=src.main_window --hidden-import=src --collect-all PyQt5 --collect-all keyboard --uac-admin --clean --noconfirm --runtime-tmpdir="%TEMP%" micro_off.py

echo.
echo ========================================
echo   СБОРКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Исполняемый файл: dist\MicroOff.exe
echo.
echo ВАЖНО: Добавьте файл в исключения антивируса!
echo.

pause
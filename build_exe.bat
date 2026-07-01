@echo off
chcp 65001 >nul
title Сборка MicroOff (с правами администратора)

echo ========================================
echo   СБОРКА MicroOff (через манифест)
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

echo.
echo Создание манифеста...

(
echo ^<?xml version="1.0" encoding="UTF-8" standalone="yes"?^>
echo ^<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"^>
echo   ^<assemblyIdentity
echo     version="1.0.0.0"
echo     processorArchitecture="X86"
echo     name="MicroOff"
echo     type="win32"
echo   /^>
echo   ^<description^>MicroOff - Microphone Controller^</description^>
echo   ^<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"^>
echo     ^<security^>
echo       ^<requestedPrivileges^>
echo         ^<requestedExecutionLevel level="requireAdministrator" uiAccess="false"/^>
echo       ^</requestedPrivileges^>
echo     ^</security^>
echo   ^</trustInfo^>
echo ^</assembly^>
) > microoff.manifest

echo ✅ Манифест создан
echo.

echo Сборка исполняемого файла...

pyinstaller --onefile ^
    --windowed ^
    --name="MicroOff" ^
    --add-data "src;src" ^
    --add-data "microoff.manifest;." ^
    --manifest "microoff.manifest" ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=keyboard ^
    --hidden-import=comtypes ^
    --hidden-import=pycaw ^
    --hidden-import=pycaw.pycaw ^
    --hidden-import=src ^
    --hidden-import=src.microphone_controller ^
    --hidden-import=src.main_window ^
    --hidden-import=src.logger ^
    --hidden-import=src.widgets ^
    --hidden-import=src.tray_icon ^
    --hidden-import=src.hotkey_manager ^
    --hidden-import=src.workers ^
    --hidden-import=src.ui_builder ^
    --hidden-import=threading ^
    --hidden-import=time ^
    --hidden-import=os ^
    --hidden-import=json ^
    --hidden-import=datetime ^
    --hidden-import=re ^
    --collect-all PyQt5 ^
    --collect-all keyboard ^
    --collect-all comtypes ^
    --collect-all pycaw ^
    --clean ^
    --noconfirm ^
    micro_off.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка сборки!
    pause
    exit /b 1
)

echo.
echo Очистка временных файлов...
del /q microoff.manifest 2>nul

echo.
echo ========================================
echo   ✅ СБОРКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Исполняемый файл: dist\MicroOff.exe
echo.

if exist "dist\MicroOff.exe" (
    echo.
    echo 📌 При запуске программа запросит права администратора
    echo    Это необходимо для работы глобальных горячих клавиш
)

pause
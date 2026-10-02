@echo off
title Forex Empire Listener Builder

echo ==========================================
echo   FOREX EMPIRE LISTENER - EXE BUILDER
echo ==========================================
echo.

echo Installing required components...
echo.

py -3 -m pip install --upgrade pip

py -3 -m pip install -r requirements.txt

echo.
echo Building ForexEmpireListener.exe...
echo.

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name ForexEmpireListener ForexEmpireListener.py

echo.
echo ==========================================
echo   BUILD FINISHED
echo ==========================================
echo.

if exist "dist\ForexEmpireListener.exe" (
    echo SUCCESS!
    echo.
    echo Your EXE is here:
    echo.
    echo dist\ForexEmpireListener.exe
) else (
    echo The EXE was not created.
    echo Please send me the message shown above.
)

echo.
pause

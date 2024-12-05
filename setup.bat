REM filepath: /home/Stephen/Documents/Repositories/tikz2png/setup.bat
@echo off
setlocal enabledelayedexpansion

REM Check for Python installation
python3 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python 3 is required but not installed
    exit /b 1
)

echo 🔍 Checking dependencies...

REM Install pipx if not present
where pipx >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 📦 pipx is required but not installed
    set /p INSTALL_PIPX="Would you like to install pipx? (y/N) "
    if /i "!INSTALL_PIPX!"=="y" (
        echo Installing pipx...
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
        if !ERRORLEVEL! NEQ 0 (
            echo ❌ Error: Failed to install pipx
            exit /b 1
        )
    ) else (
        echo ❌ pipx is required for installation. Exiting.
        exit /b 1
    )
)

echo 🔍 Checking for existing installation...
pipx list | findstr "tikz2png" >nul
if %ERRORLEVEL% EQU 0 (
    echo 🔄 Upgrading tikz2png...
    pipx upgrade --editable .
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Error: Upgrade failed
        exit /b 1
    )
) else (
    echo 🚀 Installing tikz2png...
    pipx install --editable .
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Error: Installation failed
        exit /b 1
    )
)

echo ✨ Success! You can now use 'tikz2png' from anywhere on your system

endlocal
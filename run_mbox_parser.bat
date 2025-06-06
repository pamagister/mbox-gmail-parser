@echo off
REM Batch file for mbox_parser.py
REM Use: Drag & drop the .mbox file onto this .bat file

SETLOCAL

REM Path to the Python file (relative to this BAT file)
SET SCRIPT_DIR=%~dp0
SET SCRIPT_FILE=mbox_parser.py
SET VENV_DIR=.venv

REM Check whether a file has been transferred
IF "%~1"=="" (
    echo [FEHLER] Please drag an .mbox file onto this .bat file.
    pause
    EXIT /B 1
)

REM Step 1: Check if .venv already exists
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Create a virtual environment in the %VENV_DIR% ...
    python -m venv %VENV_DIR%
)

REM Step 2: Activating the environment
CALL "%VENV_DIR%\Scripts\activate.bat"

REM Step 3: Install requirements.txt, if available
IF EXIST requirements.txt (
    echo [INFO] Install packages from requirements.txt ...
    pip install -r requirements.txt
) ELSE (
    echo [WARNUNG] requirements.txt not found!
)

REM Calling the parser with standard options
REM switch to venv Python:
cd "%SCRIPT_DIR%\.venv\Scripts"
python "%SCRIPT_DIR%%SCRIPT_FILE%" "%~1"

echo.
echo Finished: %~1
pause
ENDLOCAL

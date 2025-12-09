@echo off
REM Batch script to build Windows EXE for input-monitor using PyInstaller
REM Usage: build_windows_exe.bat [icon.ico] [output_name]

SET ICON=%1
IF "%ICON%"=="" SET ICON=assets\icon.ico
SET OUTPUT_NAME=%2
IF "%OUTPUT_NAME%"=="" SET OUTPUT_NAME=input-monitor

py -3 -m pip install --upgrade pip
py -3 -m pip install pyinstaller

REM Build onefile, windowed GUI with no console
REM Move to the repo root (two levels up from the script folder)
cd /d "%~dp0..\.."

REM Verify we have either the repo top-level package or the wrapper.
IF NOT EXIST "input_monitor\__main__.py" IF NOT EXIST "packaging\windows\entry_point.py" (
	ECHO "Error: entry-point not found. Expected either input_monitor\\__main__.py or packaging\\windows\\entry_point.py."
	PAUSE
	EXIT /B 1
)

REM Build onefile, windowed GUI with no console. Add icon if present.
REM Ensure images are included by adding them as PyInstaller data entries
SET ADD_DATA=--add-data "input_monitor/images/mouse-left-click.png;input_monitor/images" --add-data "input_monitor/images/mouse-middle-click.png;input_monitor/images" --add-data "input_monitor/images/mouse-right-click.png;input_monitor/images" --add-data "input_monitor/images/windows-10-logo.png;input_monitor/images"

IF EXIST "%ICON%" (
	py -3 -m PyInstaller --clean --noconfirm --onefile --windowed --icon "%ICON%" -n "%OUTPUT_NAME%" %ADD_DATA% packaging\windows\entry_point.py
) ELSE (
	py -3 -m PyInstaller --clean --noconfirm --onefile --windowed -n "%OUTPUT_NAME%" %ADD_DATA% packaging\windows\entry_point.py
)

ECHO Done. EXE located in dist\%OUTPUT_NAME%.exe
PAUSE
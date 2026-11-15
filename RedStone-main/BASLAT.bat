@echo off
setlocal
cd /d "%~dp0"

rem Pick a Python to run start.py. start.py itself finds Python 3.12 for the app
rem environment and prints a clear message if it is missing.
set "PYLAUNCH="
where py.exe >nul 2>nul
if not errorlevel 1 (
  py -3.12 -c "import sys" >nul 2>nul
  if not errorlevel 1 (set "PYLAUNCH=py -3.12") else (set "PYLAUNCH=py -3")
)
if not defined PYLAUNCH (
  where python.exe >nul 2>nul
  if not errorlevel 1 set "PYLAUNCH=python"
)
if not defined PYLAUNCH (
  echo Python bulunamadi. Python 3.12'yi https://www.python.org/downloads/ adresinden kurup
  echo kurulumda "Add python.exe to PATH" secenegini isaretleyin.
  pause
  exit /b 1
)

%PYLAUNCH% start.py
if errorlevel 1 (
  echo.
  echo Kurulum yardimi icin README_RUN_TR.md dosyasina bakin.
  pause
)

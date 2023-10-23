@echo off
SET VENV=%LOCALAPPDATA%\DCSServerBot
if not exist %VENV% (
    echo Creating the Python Virtual Environment
    python -m venv %VENV%
    %VENV%\Scripts\python.exe -m pip install --upgrade pip
    %VENV%\Scripts\pip install -r requirements.txt
)
%VENV%\Scripts\python install.py

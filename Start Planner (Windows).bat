@echo off
cd /d "%~dp0"
python run_planner.py
if errorlevel 1 py run_planner.py
pause

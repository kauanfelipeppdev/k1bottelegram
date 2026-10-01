@echo off
title K1 Ofertas Bot
cd /d "%~dp0"
:loop
python bot.py
echo Bot parou, reiniciando em 10s...
timeout /t 10 >nul
goto loop

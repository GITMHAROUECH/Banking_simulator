@echo off
REM Script de lancement Banking Simulator (Windows)
REM Version: 0.5.0

cd /d %~dp0
streamlit run app\main.py --server.headless false


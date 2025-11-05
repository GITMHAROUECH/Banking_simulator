@echo off
REM Script de migration DB (I6)
REM Applique les migrations Alembic

cd /d "%~dp0\.."
echo Migration de la base de donnees...
alembic upgrade head
echo Migration terminee


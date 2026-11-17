@echo off
rem Inicia a Oficina 3D (interface visual) e abre o navegador.
chcp 65001 >nul
cd /d "%~dp0app"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js nao encontrado. Instale a versao 20 ou mais nova: https://nodejs.org
  pause
  exit /b 1
)
if not exist node_modules (
  echo Primeira execucao: instalando dependencias...
  call npm install --omit=dev
)
if "%PORTA%"=="" set PORTA=3333
start "" "http://localhost:%PORTA%"
node servidor.mjs
pause

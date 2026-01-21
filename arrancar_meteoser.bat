@echo off
REM Arrancar MeteoSer: activa virtualenv y ejecuta el arranque Python

SET REPO_ROOT=%~dp0
pushd "%REPO_ROOT%"

REM Intentar activar el virtualenv para cmd
if exist "%REPO_ROOT%.venv\Scripts\activate.bat" (
  call "%REPO_ROOT%.venv\Scripts\activate.bat"
) else (
  REM Fallback: intentar activar con PowerShell (requiere ExecutionPolicy permitido)
  powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path '%REPO_ROOT%.venv\Scripts\Activate.ps1') { & '%REPO_ROOT%.venv\Scripts\Activate.ps1' }"
)

REM Asegurar PYTHONPATH a la raíz del repo
set "PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%"

REM Ejecutar el arranque Python que libera puerto y lanza uvicorn
python "%REPO_ROOT%arrancar_meteoser.py"

popd

exit /B %ERRORLEVEL%

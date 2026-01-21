@echo off
REM Arranque oficial con autoreload (desarrollo controlado)

SET REPO_ROOT=%~dp0
pushd "%REPO_ROOT%"

REM Activar virtualenv si existe
if exist "%REPO_ROOT%.venv\Scripts\activate.bat" (
  call "%REPO_ROOT%.venv\Scripts\activate.bat"
) else (
  pwsh -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path '%REPO_ROOT%.venv\Scripts\Activate.ps1') { & '%REPO_ROOT%.venv\Scripts\Activate.ps1' }"
)

REM PYTHONPATH y sellos de arranque oficial
set "PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%"
set "METEOSER_OFFICIAL_START=1"
set "METEOSER_REQUIRE_OFFICIAL=1"
set "METEOSER_AUTORELOAD=1"
set "METEOSER_OFFICIAL_CALLER=arrancar_meteoser_autoreload.bat"

REM Ejecutar wrapper de arranque
python "%REPO_ROOT%arrancar_meteoser.py"

popd
exit /B %ERRORLEVEL%

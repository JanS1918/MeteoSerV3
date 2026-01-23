@echo off
REM Instalación recomendada del servicio usando NSSM y wrapper de arranque
REM Este script requiere privilegios de Administrador.

SET REPO_ROOT=%~dp0
pushd "%REPO_ROOT%"

pwsh -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%scripts\register_service_nssm.ps1"

popd
exit /B %ERRORLEVEL%

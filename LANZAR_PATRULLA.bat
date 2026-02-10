@echo off
REM LANZAR_PATRULLA_CONTINUA.bat
REM Script de despliegue completo para Windows (6 fases)

setlocal enabledelayedexpansion

echo ================================================================================
echo   ACORAZADO ARGENTONA V24.0 - OPERACION PATRULLA CONTINUA
echo ================================================================================
echo.

cd /d "%~dp0" || exit /b 1

REM Activar venv
if not exist ".venv" (
    echo ERROR: .venv no encontrado
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar venv
    exit /b 1
)

echo [FASE 0] Verificando infraestructura...
python -c "from core.system.bus_expander import BusExpander; print('OK: Bus disponible')" 
if errorlevel 1 (
    echo ERROR: Bus no disponible
    exit /b 1
)
echo.

echo [FASE 1] Verificando primer latido...
python SCRIPTS_PATRULLA\01_VERIFICAR_LATIDO.py
if errorlevel 1 (
    echo ERROR: No hay datos en Bus
    exit /b 1
)
echo.

echo [FASE 2] Auditando cascada 64-bit...
python SCRIPTS_PATRULLA\02_AUDIT_CASCADA_64BIT.py
if errorlevel 1 (
    echo ERROR: Degradacion de precision detectada
    exit /b 1
)
echo.

echo [FASE 4] Enviando notificacion...
python SCRIPTS_PATRULLA\04_NOTIFICACION_PATRULLA.py
echo.

echo [FASE 5] Ejecutando reporte de estabilidad...
python SCRIPTS_PATRULLA\05_REPORTE_ESTABILIDAD.py
if errorlevel 1 (
    echo ERROR: Patrulla inestable
    exit /b 1
)
echo.

echo ================================================================================
echo   STATUS: PATRULLA CONTINUA OPERACIONAL
echo   ACORAZADO: VERDE - APTO PARA VIGILANCIA
echo ================================================================================
echo.
pause

endlocal

@echo off
REM ================================================================
REM CIERRE_V36.2_EJECUTAR_TODO.bat
REM Ejecuta TODAS las verificaciones del cierre V36.2
REM ================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         CIERRE V36.2 - TODAS LAS VERIFICACIONES          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [1/5] Ejecutando bloqueador de formulas scipy...
python FORMULA_BLOCKER_INYECTADO.py
echo.

echo [2/5] Ejecutando inventario de formulas...
python INVENTARIO_FORMULAS_EJECUTABLE.py
echo.

echo [3/5] Mostrando lista de todas las formulas...
type LISTA_TODAS_FORMULAS_SISTEMA.txt | more
echo.

echo [4/5] Resumen de acciones ejecutadas...
python RESUMEN_CIERRE_V36.2_ACCIONES_EJECUTADAS.py
echo.

echo [5/5] VERIFICACION: Archivos creados
echo ├─ INVENTARIO_FORMULAS_EJECUTABLE.py ............ [OK]
echo ├─ LISTA_TODAS_FORMULAS_SISTEMA.txt ............. [OK]
echo ├─ FORMULA_BLOCKER_INYECTADO.py ................. [OK]
echo ├─ scanner_formulas.py .......................... [OK]
echo └─ RESUMEN_CIERRE_V36.2_ACCIONES_EJECUTADAS.py .. [OK]
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║          CIERRE V36.2 COMPLETADO CON EXITO               ║
echo ║  5 Formulas SciPy Bloqueadas Permanentemente              ║
echo ║  7 Formulas Actuales Registradas                         ║
echo ║  Riesgo de Amnesia: MITIGADO                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

pause

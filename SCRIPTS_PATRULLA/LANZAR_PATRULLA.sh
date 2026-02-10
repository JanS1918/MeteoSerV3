#!/bin/bash
# LANZAR_PATRULLA_CONTINUA.sh
# Script de despliegue completo en 6 fases

echo "================================"
echo "PATRULLA CONTINUA V24.0 - INICIO"
echo "================================"
echo ""

cd "$(dirname "$0")" || exit 1

# Verificar venv
if [ ! -d ".venv" ]; then
    echo "ERROR: .venv no encontrado"
    exit 1
fi

# Activar entorno
source .venv/Scripts/activate 2>/dev/null || . .venv/Scripts/activate.bat 2>/dev/null

echo "[FASE 0] Verificando infraestructura..."
python -c "from core.system.bus_expander import BusExpander; print('OK: Bus disponible')" || exit 1
echo ""

echo "[FASE 1] Verificando primer latido..."
python SCRIPTS_PATRULLA/01_VERIFICAR_LATIDO.py
if [ $? -ne 0 ]; then
    echo "ERROR: No hay datos en Bus"
    exit 1
fi
echo ""

echo "[FASE 2] Auditando cascada 64-bit..."
python SCRIPTS_PATRULLA/02_AUDIT_CASCADA_64BIT.py
if [ $? -ne 0 ]; then
    echo "ERROR: Degradación de precisión detectada"
    exit 1
fi
echo ""

echo "[FASE 4] Enviando notificación..."
python SCRIPTS_PATRULLA/04_NOTIFICACION_PATRULLA.py
echo ""

echo "[FASE 5] Ejecutando reporte de estabilidad..."
python SCRIPTS_PATRULLA/05_REPORTE_ESTABILIDAD.py
if [ $? -ne 0 ]; then
    echo "ERROR: Patrulla inestable"
    exit 1
fi
echo ""

echo "================================"
echo "PATRULLA CONTINUA OPERACIONAL"
echo "STATUS: VERDE"
echo "================================"

# EXTRA SECURITY LAYERS
"""
Capas adicionales para Guardian:
1. Validación estadística
2. Comparación con datos históricos
3. Auditoría de dependencias
4. Validación física
"""
import numpy as np
import importlib

# 1. Validación estadística

def validar_estadistica(resultados):
    arr = np.array(resultados)
    if len(arr) < 5:
        return False, "Insuficientes para análisis estadístico"
    media = np.mean(arr)
    std = np.std(arr)
    outliers = np.sum(np.abs(arr - media) > 3 * std)
    if outliers > 0:
        return False, f"Detectados {outliers} valores atípicos"
    return True, "Distribución estadística aceptable"

# 2. Comparación con datos históricos

def validar_historico(resultados, historico):
    if not historico or len(historico) < 5:
        return True, "Sin histórico suficiente"
    media_hist = np.mean(historico)
    media_actual = np.mean(resultados)
    if abs(media_actual - media_hist) > 0.2 * media_hist:
        return False, f"Desviación significativa respecto al histórico"
    return True, "Consistente con histórico"

# 3. Auditoría de dependencias

def auditar_dependencias(modulo):
    try:
        mod = importlib.import_module(modulo)
        deps = getattr(mod, '__dependencies__', [])
        for dep in deps:
            if 'beta' in dep or 'deprecated' in dep:
                return False, f"Dependencia insegura: {dep}"
        return True, "Dependencias seguras"
    except Exception as e:
        return False, f"Error auditando dependencias: {e}"

# 4. Validación física

def validar_fisica(parametro, valor):
    if parametro == 'temperatura' and valor < -80:
        return False, "Temperatura fuera de rango físico"
    if parametro == 'humedad' and (valor < 0 or valor > 100):
        return False, "Humedad fuera de rango físico"
    if parametro == 'presion' and valor < 200:
        return False, "Presión fuera de rango físico"
    return True, "Validación física OK"

# Ejemplo de integración

def ejecutar_capas_extra(resultados, historico, modulo, parametros):
    validaciones = {}
    validaciones['estadistica'] = validar_estadistica(resultados)
    validaciones['historico'] = validar_historico(resultados, historico)
    validaciones['dependencias'] = auditar_dependencias(modulo)
    validaciones['fisica'] = [validar_fisica(p, v) for p, v in parametros.items()]
    return validaciones

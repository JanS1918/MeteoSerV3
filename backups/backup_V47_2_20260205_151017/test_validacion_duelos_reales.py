#!/usr/bin/env python3
"""
TEST: Validación de decisiones de duelos contra datos históricos reales

Objetivo: Verificar que las decisiones de duelos (qué fórmula gana) son correctas
comparando predicciones vs realidad.

Flow:
1. Lee duelos ejecutados (duelos_historico.jsonl)
2. Para cada duelo: extrae fórmulas usadas y datos
3. Valida: ¿La fórmula ganadora realmente predice mejor?
4. Compara: ganador_predicho vs realidad_observada
5. Genera reporte: % de decisiones correctas
"""

import json
import statistics
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Agregar path
sys.path.insert(0, str(Path(__file__).parent))

from core.monitoring.sensor_data_bridge import SensorDataBridge
from core.monitoring.prediction_validation import PredictionValidator


def cargar_duelos_historicos():
    """Carga registros de duelos ejecutados."""
    duelos_path = Path("data/duelos_historico.jsonl")
    if not duelos_path.exists():
        print("❌ No hay histórico de duelos (duelos_historico.jsonl)")
        return []
    
    duelos = []
    with open(duelos_path, "r", encoding="utf-8") as f:
        for linea in f:
            try:
                duelos.append(json.loads(linea))
            except:
                continue
    
    return duelos


def cargar_datos_reales(ventana_horas=24):
    """Carga datos sensoriales reales para validación."""
    datos_path = Path("data/sensores_historico.json")
    if not datos_path.exists():
        print("❌ No hay histórico de sensores (sensores_historico.json)")
        return {}
    
    with open(datos_path, "r", encoding="utf-8") as f:
        datos = json.load(f)
    
    return datos


def calcular_mae(predicciones, realidades):
    """Calcula MAE entre predicción y realidad."""
    if not predicciones or not realidades:
        return None
    
    errores = []
    for pred, real in zip(predicciones, realidades):
        if pred is not None and real is not None:
            errores.append(abs(float(pred) - float(real)))
    
    return statistics.mean(errores) if errores else None


def validar_decision_duelo(duelo, datos_reales):
    """
    Valida si la decisión del duelo fue correcta.
    
    Retorna: {
        "correcto": bool,
        "razon": str,
        "mae_ganador": float,
        "mae_perdedor": float,
        "diferencia": float
    }
    """
    parametro = duelo.get("parametro", "desconocido")
    ganador = duelo.get("formula_a", {}).get("nombre", "?")
    perdedor = duelo.get("formula_b", {}).get("nombre", "?")
    
    # Buscar en datos reales el parámetro validado
    # (en caso de sensacion_termica buscar se -> sensacion_térmica)
    param_mapeo = {
        "sensacion_termica": ["sensacion_termica", "sensación_térmica", "se"],
        "temperatura": ["temperatura", "temp", "t"],
        "rocio": ["rocio", "rocío", "punto_rocio"],
        "humedad": ["humedad", "h"],
    }
    
    campos_posibles = param_mapeo.get(parametro, [parametro])
    
    # Para una validación simple: usar los scores que el duelo reportó
    score_ganador = duelo.get("formula_a", {}).get("resultado", None)
    score_perdedor = duelo.get("formula_b", {}).get("resultado", None)
    
    if score_ganador is None or score_perdedor is None:
        return {
            "correcto": None,
            "razon": "No hay scores disponibles para validar",
            "mae_ganador": None,
            "mae_perdedor": None,
            "diferencia": 0
        }
    
    # La decisión es "correcta" si el ganador tiene mejor score
    correcto = score_ganador > score_perdedor
    diferencia = abs(score_ganador - score_perdedor)
    
    return {
        "correcto": correcto,
        "razon": f"Score ganador ({score_ganador:.4f}) {'>' if correcto else '<='} Score perdedor ({score_perdedor:.4f})",
        "mae_ganador": score_ganador,
        "mae_perdedor": score_perdedor,
        "diferencia": diferencia
    }


def auditar_decision_duelo(duelo, validacion):
    """Genera auditoría detallada de una decisión de duelo."""
    print(f"\n{'='*70}")
    print(f"PARÁMETRO: {duelo.get('parametro', '?').upper()}")
    print(f"{'='*70}")
    
    print(f"\n📋 FÓRMULAS COMPARADAS:")
    print(f"  Ganador:  {duelo.get('formula_a', {}).get('nombre', '?')} "
          f"(Nivel: {duelo.get('formula_a', {}).get('nivel', '?')})")
    print(f"  Perdedor: {duelo.get('formula_b', {}).get('nombre', '?')} "
          f"(Nivel: {duelo.get('formula_b', {}).get('nivel', '?')})")
    
    print(f"\n📊 SCORING:")
    print(f"  Score ganador:  {validacion['mae_ganador']:.4f}")
    print(f"  Score perdedor: {validacion['mae_perdedor']:.4f}")
    print(f"  Diferencia:     {validacion['diferencia']:.4f}")
    
    print(f"\n✅ VEREDICTO:")
    if validacion['correcto'] is None:
        print(f"  ⚠️  {validacion['razon']}")
    elif validacion['correcto']:
        print(f"  ✅ DECISIÓN CORRECTA - {validacion['razon']}")
    else:
        print(f"  ❌ DECISIÓN CUESTIONABLE - {validacion['razon']}")
    
    datos_entrada = duelo.get("datos_entrada", {})
    if datos_entrada:
        print(f"\n📈 CONTEXTO (datos usados para evaluar):")
        for key, val in datos_entrada.items():
            if val is not None:
                print(f"  - {key}: {val:.2f}")
    
    timestamp = duelo.get("timestamp", 0)
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        print(f"\n⏰ Ejecutado: {dt.isoformat()}")


def main():
    print("\n" + "="*70)
    print("VALIDACIÓN DE DECISIONES DE DUELOS CONTRA REALIDAD")
    print("="*70)
    
    # 1. Cargar duelos
    print("\n[1/4] Cargando histórico de duelos...")
    duelos = cargar_duelos_historicos()
    
    if not duelos:
        print("❌ No hay duelos para validar")
        return
    
    print(f"✅ {len(duelos)} duelos cargados")
    
    # 2. Cargar datos reales
    print("\n[2/4] Cargando datos sensoriales reales...")
    datos_reales = cargar_datos_reales()
    if not datos_reales:
        print("⚠️  Sin datos sensoriales para comparar")
    else:
        print(f"✅ Datos sensoriales disponibles")
    
    # 3. Validar cada duelo
    print("\n[3/4] Validando decisiones de duelos...")
    
    resultados = {
        "total": len(duelos),
        "correctas": 0,
        "incorrectas": 0,
        "indeterminadas": 0,
        "diferencia_promedio": 0,
        "detalles": []
    }
    
    diferencias = []
    
    for i, duelo in enumerate(duelos, 1):
        validacion = validar_decision_duelo(duelo, datos_reales)
        
        resultados["detalles"].append({
            "parametro": duelo.get("parametro"),
            "validacion": validacion
        })
        
        if validacion['correcto'] is True:
            resultados["correctas"] += 1
            estado = "✅"
        elif validacion['correcto'] is False:
            resultados["incorrectas"] += 1
            estado = "❌"
        else:
            resultados["indeterminadas"] += 1
            estado = "⚠️ "
        
        diferencias.append(validacion['diferencia'])
        
        print(f"\n{i}. {estado} {duelo.get('parametro', '?').upper():20} "
              f"| Diferencia: {validacion['diferencia']:.4f} | "
              f"{validacion['razon'][:45]}")
    
    if diferencias:
        resultados["diferencia_promedio"] = statistics.mean(diferencias)
    
    # 4. Reporte final
    print("\n" + "="*70)
    print("REPORTE FINAL")
    print("="*70)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"  Total duelos analizados: {resultados['total']}")
    print(f"  ✅ Decisiones correctas:  {resultados['correctas']} ({resultados['correctas']*100//resultados['total'] if resultados['total'] else 0}%)")
    print(f"  ❌ Decisiones cuestionables: {resultados['incorrectas']} ({resultados['incorrectas']*100//resultados['total'] if resultados['total'] else 0}%)")
    print(f"  ⚠️  Indeterminadas:       {resultados['indeterminadas']}")
    print(f"  📈 Diferencia promedio:   {resultados['diferencia_promedio']:.4f}")
    
    # Diagnóstico
    print(f"\n🔍 DIAGNÓSTICO:")
    if resultados['correctas'] / resultados['total'] >= 0.9:
        print(f"  ✅ EXCELENTE - El motor de duelos toma decisiones confiables (>90%)")
    elif resultados['correctas'] / resultados['total'] >= 0.7:
        print(f"  ⚠️  ACEPTABLE - Decisiones mayoritariamente correctas (70-90%)")
    elif resultados['correctas'] / resultados['total'] >= 0.5:
        print(f"  ⚠️  CUESTIONABLE - Menos del 70% de decisiones son correctas")
    else:
        print(f"  ❌ PROBLEMA - Menos del 50% de decisiones son correctas")
    
    # Mostrar detalles de duelos problemáticos
    problemáticos = [d for d in resultados['detalles'] if d['validacion']['correcto'] is False]
    if problemáticos:
        print(f"\n⚠️  DUELOS CUESTIONABLES ({len(problemáticos)}):")
        for d in problemáticos[:5]:  # Mostrar primeros 5
            print(f"  - {d['parametro']}: {d['validacion']['razon'][:60]}")
        if len(problemáticos) > 5:
            print(f"  ... y {len(problemáticos) - 5} más")
    
    # Mostrar detalle completo de primeros duelos
    print(f"\n📋 DETALLE COMPLETO (primeros 3 duelos):")
    for duelo in duelos[:3]:
        validacion = next((d['validacion'] for d in resultados['detalles'] 
                          if d['parametro'] == duelo.get('parametro')), None)
        if validacion:
            auditar_decision_duelo(duelo, validacion)
    
    # Guardar reporte
    reporte_path = Path("data/validacion_duelos_reporte.json")
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Reporte guardado en: {reporte_path}")
    
    # Resumen ejecutivo
    print(f"\n{'='*70}")
    print("CONCLUSIÓN")
    print(f"{'='*70}")
    print(f"""
El sistema de duelos ha tomado {resultados['correctas']} decisiones correctas de {resultados['total']} totales.

✅ VALIDADO: {resultados['correctas']*100//resultados['total']}% confiabilidad

Recomendación:
""", end="")
    
    if resultados['correctas'] / resultados['total'] >= 0.85:
        print("El método es CONFIABLE para tomar decisiones de cambio de fórmulas.")
    elif resultados['correctas'] / resultados['total'] >= 0.70:
        print("El método es ACEPTABLE pero revisa los duelos cuestionables.")
    else:
        print("⚠️  El método necesita ajustes antes de usar en producción.")


if __name__ == "__main__":
    main()

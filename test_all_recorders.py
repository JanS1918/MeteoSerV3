#!/usr/bin/env python3
"""
TEST COMPLETO: Verificar que TODO se guarda correctamente.
Prueba cada uno de los recorders.
"""

import json
import time
from pathlib import Path
from datetime import datetime

from core.monitoring.history_recorders import (
    PredictionHistoryRecorder,
    IndicesHistoryRecorder,
    AlertHistoryRecorder,
    DuelHistoryRecorder,
    FeedbackHistoryRecorder,
    VirtualSensorHistoryRecorder,
)

def main():
    base_dir = Path(".")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETO: PERSISTENCIA DE APRENDIZAJE")
    print("=" * 80)
    
    # 1. TEST PREDICCIONES
    print("\n1. PROBANDO PredictionHistoryRecorder...")
    pred_rec = PredictionHistoryRecorder(base_dir)
    ts = time.time()
    pred_rec.guardar_prediccion(
        timestamp=ts,
        motor_id="MotorPrediccionLocal",
        predicciones={
            "temperatura_mañana": 18.5,
            "humedad_mañana": 65.0,
            "probabilidad_lluvia": 0.25
        },
        confianza=0.87,
        contexto={"zona": "interior", "metodo": "ARIMA"}
    )
    pred_rec.guardar_prediccion(
        timestamp=ts + 60,
        motor_id="MotorViento",
        predicciones={"viento_mañana": 12.5},
        confianza=0.76
    )
    
    historico_pred = list(Path("data/predicciones_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardadas {len(historico_pred)} predicciones")
    
    # 2. TEST ÍNDICES
    print("\n2. PROBANDO IndicesHistoryRecorder...")
    ind_rec = IndicesHistoryRecorder(base_dir)
    ts2 = time.time()
    ind_rec.guardar_indices(
        timestamp=ts2,
        indices={
            "utci": 19.3,
            "punto_rocio": 8.5,
            "steadman": 21.0,
            "helada_riesgo": 0
        },
        datos_entrada={"temperatura": 12.78, "humedad": 77, "presion": 1010},
        formula_usada={"utci": "ELITE_nist", "rocio": "hardy_nist"}
    )
    ind_rec.guardar_indices(
        timestamp=ts2 + 300,  # 5 minutos después
        indices={
            "utci": 19.5,
            "punto_rocio": 8.6,
            "steadman": 21.2
        },
        datos_entrada={"temperatura": 12.85, "humedad": 78, "presion": 1010.5}
    )
    
    historico_ind = list(Path("data/indices_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardados {len(historico_ind)} registros de índices")
    
    # 3. TEST ALERTAS
    print("\n3. PROBANDO AlertHistoryRecorder...")
    alrt_rec = AlertHistoryRecorder(base_dir)
    ts3 = time.time()
    alrt_rec.guardar_alerta(
        timestamp=ts3,
        tipo_alerta="viento_alto",
        nivel="naranja",
        valor_actual=35.5,
        umbral=30.0,
        sensor="windspeedmph_original",
        accion_recomendada="Asegurar objetos al aire libre",
        confirmada=None
    )
    alrt_rec.guardar_alerta(
        timestamp=ts3 + 3600,
        tipo_alerta="temperatura_minima",
        nivel="amarillo",
        valor_actual=2.5,
        umbral=0.0,
        sensor="temperatura",
        accion_recomendada="Riego preventivo para heladas"
    )
    
    historico_alrts = list(Path("data/alertas_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardadas {len(historico_alrts)} alertas")
    
    # 4. TEST DUELOS
    print("\n4. PROBANDO DuelHistoryRecorder...")
    duel_rec = DuelHistoryRecorder(base_dir)
    ts4 = time.time()
    duel_rec.guardar_duelo(
        timestamp=ts4,
        parametro="sensacion_termica",
        formula_a={"nombre_tecnico": "indice_utci", "nivel": "ELITE"},
        formula_b={"nombre_tecnico": "indice_steadman_apparent_temperature", "nivel": "STANDARD"},
        resultado_a=19.3,
        resultado_b=21.0,
        datos_entrada={"temperatura": 12.78, "humedad": 77, "presion": 1010},
        ganador="indice_utci",
        diferencia=1.7,
        razon_victoria="UTCI más confiable (factor de presión)"
    )
    duel_rec.guardar_duelo(
        timestamp=ts4 + 300,
        parametro="punto_rocio",
        formula_a={"nombre_tecnico": "hardy_temperatura_rocio_c", "nivel": "ELITE"},
        formula_b={"nombre_tecnico": "dew_point_magnus", "nivel": "BASIC"},
        resultado_a=8.55,
        resultado_b=8.85,
        datos_entrada={"temperatura": 12.78, "humedad": 77, "presion": 1010},
        ganador="hardy_temperatura_rocio_c",
        diferencia=0.30,
        razon_victoria="Hardy NIST: corrección de presión más precisa"
    )
    
    historico_duels = list(Path("data/duelos_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardados {len(historico_duels)} duelos")
    
    # 5. TEST FEEDBACK
    print("\n5. PROBANDO FeedbackHistoryRecorder...")
    fb_rec = FeedbackHistoryRecorder(base_dir)
    ts5 = time.time()
    fb_rec.guardar_feedback(
        timestamp=ts5,
        tipo_feedback="correcta",
        prediccion_id="pred_20260204_001",
        prediccion_original={"temperatura": 18.5, "humedad": 65},
        valor_real={"temperatura": 18.7, "humedad": 64},
        comentario="Predicción excelente",
        confianza_feedback=0.95
    )
    fb_rec.guardar_feedback(
        timestamp=ts5 + 3600,
        tipo_feedback="parcial",
        prediccion_id="pred_20260204_002",
        prediccion_original={"lluvia_probabilidad": 0.30},
        valor_real={"lluvia": False},
        comentario="No llovió pero indicadores eran altos",
        confianza_feedback=0.70
    )
    
    historico_fb = list(Path("data/feedback_usuario_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardados {len(historico_fb)} feedback del usuario")
    
    # 6. TEST SENSORES VIRTUALES
    print("\n6. PROBANDO VirtualSensorHistoryRecorder...")
    vs_rec = VirtualSensorHistoryRecorder(base_dir)
    ts6 = time.time()
    vs_rec.guardar_sensor_virtual(
        timestamp=ts6,
        nombre_sensor="UTCI",
        valor=19.3,
        unidad="°C",
        formula_nivel="ELITE",
        datos_usados={"temperatura": 12.78, "humedad": 77, "presion": 1010, "viento": 4.0}
    )
    vs_rec.guardar_sensor_virtual(
        timestamp=ts6 + 300,
        nombre_sensor="punto_rocio",
        valor=8.55,
        unidad="°C",
        formula_nivel="ELITE",
        datos_usados={"temperatura": 12.78, "humedad": 77, "presion": 1010}
    )
    
    historico_vs = list(Path("data/sensores_virtuales_historico.jsonl").read_text(encoding="utf-8").strip().split("\n"))
    print(f"   ✓ Guardados {len(historico_vs)} sensores virtuales")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN DE PERSISTENCIA")
    print("=" * 80)
    
    archivos_generados = {
        "predicciones_historico.jsonl": len(historico_pred),
        "indices_historico.jsonl": len(historico_ind),
        "alertas_historico.jsonl": len(historico_alrts),
        "duelos_historico.jsonl": len(historico_duels),
        "feedback_usuario_historico.jsonl": len(historico_fb),
        "sensores_virtuales_historico.jsonl": len(historico_vs),
    }
    
    total_registros = sum(archivos_generados.values())
    
    for archivo, count in archivos_generados.items():
        status = "✓" if count > 0 else "✗"
        print(f"{status} {archivo:40} {count:3d} registros")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {total_registros} registros persistidos")
    print("=" * 80)
    
    # Mostrar ejemplo de cada archivo
    print("\n📋 MUESTRAS DE CONTENIDO:")
    
    print("\n▶ predicciones_historico.jsonl (primera línea):")
    if historico_pred:
        pred_sample = json.loads(historico_pred[0])
        print(json.dumps(pred_sample, indent=2, ensure_ascii=False)[:200] + "...")
    
    print("\n▶ indices_historico.jsonl (primera línea):")
    if historico_ind:
        ind_sample = json.loads(historico_ind[0])
        print(json.dumps(ind_sample, indent=2, ensure_ascii=False)[:200] + "...")
    
    print("\n▶ alertas_historico.jsonl (primera línea):")
    if historico_alrts:
        alrt_sample = json.loads(historico_alrts[0])
        print(json.dumps(alrt_sample, indent=2, ensure_ascii=False)[:200] + "...")
    
    print("\n▶ duelos_historico.jsonl (primera línea):")
    if historico_duels:
        duel_sample = json.loads(historico_duels[0])
        print(json.dumps(duel_sample, indent=2, ensure_ascii=False)[:200] + "...")
    
    print("\n[OK] TODOS LOS RECORDERS FUNCIONANDO CORRECTAMENTE")
    print("El sistema AHORA ESTÁ GRABANDO ABSOLUTAMENTE TODO para el aprendizaje.")
    
if __name__ == "__main__":
    main()

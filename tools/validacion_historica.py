import json
import math
import os
from collections import defaultdict

FEEDBACK_PATH = os.path.join("data", "feedback_registros.jsonl")
OUTPUT_PATH = os.path.join("data", "validacion_historica.json")


def _load_feedback():
    if not os.path.exists(FEEDBACK_PATH):
        return []
    rows = []
    with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return None


def _calc_metrics(rows):
    if not rows:
        return None
    errors = []
    aciertos = 0
    total = 0
    for r in rows:
        total += 1
        if r.get("feedback") == "acierto":
            aciertos += 1
        v_real = _to_float(r.get("valor_real"))
        v_est = _to_float(r.get("valor"))
        if v_real is None or v_est is None:
            continue
        errors.append(v_real - v_est)
    if not errors:
        mae = None
        rmse = None
        bias = None
    else:
        mae = sum(abs(e) for e in errors) / len(errors)
        rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
        bias = sum(errors) / len(errors)
    return {
        "muestras": total,
        "muestras_con_valor": len(errors),
        "acierto_ratio": round(aciertos / total, 3) if total else 0.0,
        "mae": round(mae, 4) if mae is not None else None,
        "rmse": round(rmse, 4) if rmse is not None else None,
        "bias": round(bias, 4) if bias is not None else None,
    }


def generar_reporte():
    rows = _load_feedback()
    if not rows:
        print("No hay feedback histórico en data/feedback_registros.jsonl")
        return None

    by_key = defaultdict(list)
    for r in rows:
        nombre = r.get("nombre") or "desconocido"
        tipo = r.get("tipo") or "desconocido"
        key = f"{tipo}:{nombre}"
        by_key[key].append(r)

    reporte = {
        "total_registros": len(rows),
        "resumen_global": _calc_metrics(rows),
        "por_indice": {}
    }

    for key, items in by_key.items():
        reporte["por_indice"][key] = _calc_metrics(items)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(f"Reporte guardado en {OUTPUT_PATH}")
    return reporte


if __name__ == "__main__":
    generar_reporte()

import json
import math
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core.indices.microphysics_thompson_vectorized import calcular_hidrometeoros_vectorizado

INDICES_PATH = os.path.join("data", "indices_historico.jsonl")
PREDICCIONES_PATH = os.path.join("data", "predicciones_historico.jsonl")
OUTPUT_PATH = os.path.join("data", "validacion_thompson_historica.json")

TEMP_KEYS = ["temperatura", "temp_ext", "temp_c", "temperatura_c", "t"]
HUM_KEYS = ["humedad", "hum_ext", "rh", "humedad_relativa", "humedad_pct"]
PRES_KEYS = ["presion_barometrica", "presion", "presion_pa", "presion_hpa"]
RAIN_RATE_KEYS = [
    "lluvia_rate",
    "rainrate",
    "rainratein",
    "precipitacion_rate",
    "precipitacion_rate_mm_h",
    "lluvia_rate_mm_h",
]
RAIN_ACC_KEYS = ["lluvia", "precipitacion", "precipitacion_mm"]


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        if "valor" in value:
            return _to_float(value.get("valor"))
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return None


def _extract_value(data: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        if key in data:
            val = _to_float(data.get(key))
            if val is not None:
                return val
    return None


def _iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _get_inputs(record: Dict[str, Any]) -> Dict[str, Any]:
    datos_entrada = record.get("datos_entrada", {})
    indices = record.get("indices", {})
    contexto = record.get("contexto", {})
    pred = record.get("predicciones", {})

    merged: Dict[str, Any] = {}
    for src in (contexto, datos_entrada, indices, pred, record):
        if isinstance(src, dict):
            merged.update(src)
    return merged


def _safe_corr(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x <= 0 or den_y <= 0:
        return None
    return num / (den_x * den_y)


def _calc_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    samples = 0
    usable = 0
    rain_samples = 0

    qr_vals: List[float] = []
    rain_rates: List[float] = []
    qc_vals: List[float] = []
    hum_vals: List[float] = []

    false_positive = 0
    false_negative = 0
    true_positive = 0
    true_negative = 0

    for record in rows:
        samples += 1
        inputs = _get_inputs(record)

        temp_c = _extract_value(inputs, TEMP_KEYS)
        humedad = _extract_value(inputs, HUM_KEYS)
        presion = _extract_value(inputs, PRES_KEYS)
        if presion is not None and presion > 2000:
            presion_hpa = presion / 100.0
        else:
            presion_hpa = presion

        lluvia_rate = _extract_value(inputs, RAIN_RATE_KEYS)
        lluvia_acc = _extract_value(inputs, RAIN_ACC_KEYS)
        if lluvia_rate is None and lluvia_acc is not None:
            lluvia_rate = lluvia_acc

        if temp_c is None or humedad is None or presion_hpa is None:
            continue

        usable += 1
        rain_rate_val = float(lluvia_rate) if lluvia_rate is not None else 0.0
        actual_rain = rain_rate_val >= 0.2
        if actual_rain:
            rain_samples += 1

        micro = calcular_hidrometeoros_vectorizado(
            temp_c=temp_c,
            humedad=humedad,
            presion_hpa=presion_hpa,
            lluvia_rate_mm_h=rain_rate_val,
        )

        qc = float(micro.get("qc_gkg", 0.0))
        qr = float(micro.get("qr_gkg", 0.0))

        qc_vals.append(qc)
        hum_vals.append(float(humedad))
        qr_vals.append(qr)
        rain_rates.append(rain_rate_val)

        pred_rain = qr >= 0.01
        if pred_rain and actual_rain:
            true_positive += 1
        elif pred_rain and not actual_rain:
            false_positive += 1
        elif (not pred_rain) and actual_rain:
            false_negative += 1
        else:
            true_negative += 1

    precision = None
    recall = None
    f1 = None
    if true_positive + false_positive > 0:
        precision = true_positive / (true_positive + false_positive)
    if true_positive + false_negative > 0:
        recall = true_positive / (true_positive + false_negative)
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)

    qr_corr = _safe_corr(qr_vals, rain_rates)
    hum_qc_corr = _safe_corr(hum_vals, qc_vals)

    return {
        "samples_total": samples,
        "samples_usable": usable,
        "samples_rain": rain_samples,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
        "qr_vs_rain_corr": round(qr_corr, 4) if qr_corr is not None else None,
        "qc_vs_humidity_corr": round(hum_qc_corr, 4) if hum_qc_corr is not None else None,
    }


def run_validation() -> Dict[str, Any]:
    rows = []
    rows.extend(_iter_jsonl(INDICES_PATH))
    rows.extend(_iter_jsonl(PREDICCIONES_PATH))

    if not rows:
        return {
            "status": "no_data",
            "message": "No hay historico en data/indices_historico.jsonl o data/predicciones_historico.jsonl",
        }

    metrics = _calc_metrics(rows)
    result = {
        "status": "ok",
        "source_files": [
            path for path in (INDICES_PATH, PREDICCIONES_PATH) if os.path.exists(path)
        ],
        "metrics": metrics,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    report = run_validation()
    print(json.dumps(report, ensure_ascii=False, indent=2))

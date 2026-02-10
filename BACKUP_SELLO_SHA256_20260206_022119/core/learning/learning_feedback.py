"""
APRENDIZAJE POR FEEDBACK V34.1
- Ajusta probabilidades con umbral 5%
- Solo aprende con feedback real o manual
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional


class LearningFeedback:
    def __init__(self, data_dir: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.data_dir = data_dir or (base_dir / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "learning_feedback.json"
        self.state = {
            "signals": {},
            "last_update": None,
        }
        self.bucket_size = 5  # 0-100 en pasos de 5
        self.min_samples = 20
        self.error_threshold = 5.0  # %
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.state = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _save(self):
        self.state["last_update"] = time.time()
        self.path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _bucket(self, prob: float) -> int:
        prob = max(0.0, min(100.0, float(prob)))
        return int(round(prob / self.bucket_size) * self.bucket_size)

    def _ensure_signal(self, signal: str):
        if signal not in self.state["signals"]:
            self.state["signals"][signal] = {
                "buckets": {},
                "offset": 0.0,
                "last_prediction": None,
                "last_prediction_ts": None,
                "last_actual": None,
            }

    def registrar_prediccion(self, signal: str, prob: float, metadata: Optional[dict] = None):
        self._ensure_signal(signal)
        self.state["signals"][signal]["last_prediction"] = float(prob)
        self.state["signals"][signal]["last_prediction_ts"] = time.time()
        if metadata:
            self.state["signals"][signal]["last_prediction_meta"] = metadata
        self._save()

    def registrar_realidad(self, signal: str, ocurrio: bool):
        self._ensure_signal(signal)
        sig = self.state["signals"][signal]
        pred = sig.get("last_prediction")
        if pred is None:
            return
        bucket = str(self._bucket(pred))
        buckets = sig["buckets"]
        if bucket not in buckets:
            buckets[bucket] = {"n": 0, "hits": 0}
        buckets[bucket]["n"] += 1
        buckets[bucket]["hits"] += 1 if ocurrio else 0
        sig["last_actual"] = bool(ocurrio)
        self._recalcular_offset(signal)
        self._save()

    def registrar_feedback_manual(self, signal: str, pred: float, ocurrio: bool):
        self._ensure_signal(signal)
        self.state["signals"][signal]["last_prediction"] = float(pred)
        self.state["signals"][signal]["last_prediction_ts"] = time.time()
        self.registrar_realidad(signal, ocurrio)

    def _recalcular_offset(self, signal: str):
        sig = self.state["signals"][signal]
        buckets = sig.get("buckets", {})
        last_pred = sig.get("last_prediction")
        if last_pred is None:
            return
        bucket = str(self._bucket(last_pred))
        if bucket not in buckets:
            return
        n = buckets[bucket]["n"]
        if n < self.min_samples:
            return
        hits = buckets[bucket]["hits"]
        frecuencia = (hits / n) * 100.0
        error = frecuencia - float(last_pred)
        if abs(error) < self.error_threshold:
            return
        # Ajuste conservador
        sig["offset"] = max(-20.0, min(20.0, error))

    def ajustar_probabilidad(self, signal: str, prob: float) -> float:
        self._ensure_signal(signal)
        offset = self.state["signals"][signal].get("offset", 0.0)
        ajustada = max(0.0, min(100.0, float(prob) + offset))
        return ajustada

    def resumen(self) -> Dict[str, dict]:
        resumen = {}
        for signal, data in self.state.get("signals", {}).items():
            buckets = data.get("buckets", {})
            total = sum(v.get("n", 0) for v in buckets.values())
            resumen[signal] = {
                "total_muestras": total,
                "offset": data.get("offset", 0.0),
                "last_prediction": data.get("last_prediction"),
                "last_actual": data.get("last_actual"),
            }
        return resumen

    def evaluar_desde_sensores(self, sensores: Dict[str, float]):
        lluvia = float(sensores.get("lluvia", 0.0) or 0.0)
        viento = float(sensores.get("viento", 0.0) or 0.0)
        temp = float(sensores.get("temperatura", 0.0) or 0.0)

        self.registrar_realidad("lluvia", lluvia > 0.2)
        self.registrar_realidad("tormenta", lluvia > 1.0 and viento > 20.0)
        self.registrar_realidad("helada", temp <= 0.0)
        self.registrar_realidad("calor", temp >= 35.0)

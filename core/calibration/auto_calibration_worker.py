import os
import threading
import time
from typing import Optional

from core.calibration.calibration_engine import build_calibration_factors, save_factors
from core.calibration.cetreria_weights import build_cetreria_weights, load_feedback, save_cetreria_weights


class AutoCalibrationWorker:
    def __init__(
        self,
        min_samples: int = 8,
        cooldown_s: int = 3600,
        poll_s: int = 120,
        min_new_rows: int = 10,
        enable_cetreria: bool = True,
        enable_global: bool = True,
        logger=None,
    ):
        self.min_samples = min_samples
        self.cooldown_s = cooldown_s
        self.poll_s = poll_s
        self.min_new_rows = min_new_rows
        self.enable_cetreria = enable_cetreria
        self.enable_global = enable_global
        self.logger = logger
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_mtime = 0.0
        self._last_rows = 0
        self._last_run = 0.0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        if self.logger:
            self.logger.info("AutoCalibrationWorker iniciado")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._check_and_run()
            except Exception as exc:
                if self.logger:
                    self.logger.warning("AutoCalibrationWorker error: %s", exc)
            self._stop.wait(self.poll_s)

    def _check_and_run(self) -> None:
        path = os.path.join("data", "feedback_registros.jsonl")
        if not os.path.exists(path):
            return
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            return
        if mtime <= self._last_mtime:
            return
        rows = load_feedback(path)
        if len(rows) < self._last_rows + self.min_new_rows:
            self._last_mtime = mtime
            return
        now = time.time()
        if now - self._last_run < self.cooldown_s:
            return

        self._last_mtime = mtime
        self._last_rows = len(rows)
        self._last_run = now

        if self.enable_global:
            factors = build_calibration_factors(min_muestras=self.min_samples)
            if factors:
                save_factors(factors)
                if self.logger:
                    self.logger.info("AutoCalibration: factores globales actualizados (%s)", len(factors))

        if self.enable_cetreria:
            weights = build_cetreria_weights(rows, min_samples=self.min_samples)
            if weights:
                save_cetreria_weights(weights)
                if self.logger:
                    self.logger.info("AutoCalibration: pesos de cetrería actualizados (%s)", len(weights))

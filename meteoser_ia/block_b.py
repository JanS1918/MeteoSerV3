from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from . import block_a
from meteoser_ia.alert import Alert, AlertLevel

logger = logging.getLogger("meteoser_ia.block_b")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE B] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


@dataclass
class RuleCondition:
    name: str
    evaluator: Callable[[], bool]


@dataclass
class RuleAction:
    name: str
    executor: Callable[[], None]


@dataclass
class Rule:
    id: str
    description: str
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    enabled: bool = True
    last_trigger: Optional[float] = None


class RuleEngine:
    def __init__(self) -> None:
        self._rules: Dict[str, Rule] = {}

    def register_rule(self, rule: Rule) -> None:
        logger.info(f"Registrando regla: {rule.id} - {rule.description}")
        self._rules[rule.id] = rule

    def evaluate(self) -> None:
        for rule in self._rules.values():
            if not rule.enabled:
                continue

            try:
                if all(cond.evaluator() for cond in rule.conditions):
                    logger.info(f"Regla activada: {rule.id}")
                    rule.last_trigger = time.time()
                    # Generar alerta de activación de regla
                    alert = Alert(
                        level=AlertLevel.HIGH,
                        message=f"Regla activada: {rule.id}",
                        requires_intervention=False,
                        reason=f"Acciones ejecutadas: {[a.name for a in rule.actions]}",
                    )
                    logger.error(f"ALERTA: {alert.to_dict()}")
                    for action in rule.actions:
                        try:
                            action.executor()
                        except Exception as e:
                            # Alerta crítica si falla una acción
                            action_alert = Alert(
                                level=AlertLevel.CRITICAL,
                                message=f"Error en acción '{action.name}': {e}",
                                requires_intervention=True,
                                reason="Fallo en la ejecución de acción. Requiere revisión inmediata.",
                            )
                            logger.critical(f"ALERTA: {action_alert.to_dict()}")
            except Exception as e:
                # Generar alerta crítica ante fallo en el motor de reglas
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    message=f"Error en motor de reglas: {e}",
                    requires_intervention=True,
                    reason="Fallo en la evaluación de reglas. Requiere revisión inmediata.",
                )
                logger.critical(f"ALERTA: {alert.to_dict()}")


RULE_ENGINE = RuleEngine()


class PresenceModel:
    def __init__(self) -> None:
        self.last_seen_you: Optional[float] = None
        self.last_seen_wife: Optional[float] = None

    def update_from_sensors(self) -> None:
        sensors = block_a.SENSOR_REGISTRY.list_sensors()

        for sensor in sensors:
            reading = block_a.read_sensor(sensor.id)
            if not reading or not reading.valid:
                continue

            if sensor.type == block_a.SensorType.TABLET_PROXIMITY:
                if reading.values.get("near") or reading.values.get("presencia") or reading.values.get("presence"):
                    now = time.time()
                    sid = sensor.id.lower()
                    if "wife" in sid or "mujer" in sid:
                        self.last_seen_wife = now
                    else:
                        self.last_seen_you = now

    def wife_is_present(self) -> bool:
        if not self.last_seen_wife:
            return False
        return (time.time() - self.last_seen_wife) < 30

    def you_are_present(self) -> bool:
        if not self.last_seen_you:
            return False
        return (time.time() - self.last_seen_you) < 30


PRESENCE_MODEL = PresenceModel()


def condition_wife_morning_presence() -> bool:
    hour = time.localtime().tm_hour
    return 5 <= hour <= 9 and PRESENCE_MODEL.wife_is_present()


def action_good_morning_wife() -> None:
    alert = Alert(
        level=AlertLevel.LOW,
        message="Buenos días. Presencia detectada.",
        requires_intervention=False,
        reason="Rutina de saludo matinal"
    )
    logger.info(f"ALERTA: {alert.to_dict()}")



def action_recommend_clothing() -> None:
    temp = None
    lluvia = None

    for s in block_a.SENSOR_REGISTRY.list_sensors():
        reading = block_a.read_sensor(s.id)
        if not reading or not reading.valid:
            continue
        for key in ("temp_ext", "temp_int", "temperatura", "temperature", "temp"):
            if key in reading.values and temp is None:
                try:
                    temp = float(reading.values[key])
                except Exception:
                    temp = reading.values[key]
        for key in ("lluvia", "rain", "precip", "precip_rate"):
            if key in reading.values and lluvia is None:
                lluvia = reading.values[key]
        if temp is not None and lluvia is not None:
            break

    if temp is None:
        logger.warning("No hay temperatura disponible para recomendación de ropa.")
        return

    try:
        temp_val = float(temp)
    except Exception:
        temp_val = None

    if temp_val is None:
        msg = f"Temperatura reportada: {temp}. Ajusta la ropa según tu confort."
    elif temp_val < 10:
        msg = "Hace frío, mejor abrigo."
    elif temp_val < 18:
        msg = "Temperatura fresca, una chaqueta ligera."
    else:
        msg = "Temperatura agradable, ropa ligera."

    try:
        lluvia_val = float(lluvia) if lluvia is not None else 0.0
    except Exception:
        lluvia_val = 0.0

    if lluvia_val and lluvia_val > 0:
        msg += " Y coge paraguas."

    logger.info(f"Recomendación de ropa: {msg}")


def register_default_rules() -> None:
    RULE_ENGINE.register_rule(
        Rule(
            id="wife_morning_greeting",
            description="Dar los buenos días a tu mujer cuando aparece por la mañana",
            conditions=[
                RuleCondition("presencia_mujer", condition_wife_morning_presence),
            ],
            actions=[
                RuleAction("saludo_mujer", action_good_morning_wife),
                RuleAction("recomendar_ropa", action_recommend_clothing),
            ],
        )
    )


def _run_smoke_test() -> None:
    logger.info("SMOKE TEST del Bloque B...")

    block_a.discover_all_sensors()

    register_default_rules()

    for _ in range(10):
        PRESENCE_MODEL.update_from_sensors()
        RULE_ENGINE.evaluate()
        time.sleep(1)


if __name__ == "__main__":
    _run_smoke_test()

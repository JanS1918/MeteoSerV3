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
                if reading.values.get("near"):
                    now = time.time()
                    if (
                        block_a.EXTERNAL_INTEGRATION_MODE
                        == block_a.ExternalIntegrationMode.MOCK
                    ):
                        if int(now) % 2 == 0:
                            self.last_seen_you = now
                        else:
                            self.last_seen_wife = now

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
    logger.info("Acción: Buenos días para tu mujer (simulado).")


def action_recommend_clothing() -> None:
    api_sensor = None
    for s in block_a.SENSOR_REGISTRY.list_sensors():
        if s.type == block_a.SensorType.VIRTUAL_EXTERNAL_API:
            api_sensor = s
            break

    if not api_sensor:
        logger.warning("No hay API meteorológica simulada disponible.")
        return

    reading = block_a.read_sensor(api_sensor.id)
    if not reading or not reading.valid:
        logger.warning("Lectura meteorológica inválida.")
        return

    temp = reading.values.get("temp", 20)
    condition = reading.values.get("condition", "sunny")

    if temp < 10:
        msg = "Hace frío, mejor abrigo."
    elif temp < 18:
        msg = "Temperatura fresca, una chaqueta ligera."
    else:
        msg = "Temperatura agradable, ropa ligera."

    if condition == "rain":
        msg += " Y coge paraguas."

    logger.info(f"Recomendación de ropa (simulada): {msg}")


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

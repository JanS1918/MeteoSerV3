"""
🧠 PERSISTENCIA DEL CEREBRO ESTADÍSTICO
═══════════════════════════════════════════════════════════════
Serialización y recuperación del estado del StatisticalBrain.

El Acorazado despierta con MEMORIA COMPLETA tras cada reinicio.

Metadata: motor: Quantum_Diamond_Persistent_v1.4
═══════════════════════════════════════════════════════════════
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from collections import deque
import numpy as np

logger = logging.getLogger("brain_persistence")

# ════════════════════════════════════════════════════════════════
# RUTA DE PERSISTENCIA
# ════════════════════════════════════════════════════════════════

PERSISTENCE_DIR = Path("data/brain_state")
STATE_FILE = PERSISTENCE_DIR / "statistical_brain_state.pkl"
METADATA_FILE = PERSISTENCE_DIR / "brain_metadata.json"


def ensure_persistence_directory():
    """Crea el directorio de persistencia si no existe."""
    PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════════
# SERIALIZACIÓN DEL ESTADO
# ════════════════════════════════════════════════════════════════

def serialize_brain_state(brain) -> Dict[str, Any]:
    """
    Serializa el estado completo del StatisticalBrain.
    
    Guarda:
    - Historial de todos los sensores (hasta 1440 valores)
    - Estados CUSUM (deriva acumulada)
    - Estados Kalman (predicción)
    - Métricas acumuladas
    - Modo observación
    
    Args:
        brain: Instancia de StatisticalBrain
        
    Returns:
        Dict con estado serializable
    """
    state = {
        "version": "1.4.0",
        "motor": "Quantum_Diamond_Persistent_v1.4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "history_length": brain.history_length,
        "observation_mode": brain.observation_mode,
        "observation_cycles": brain.observation_cycles,
        "observation_required": brain.observation_required,
        "history": {},
        "cusum_states": {},
        "kalman_states": {},
        "metrics": {}
    }
    
    # Serializar historial
    for sensor, hist in brain.history.items():
        state["history"][sensor] = list(hist)  # deque → list
    
    # Serializar estados CUSUM
    for sensor, cusum in brain.cusum_states.items():
        state["cusum_states"][sensor] = {
            "cumsum_pos": cusum.cumsum_pos,
            "cumsum_neg": cusum.cumsum_neg,
            "target": cusum.target,
            "drift_detected": cusum.drift_detected
        }
    
    # Serializar estados Kalman
    for sensor, kalman in brain.kalman_states.items():
        state["kalman_states"][sensor] = {
            "x": kalman.x.tolist(),
            "P": kalman.P.tolist(),
            "Q": kalman.Q.tolist(),
            "R": kalman.R
        }
    
    # Serializar métricas
    state["metrics"] = {
        "hampel_outliers": brain.metrics.hampel_outliers,
        "mahalanobis_alerts": brain.metrics.mahalanobis_alerts,
        "mann_kendall_trends": brain.metrics.mann_kendall_trends,
        "cusum_drifts": brain.metrics.cusum_drifts,
        "lyapunov_chaos": brain.metrics.lyapunov_chaos,
        "transfer_entropy_scores": brain.metrics.transfer_entropy_scores,
        "metadata": brain.metrics.metadata
    }
    
    return state


def save_brain_state(brain) -> bool:
    """
    Guarda el estado del cerebro en disco (pickle + metadata JSON).
    
    Args:
        brain: Instancia de StatisticalBrain
        
    Returns:
        True si se guardó correctamente
    """
    try:
        ensure_persistence_directory()
        
        # Serializar estado
        state = serialize_brain_state(brain)
        
        # Guardar con pickle (binario, rápido)
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Guardar metadata legible (JSON)
        metadata = {
            "version": state["version"],
            "motor": state["motor"],
            "timestamp": state["timestamp"],
            "sensors_count": len(state["history"]),
            "total_observations": sum(len(h) for h in state["history"].values()),
            "observation_mode": state["observation_mode"],
            "observation_cycles": state["observation_cycles"]
        }
        
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 ESTADO DEL CEREBRO GUARDADO: {len(state['history'])} sensores, "
                   f"{metadata['total_observations']} observaciones")
        return True
        
    except Exception as e:
        logger.exception(f"❌ ERROR al guardar estado del cerebro: {e}")
        return False


# ════════════════════════════════════════════════════════════════
# DESERIALIZACIÓN Y CARGA
# ════════════════════════════════════════════════════════════════

def load_brain_state() -> Optional[Dict[str, Any]]:
    """
    Carga el estado previo del cerebro desde disco.
    
    Returns:
        Dict con estado o None si no existe
    """
    try:
        if not STATE_FILE.exists():
            logger.info("📂 No hay estado previo del cerebro (primera ejecución)")
            return None
        
        with open(STATE_FILE, 'rb') as f:
            state = pickle.load(f)
        
        logger.info(f"🧠 ESTADO DEL CEREBRO CARGADO: {state['motor']} "
                   f"({state['timestamp']})")
        logger.info(f"   ├─ Sensores: {len(state['history'])}")
        logger.info(f"   ├─ Observaciones: {sum(len(h) for h in state['history'].values())}")
        logger.info(f"   └─ Modo observación: {state['observation_mode']}")
        
        return state
        
    except Exception as e:
        logger.exception(f"❌ ERROR al cargar estado del cerebro: {e}")
        return None


def restore_brain_state(brain, state: Dict[str, Any]) -> bool:
    """
    Restaura el estado del cerebro desde un dict serializado.
    
    Args:
        brain: Instancia de StatisticalBrain (nueva)
        state: Estado serializado
        
    Returns:
        True si se restauró correctamente
    """
    try:
        from collections import deque
        from dataclasses import replace
        
        # Restaurar configuración básica
        brain.history_length = state.get("history_length", 1440)
        brain.observation_mode = state.get("observation_mode", False)
        brain.observation_cycles = state.get("observation_cycles", 0)
        brain.observation_required = state.get("observation_required", 30)
        
        # Restaurar historial
        brain.history = {}
        for sensor, hist_list in state["history"].items():
            brain.history[sensor] = deque(hist_list, maxlen=brain.history_length)
        
        # Restaurar estados CUSUM
        from core.engines.statistical_brain import CUSUMState
        brain.cusum_states = {}
        for sensor, cusum_dict in state["cusum_states"].items():
            brain.cusum_states[sensor] = CUSUMState(
                cumsum_pos=cusum_dict["cumsum_pos"],
                cumsum_neg=cusum_dict["cumsum_neg"],
                target=cusum_dict["target"],
                drift_detected=cusum_dict["drift_detected"]
            )
        
        # Restaurar estados Kalman
        from core.engines.statistical_brain import KalmanState
        brain.kalman_states = {}
        for sensor, kalman_dict in state["kalman_states"].items():
            brain.kalman_states[sensor] = KalmanState(
                x=np.array(kalman_dict["x"]),
                P=np.array(kalman_dict["P"]),
                Q=np.array(kalman_dict["Q"]),
                R=kalman_dict["R"]
            )
        
        # Restaurar métricas
        metrics_data = state["metrics"]
        brain.metrics.hampel_outliers = metrics_data["hampel_outliers"]
        brain.metrics.mahalanobis_alerts = metrics_data["mahalanobis_alerts"]
        brain.metrics.mann_kendall_trends = metrics_data["mann_kendall_trends"]
        brain.metrics.cusum_drifts = metrics_data["cusum_drifts"]
        brain.metrics.lyapunov_chaos = metrics_data["lyapunov_chaos"]
        brain.metrics.transfer_entropy_scores = metrics_data["transfer_entropy_scores"]
        brain.metrics.metadata = metrics_data["metadata"]
        
        # Actualizar metadata con timestamp de restauración
        brain.metrics.metadata["restored_at"] = datetime.now(timezone.utc).isoformat()
        brain.metrics.metadata["original_timestamp"] = state["timestamp"]
        
        logger.info("✅ CEREBRO RESTAURADO CON ÉXITO")
        logger.info(f"   ├─ Memoria histórica: {len(brain.history)} sensores")
        logger.info(f"   ├─ CUSUM: {len(brain.cusum_states)} estados")
        logger.info(f"   ├─ Kalman: {len(brain.kalman_states)} filtros")
        logger.info(f"   └─ Alertas Hampel: {brain.metrics.hampel_outliers}")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ ERROR al restaurar estado del cerebro: {e}")
        return False


# ════════════════════════════════════════════════════════════════
# AUTO-PERSISTENCIA PERIÓDICA
# ════════════════════════════════════════════════════════════════

class BrainAutosaver:
    """
    Guardado automático periódico del estado del cerebro.
    
    Guarda cada N ciclos para evitar pérdida de memoria en caso de crash.
    """
    
    def __init__(self, brain, save_interval: int = 100):
        """
        Args:
            brain: Instancia de StatisticalBrain
            save_interval: Ciclos entre guardados (default 100 ≈ 15-30 min)
        """
        self.brain = brain
        self.save_interval = save_interval
        self.cycle_count = 0
        self.last_save = datetime.now(timezone.utc)
    
    def tick(self):
        """
        Incrementa contador y guarda si es necesario.
        
        Llamar en cada ciclo de ingestión.
        """
        self.cycle_count += 1
        
        if self.cycle_count >= self.save_interval:
            logger.info(f"⏰ AUTO-GUARDADO DEL CEREBRO (ciclo {self.cycle_count})")
            if save_brain_state(self.brain):
                self.cycle_count = 0
                self.last_save = datetime.now(timezone.utc)
    
    def force_save(self):
        """Fuerza un guardado inmediato."""
        logger.info("🛑 GUARDADO FORZADO DEL CEREBRO")
        save_brain_state(self.brain)
        self.cycle_count = 0
        self.last_save = datetime.now(timezone.utc)

# ⚛️ CEREBRO ESTADÍSTICO UNIVERSAL - QUANTUM_DIAMOND_PERSISTENT_v1.4
# ════════════════════════════════════════════════════════════════════════════
# Motor de Vigilancia, Coherencia y Predicción Física de Alta Fidelidad
# 
# Arquitectura: Organismo Único con fusión transversal de subfórmulas
# Metadata: motor: Quantum_Diamond_Persistent_v1.4
# 
# v1.4 - Memoria Permanente:
#   - Serialización y carga de estado completo (historial, CUSUM, Kalman)
#   - Resurrección instantánea tras reinicio (sin pérdida de aprendizaje)
#   - Auto-guardado periódico para resiliencia ante crashes
# ════════════════════════════════════════════════════════════════════════════

import math
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("statistical_brain")

# ════════════════════════════════════════════════════════════════════════════
# PIEZA 1: FILTRO DE HAMPEL SOBRE RESIDUO FÍSICO (LIMPIEZA QUIRÚRGICA)
# ════════════════════════════════════════════════════════════════════════════

def median(xs: List[float]) -> float:
    """Mediana robusta."""
    if not xs:
        return 0.0
    sorted_xs = sorted(xs)
    n = len(sorted_xs)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_xs[mid - 1] + sorted_xs[mid]) / 2.0
    return sorted_xs[mid]


def mad(xs: List[float]) -> float:
    """Median Absolute Deviation (MAD) - desviación absoluta mediana."""
    if not xs:
        return 0.0
    med = median(xs)
    return median([abs(x - med) for x in xs])


def hampel_filter_residual(
    value: float,
    history: List[float],
    physical_expected: float,
    k: float = 3.0,
    window: int = 20
) -> Tuple[bool, float, str]:
    """
    Filtro de Hampel sobre residuo físico (IAPWS-95, CIPM-2007).
    
    Args:
        value: Valor actual del sensor
        history: Historial de valores previos
        physical_expected: Valor esperado según modelo físico
        k: Umbral de detección (típicamente 3.0)
        window: Tamaño de ventana para cálculo de MAD
        
    Returns:
        (is_valid, residual, reason)
    """
    residual = value - physical_expected
    
    if len(history) < window:
        return True, residual, "OK_INICIAL"
    
    recent = history[-window:]
    
    # Calcular residuos históricos
    residuals = [h - physical_expected for h in recent]
    
    med = median(residuals)
    mad_val = mad(residuals)
    
    # Si MAD es muy pequeño, la serie es casi constante
    if mad_val < 1e-3:
        # Usar desviación estándar como fallback
        std_dev = math.sqrt(sum((r - med)**2 for r in residuals) / len(residuals))
        if std_dev < 1e-3:
            return True, residual, "OK_SERIE_CONSTANTE"
        mad_val = std_dev * 0.6745  # Convertir a escala MAD
    
    z_score = abs(residual - med) / (1.4826 * mad_val)
    
    if z_score > k:
        return False, residual, f"HAMPEL_OUTLIER_Z={z_score:.2f}"
    
    return True, residual, "OK"


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 2: DISTANCIA DE MAHALANOBIS (COHERENCIA GEOMÉTRICA MULTIVARIANTE)
# ════════════════════════════════════════════════════════════════════════════

def mahalanobis_distance(
    point: np.ndarray,
    mean: np.ndarray,
    cov_inv: np.ndarray
) -> float:
    """
    Distancia de Mahalanobis para detección de incoherencia geométrica.
    
    Args:
        point: Vector de observación actual
        mean: Vector de medias históricas
        cov_inv: Matriz de covarianza inversa
        
    Returns:
        Distancia de Mahalanobis
    """
    try:
        diff = point - mean
        return float(np.sqrt(diff.T @ cov_inv @ diff))
    except Exception:
        return 0.0


def detect_multivariate_incoherence(
    sensor_values: Dict[str, float],
    history: Dict[str, deque],
    threshold: float = 3.0
) -> Tuple[bool, float, str]:
    """
    Detecta incoherencia geométrica usando Mahalanobis.
    
    Args:
        sensor_values: Diccionario de valores actuales
        history: Historial de valores por sensor
        threshold: Umbral de distancia para alerta
        
    Returns:
        (is_coherent, distance, group)
    """
    # Grupos termo-hídricos, barométricos, radiométricos
    groups = {
        "termo_hidrico": ["temperatura", "humedad", "punto_rocio", "temp_ext", "hum_ext"],
        "barometrico": ["presion", "presion_atmosferica", "altitud"],
        "radiometrico": ["radiacion", "uv", "luz", "irradiancia"]
    }
    
    for group_name, keys in groups.items():
        available = [k for k in keys if k in sensor_values and k in history]
        if len(available) < 2:
            continue
        
        # Construir matriz de datos históricos
        matrix = []
        for k in available:
            hist = list(history[k])
            if len(hist) >= 20:
                matrix.append(hist[-20:])
        
        if len(matrix) < 2:
            continue
        
        try:
            data_matrix = np.array(matrix).T
            mean_vec = np.mean(data_matrix, axis=0)
            cov_matrix = np.cov(data_matrix.T)
            
            # Regularización para evitar singularidad
            cov_matrix += np.eye(len(available)) * 1e-6
            cov_inv = np.linalg.inv(cov_matrix)
            
            # Punto actual
            current_point = np.array([sensor_values[k] for k in available])
            
            # Distancia de Mahalanobis
            dist = mahalanobis_distance(current_point, mean_vec, cov_inv)
            
            if dist > threshold:
                return False, dist, f"INCOHERENCIA_GEOMETRICA_{group_name.upper()}"
        
        except Exception as e:
            logger.debug(f"Error en Mahalanobis para {group_name}: {e}")
            continue
    
    return True, 0.0, "COHERENTE"


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 3: TEST DE MANN-KENDALL Y PENDIENTE DE SEN (TENDENCIA ROBUSTA)
# ════════════════════════════════════════════════════════════════════════════

def mann_kendall_test(series: List[float]) -> Tuple[float, str]:
    """
    Test de Mann-Kendall para detección de tendencia monótona.
    
    Args:
        series: Serie temporal
        
    Returns:
        (tau, trend) donde tau es el estadístico y trend es la tendencia
    """
    n = len(series)
    if n < 10:
        return 0.0, "INSUFICIENTE"
    
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += np.sign(series[j] - series[i])
    
    # Estadístico tau normalizado
    tau = s / (n * (n - 1) / 2)
    
    if tau > 0.3:
        return tau, "TENDENCIA_CRECIENTE"
    elif tau < -0.3:
        return tau, "TENDENCIA_DECRECIENTE"
    else:
        return tau, "SIN_TENDENCIA"


def sen_slope(series: List[float]) -> float:
    """
    Pendiente de Sen (mediana de pendientes por pares).
    
    Args:
        series: Serie temporal
        
    Returns:
        Pendiente robusta
    """
    n = len(series)
    if n < 2:
        return 0.0
    
    slopes = []
    for i in range(n - 1):
        for j in range(i + 1, n):
            if j != i:
                slope = (series[j] - series[i]) / (j - i)
                slopes.append(slope)
    
    return median(slopes) if slopes else 0.0


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 4: CUSUM (DETECCIÓN DE DERIVA Y DRIFT)
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class CUSUMState:
    """Estado del algoritmo CUSUM para detección de deriva."""
    cumsum_pos: float = 0.0
    cumsum_neg: float = 0.0
    target: float = 0.0
    drift_detected: bool = False
    
    
def cusum_drift_detection(
    value: float,
    state: CUSUMState,
    threshold: float = 5.0,
    slack: float = 0.5
) -> Tuple[bool, CUSUMState]:
    """
    Algoritmo CUSUM para detección de deriva en sensores.
    
    Args:
        value: Valor actual
        state: Estado previo del CUSUM
        threshold: Umbral de alerta
        slack: Tolerancia de deriva aceptable
        
    Returns:
        (drift_detected, new_state)
    """
    # Actualizar target como media móvil exponencial
    alpha = 0.01
    new_target = alpha * value + (1 - alpha) * state.target
    
    # Desviación respecto al target
    deviation = value - new_target
    
    # CUSUM acumulado
    new_cumsum_pos = max(0, state.cumsum_pos + deviation - slack)
    new_cumsum_neg = max(0, state.cumsum_neg - deviation - slack)
    
    # Detección de deriva
    drift = new_cumsum_pos > threshold or new_cumsum_neg > threshold
    
    # Reset si se detecta deriva
    if drift:
        new_cumsum_pos = 0.0
        new_cumsum_neg = 0.0
    
    new_state = CUSUMState(
        cumsum_pos=new_cumsum_pos,
        cumsum_neg=new_cumsum_neg,
        target=new_target,
        drift_detected=drift
    )
    
    return drift, new_state


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 5: SAVITZKY-GOLAY (SUAVIZADO DE DIAMANTE SIN PERDER PICOS)
# ════════════════════════════════════════════════════════════════════════════

def savitzky_golay_filter(
    series: List[float],
    window: int = 11,
    order: int = 3
) -> List[float]:
    """
    Filtro de Savitzky-Golay para suavizado de alta calidad.
    
    Args:
        series: Serie temporal
        window: Tamaño de ventana (impar)
        order: Orden del polinomio
        
    Returns:
        Serie suavizada
    """
    if len(series) < window:
        return series
    
    if window % 2 == 0:
        window += 1
    
    half_window = window // 2
    
    # Coeficientes de Savitzky-Golay (simplificados)
    # Para orden 3, ventana 11
    coeffs = np.array([-0.084, 0.021, 0.103, 0.161, 0.196, 0.207, 
                       0.196, 0.161, 0.103, 0.021, -0.084])
    
    smoothed = []
    for i in range(len(series)):
        if i < half_window or i >= len(series) - half_window:
            smoothed.append(series[i])
        else:
            window_data = series[i - half_window:i + half_window + 1]
            smoothed.append(float(np.dot(coeffs, window_data)))
    
    return smoothed


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 6: EXPONENTE DE LYAPUNOV (CAOS ATMOSFÉRICO)
# ════════════════════════════════════════════════════════════════════════════

def lyapunov_exponent(series: List[float], delay: int = 1) -> float:
    """
    Exponente de Lyapunov para detección de caos atmosférico.
    
    Args:
        series: Serie temporal
        delay: Retardo de embedding
        
    Returns:
        Exponente de Lyapunov (positivo = caos, negativo = estable)
    """
    n = len(series)
    if n < 50:
        return 0.0
    
    # Reconstrucción del espacio de fases (embedding)
    embedded = []
    for i in range(n - delay):
        embedded.append([series[i], series[i + delay]])
    
    if len(embedded) < 10:
        return 0.0
    
    # Cálculo simplificado del exponente
    divergences = []
    for i in range(len(embedded) - 10):
        p1 = np.array(embedded[i])
        p2 = np.array(embedded[i + 1])
        
        # Distancia inicial
        d0 = np.linalg.norm(p2 - p1)
        
        if d0 < 1e-9:
            continue
        
        # Distancia después de 10 pasos
        if i + 11 < len(embedded):
            p1_future = np.array(embedded[i + 10])
            p2_future = np.array(embedded[i + 11])
            d1 = np.linalg.norm(p2_future - p1_future)
            
            if d1 > 1e-9:
                divergences.append(math.log(d1 / d0) / 10.0)
    
    if not divergences:
        return 0.0
    
    return float(np.mean(divergences))


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 7: ENTROPÍA DE TRANSFERENCIA (CAUSALIDAD FÍSICA)
# ════════════════════════════════════════════════════════════════════════════

def transfer_entropy(
    source: List[float],
    target: List[float],
    lag: int = 1,
    bins: int = 10
) -> float:
    """
    Entropía de Transferencia para certificar causalidad física.
    
    Args:
        source: Serie de la variable fuente (ej: radiación)
        target: Serie de la variable objetivo (ej: UV)
        lag: Retardo temporal
        bins: Número de bins para discretización
        
    Returns:
        Entropía de transferencia (mayor = más causalidad)
    """
    n = min(len(source), len(target))
    if n < lag + 10:
        return 0.0

    # Ajuste dinámico de bins para evitar sobre-discretización
    bins_eff = min(bins, max(3, int(math.sqrt(n))))

    def _digitize(series: List[float]) -> Optional[np.ndarray]:
        edges = np.quantile(series, np.linspace(0.0, 1.0, bins_eff + 1))
        edges = np.unique(edges)
        if len(edges) <= 2:
            return None
        return np.digitize(series, edges[1:-1], right=False)

    source_disc = _digitize(source[:n])
    target_disc = _digitize(target[:n])
    if source_disc is None or target_disc is None:
        return 0.0

    def _compute_te(src_disc: np.ndarray, tgt_disc: np.ndarray) -> float:
        from collections import Counter
        count_xyz = Counter()
        count_yx = Counter()
        count_yy = Counter()
        count_y = Counter()

        for i in range(lag, n - 1):
            y_next = int(tgt_disc[i + 1])
            y_prev = int(tgt_disc[i])
            x_prev = int(src_disc[i - lag])
            count_xyz[(y_next, y_prev, x_prev)] += 1
            count_yx[(y_prev, x_prev)] += 1
            count_yy[(y_next, y_prev)] += 1
            count_y[y_prev] += 1

        total = sum(count_xyz.values())
        if total <= 0:
            return 0.0

        alpha = 1e-6  # suavizado de Laplace
        te_val = 0.0
        for (y_next, y_prev, x_prev), c_xyz in count_xyz.items():
            p_xyz = c_xyz / total
            p_cond_1 = (c_xyz + alpha) / (count_yx[(y_prev, x_prev)] + alpha * bins_eff)
            p_cond_2 = (count_yy[(y_next, y_prev)] + alpha) / (count_y[y_prev] + alpha * bins_eff)
            ratio = p_cond_1 / max(p_cond_2, 1e-12)
            te_val += p_xyz * math.log(max(ratio, 1e-12))

        return max(0.0, float(te_val))

    te_raw = _compute_te(source_disc, target_disc)

    def _mutual_info(a: np.ndarray, b: np.ndarray) -> float:
        from collections import Counter
        count_ab = Counter()
        count_a = Counter()
        count_b = Counter()
        for i in range(len(a)):
            count_ab[(int(a[i]), int(b[i]))] += 1
            count_a[int(a[i])] += 1
            count_b[int(b[i])] += 1
        total = len(a)
        if total == 0:
            return 0.0
        mi = 0.0
        for (ai, bi), cab in count_ab.items():
            p_ab = cab / total
            p_a = count_a[ai] / total
            p_b = count_b[bi] / total
            mi += p_ab * math.log(max(p_ab / max(p_a * p_b, 1e-12), 1e-12))
        return max(0.0, float(mi))

    te_proxy = _mutual_info(source_disc[:-lag], target_disc[lag:])

    # Corrección de sesgo por aleatoriedad (shuffling determinista)
    if n >= 30:
        rng = np.random.default_rng(0)
        biases = []
        for _ in range(3):
            shuffled = rng.permutation(source_disc)
            biases.append(_compute_te(shuffled, target_disc))
        bias = float(np.mean(biases)) if biases else 0.0
        te_adj = max(0.0, te_raw - 0.5 * bias)
        return max(te_adj, te_proxy)

    return max(te_raw, te_proxy)


# ════════════════════════════════════════════════════════════════════════════
# PIEZA 8: FILTRO DE KALMAN EXTENDIDO (EKF) CON MODELO FÍSICO
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class KalmanState:
    """Estado del filtro de Kalman Extendido."""
    x: np.ndarray = field(default_factory=lambda: np.zeros(2))
    P: np.ndarray = field(default_factory=lambda: np.eye(2))
    Q: np.ndarray = field(default_factory=lambda: np.eye(2) * 0.01)
    R: float = 0.1
    

def ekf_predict(
    state: KalmanState,
    dt: float,
    physical_model: callable
) -> KalmanState:
    """
    Predicción del filtro de Kalman Extendido usando modelo físico.
    
    Args:
        state: Estado previo
        dt: Intervalo temporal
        physical_model: Función de transición física
        
    Returns:
        Estado predicho
    """
    # Predicción usando modelo físico
    x_pred = physical_model(state.x, dt)
    
    # Jacobiano (simplificado)
    F = np.eye(len(state.x))
    
    # Covarianza predicha
    P_pred = F @ state.P @ F.T + state.Q
    
    return KalmanState(x=x_pred, P=P_pred, Q=state.Q, R=state.R)


def ekf_update(
    state: KalmanState,
    measurement: float,
    measurement_index: int = 0
) -> KalmanState:
    """
    Actualización del filtro de Kalman Extendido con medición.
    
    Args:
        state: Estado predicho
        measurement: Medición del sensor
        measurement_index: Índice de la variable medida
        
    Returns:
        Estado actualizado
    """
    # Matriz de observación
    H = np.zeros((1, len(state.x)))
    H[0, measurement_index] = 1.0
    
    # Innovación
    y = measurement - H @ state.x
    
    # Covarianza de innovación
    S = H @ state.P @ H.T + state.R
    
    # Ganancia de Kalman
    if S > 1e-9:
        K = state.P @ H.T / S
    else:
        K = np.zeros((len(state.x), 1))
    
    # Actualización
    x_updated = state.x + K.flatten() * y
    P_updated = (np.eye(len(state.x)) - K @ H) @ state.P
    
    return KalmanState(x=x_updated, P=P_updated, Q=state.Q, R=state.R)


# ════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: CEREBRO ESTADÍSTICO UNIVERSAL
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class StatisticalBrainMetrics:
    """Métricas del Cerebro Estadístico."""
    hampel_outliers: int = 0
    mahalanobis_alerts: int = 0
    mann_kendall_trends: Dict[str, str] = field(default_factory=dict)
    cusum_drifts: int = 0
    lyapunov_chaos: float = 0.0
    transfer_entropy_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "motor": "Quantum_Diamond_Persistent_v1.4",
        "version": "1.4.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


class StatisticalBrain:
    """
    Cerebro Estadístico Universal para vigilancia y coherencia física.
    
    Integración transversal con todos los niveles físicos:
    - Nivel 1: Psicrometría (Hampel, Mahalanobis)
    - Nivel 2: Densidad (CUSUM)
    - Nivel 3: Astronomía (Savitzky-Golay)
    - Nivel 4: Cetrería (Entropía de Transferencia)
    - Nivel 5: Edificio (EKF)
    
    ARQUITECTURA DE LIMPIEZA:
    - observation_mode: True tras limpiar buffers (silencio quirúrgico)
    - observation_cycles: Ciclos necesarios antes de emitir veredictos
    - confidence_threshold: Umbral de datos acumulados para confiar en flags
    """
    
    def __init__(self, history_length: int = 1440, restore_state: bool = True):
        self.history: Dict[str, deque] = {}
        self.history_length = history_length
        self.cusum_states: Dict[str, CUSUMState] = {}
        self.kalman_states: Dict[str, KalmanState] = {}
        self.metrics = StatisticalBrainMetrics()
        
        # Estado de observación post-limpieza
        self.observation_mode = False  # Modo "silencio" tras limpiar
        self.observation_cycles = 0    # Ciclos en modo observación
        self.observation_required = 30 # Ciclos mínimos antes de emitir flags (aprox. 5-10 min con datos cada 10-20s)
        
        # 🧠 RESURRECCIÓN: Cargar estado previo si existe
        if restore_state:
            try:
                from core.engines.brain_persistence import load_brain_state, restore_brain_state
                saved_state = load_brain_state()
                if saved_state:
                    restore_brain_state(self, saved_state)
                    logger.info("✨ CEREBRO DESPIERTO CON MEMORIA COMPLETA")
            except Exception as e:
                logger.exception(f"⚠️ No se pudo restaurar estado previo: {e}")
                logger.info("🆕 Iniciando cerebro desde cero")

    def enter_observation_mode(self):
        """Entra en modo de observación quirúrgica: silencio total de flags tras limpieza."""
        self.observation_mode = True
        self.observation_cycles = 0
        logger.info("🧹 CEREBRO EN MODO OBSERVACIÓN: Silencio quirúrgico hasta acumular confianza")
        
    def ingest(
        self,
        sensor_values: Dict[str, float],
        physical_models: Optional[Dict[str, callable]] = None
    ) -> Dict[str, Any]:
        """
        Ingesta de datos con todas las validaciones del Cerebro Universal.
        
        LÓGICA DE OBSERVACIÓN:
        - En observation_mode: Acumula datos sin emitir flags (silencio quirúrgico)
        - Tras observation_required ciclos: Se emiten flags reales
        - Flags internos (Hampel, Mahalanobis, etc.) siempre se aplican al historial
        
        Args:
            sensor_values: Diccionario de valores de sensores
            physical_models: Modelos físicos esperados por sensor
            
        Returns:
            Resultado con flags, scores y metadatos
        """
        results = {
            "filtered_values": {},
            "flags": {},
            "scores": {},
            "explanations": {},
            "metadata": self.metrics.metadata.copy(),
            "observation_mode": self.observation_mode
        }
        
        # Incrementar ciclo de observación si estamos en modo silencio
        if self.observation_mode:
            self.observation_cycles += 1
            if self.observation_cycles >= self.observation_required:
                self.observation_mode = False
                logger.info(f"✓ OBSERVACIÓN COMPLETADA: {self.observation_cycles} ciclos. Cerebro activo de nuevo.")
        
        # Determinar si podemos emitir flags en esta ingesta
        can_emit_flags = not self.observation_mode
        
        # 1. Filtro de Hampel sobre residuo físico
        # NOTA: SIEMPRE validamos y almacenamos, pero solo reportamos flags si no estamos en observación
        for sensor, value in sensor_values.items():
            if sensor not in self.history:
                self.history[sensor] = deque(maxlen=self.history_length)
            # Modelo físico esperado
            if physical_models and sensor in physical_models:
                expected = physical_models[sensor](value)
            else:
                expected = value
            valid, residual, reason = hampel_filter_residual(
                value,
                list(self.history[sensor]),
                expected
            )
            if valid:
                self.history[sensor].append(value)
                results["filtered_values"][sensor] = value
                results["flags"][sensor] = "OK"
            else:
                # Valor fuera del rango esperado, pero lo almacenamos igualmente
                self.history[sensor].append(value)
                results["filtered_values"][sensor] = value
                # Solo reportar el flag si no estamos en observación
                if can_emit_flags:
                    results["flags"][sensor] = reason
                    results["explanations"][sensor] = f"Residuo={residual:.3f}"
                    self.metrics.hampel_outliers += 1
                else:
                    # En observación: silencio, pero registramos internamente
                    results["flags"][sensor] = "OK_OBSERVANDO"
        
        # 2. Coherencia multivariante (Mahalanobis)
        coherent, dist, group = detect_multivariate_incoherence(
            results["filtered_values"],
            self.history
        )
        if not coherent and can_emit_flags:
            results["flags"]["coherencia"] = group
            results["scores"]["mahalanobis"] = dist
            self.metrics.mahalanobis_alerts += 1
        
        # 3. Tendencia (Mann-Kendall) y Deriva (CUSUM)
        for sensor, hist in self.history.items():
            if len(hist) >= 20:
                # Mann-Kendall
                tau, trend = mann_kendall_test(list(hist))
                if trend != "SIN_TENDENCIA" and can_emit_flags:
                    results["flags"][f"{sensor}_tendencia"] = trend
                    self.metrics.mann_kendall_trends[sensor] = trend
                # CUSUM
                if sensor not in self.cusum_states:
                    self.cusum_states[sensor] = CUSUMState(target=hist[-1])
                drift, new_state = cusum_drift_detection(
                    hist[-1],
                    self.cusum_states[sensor]
                )
                self.cusum_states[sensor] = new_state
                if drift and can_emit_flags:
                    results["flags"][f"{sensor}_deriva"] = "DRIFT_DETECTADO"
                    results["explanations"][f"{sensor}_deriva"] = "MANTENIMIENTO_RECOMENDADO"
                    self.metrics.cusum_drifts += 1
        
        # 4. Caos atmosférico (Lyapunov)
        for sensor in ["temperatura", "presion", "viento"]:
            if sensor in self.history and len(self.history[sensor]) >= 50:
                lyap = lyapunov_exponent(list(self.history[sensor]))
                if lyap > 0.1 and can_emit_flags:
                    results["flags"][f"{sensor}_caos"] = "INESTABILIDAD_DETECTADA"
                    results["scores"]["lyapunov"] = lyap
                    self.metrics.lyapunov_chaos = max(self.metrics.lyapunov_chaos, lyap)
        
        # 5. Causalidad (Entropía de Transferencia)
        causal_pairs = [
            ("radiacion", "uv"),
            ("temperatura", "humedad"),
            ("viento", "racha")
        ]
        
        for source, target in causal_pairs:
            if source in self.history and target in self.history:
                if len(self.history[source]) >= 20 and len(self.history[target]) >= 20:
                    te = transfer_entropy(
                        list(self.history[source]),
                        list(self.history[target])
                    )
                    results["scores"][f"causalidad_{source}_{target}"] = te
                    self.metrics.transfer_entropy_scores[f"{source}→{target}"] = te
        
        return results
    
    def smooth_series(self, sensor: str, window: int = 11, order: int = 3) -> List[float]:
        """
        Suavizado de Savitzky-Golay para series temporales.
        
        Uso: Limpiar inputs antes de física de precisión (astronomía, vuelo).
        """
        if sensor not in self.history:
            return []
        
        return savitzky_golay_filter(list(self.history[sensor]), window, order)
    
    def predict_with_ekf(
        self,
        sensor: str,
        physical_model: callable,
        dt: float = 60.0
    ) -> Optional[float]:
        """
        Predicción usando Filtro de Kalman Extendido con modelo físico.
        
        Uso: Predicción de estados futuros (sorción GAB, humedad en paredes).
        """
        if sensor not in self.kalman_states:
            if sensor in self.history and len(self.history[sensor]) > 0:
                initial_value = self.history[sensor][-1]
                self.kalman_states[sensor] = KalmanState(
                    x=np.array([initial_value, 0.0])
                )
            else:
                return None
        
        # Predicción
        state_pred = ekf_predict(self.kalman_states[sensor], dt, physical_model)
        
        # Actualización con medición (si disponible)
        if sensor in self.history and len(self.history[sensor]) > 0:
            measurement = self.history[sensor][-1]
            state_updated = ekf_update(state_pred, measurement)
            self.kalman_states[sensor] = state_updated
            return float(state_updated.x[0])
        else:
            self.kalman_states[sensor] = state_pred
            return float(state_pred.x[0])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene todas las métricas del Cerebro Estadístico."""
        return {
            "hampel_outliers_total": self.metrics.hampel_outliers,
            "mahalanobis_alerts_total": self.metrics.mahalanobis_alerts,
            "mann_kendall_trends": self.metrics.mann_kendall_trends,
            "cusum_drifts_total": self.metrics.cusum_drifts,
            "lyapunov_max": self.metrics.lyapunov_chaos,
            "transfer_entropy": self.metrics.transfer_entropy_scores,
            "metadata": self.metrics.metadata
        }

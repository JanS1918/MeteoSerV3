"""
🛡️ CAPA 39: MOS CLUSTERING VALIDATOR
Protege el aprendizaje del MOS V47.2 validando que los escenarios físicos
estén correctamente clasificados ANTES de aprender de ellos.

EVITA:
- Aprender de escenarios mal clasificados
- Contaminar ALFA con eventos BETA/GAMMA
- Correcciones BIAS basadas en física incorrecta

VALIDA:
✅ Escenario clasificado coherente con condiciones reales
✅ No hay contradicciones en parámetros (ej: "radiativo" con viento alto)
✅ Similitud >85% entre eventos del mismo escenario
✅ No hay drift en la clasificación (estabilidad temporal)

AUTOR: V47.3 SUMMUM - Guardian Inteligente
FECHA: 2026-02-05
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MOSClusteringValidator:
    """
    Validador de clasificación de escenarios MOS.
    
    Verifica que cada evento clasificado es coherente con sus condiciones
    físicas y que el clustering mantiene pureza matemática.
    """
    
    # Umbrales de coherencia para cada escenario
    UMBRALES_COHERENCIA = {
        "ALFA": {  # Radiativo
            "viento_max": 2.0,      # m/s
            "cobertura_max": 30,    # %
            "hora_min": 20,         # 20:00
            "hora_max": 8,          # 08:00
        },
        "BETA": {  # Inversión
            "hr_min": 85,           # %
            "cobertura_min": 60,    # %
        },
        "GAMMA": {  # Ventoso
            "viento_min": 3.5,      # m/s
        },
        "DELTA": {  # Estándar (resto)
            # Sin restricciones específicas
        }
    }
    
    # Umbrales de validación
    SIMILITUD_MINIMA = 85.0         # % similitud entre eventos del mismo escenario
    DRIFT_MAX_CLASIFICACION = 0.15  # 15% cambio en distribución escenarios (30 días)
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.estado_file = self.data_dir / "mos_clustering_validator_estado.json"
        self.estado = self._cargar_estado()
        
        logger.info("✅ MOSClusteringValidator inicializado")
    
    def _cargar_estado(self) -> Dict:
        """Carga estado persistente del validador."""
        if self.estado_file.exists():
            with open(self.estado_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "validaciones_totales": 0,
            "errores_detectados": 0,
            "escenarios_validados": {
                "ALFA": {"correctos": 0, "incorrectos": 0},
                "BETA": {"correctos": 0, "incorrectos": 0},
                "GAMMA": {"correctos": 0, "incorrectos": 0},
                "DELTA": {"correctos": 0, "incorrectos": 0}
            },
            "drift_historico": [],  # [{timestamp, distribucion}]
            "ultima_actualizacion": None
        }
    
    def _guardar_estado(self):
        """Guarda estado persistente."""
        self.estado["ultima_actualizacion"] = datetime.now().isoformat()
        with open(self.estado_file, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)
    
    def validar_clasificacion(
        self,
        escenario: str,
        condiciones: Dict[str, float]
    ) -> Tuple[bool, str, float]:
        """
        Valida que un escenario clasificado sea coherente con condiciones reales.
        
        Args:
            escenario: ALFA|BETA|GAMMA|DELTA
            condiciones: {"viento": 1.2, "hr": 55, "cobertura_nubes": 10, "hora": 22}
        
        Returns:
            (es_valido, razon, confianza_validacion)
        """
        self.estado["validaciones_totales"] += 1
        
        # Validar ALFA (Radiativo)
        if escenario == "ALFA":
            umbrales = self.UMBRALES_COHERENCIA["ALFA"]
            
            # Viento debe ser bajo
            if condiciones.get("viento", 0) > umbrales["viento_max"]:
                self._registrar_error("ALFA", "viento_alto")
                return (False, f"ALFA con viento {condiciones['viento']:.1f} m/s > {umbrales['viento_max']} m/s", 0.0)
            
            # Cielo despejado
            if condiciones.get("cobertura_nubes", 100) > umbrales["cobertura_max"]:
                self._registrar_error("ALFA", "nublado")
                return (False, f"ALFA con cobertura {condiciones['cobertura_nubes']:.0f}% > {umbrales['cobertura_max']}%", 0.0)
            
            # Noche
            hora = condiciones.get("hora", 12)
            if not (hora >= umbrales["hora_min"] or hora <= umbrales["hora_max"]):
                self._registrar_error("ALFA", "horario_diurno")
                return (False, f"ALFA en hora {hora}:00 (debe ser nocturno)", 0.0)
        
        # Validar BETA (Inversión)
        elif escenario == "BETA":
            umbrales = self.UMBRALES_COHERENCIA["BETA"]
            
            # Humedad alta
            if condiciones.get("hr", 0) < umbrales["hr_min"]:
                self._registrar_error("BETA", "hr_baja")
                return (False, f"BETA con HR {condiciones['hr']:.0f}% < {umbrales['hr_min']}%", 0.0)
            
            # Nublado
            if condiciones.get("cobertura_nubes", 0) < umbrales["cobertura_min"]:
                self._registrar_error("BETA", "despejado")
                return (False, f"BETA con cobertura {condiciones['cobertura_nubes']:.0f}% < {umbrales['cobertura_min']}%", 0.0)
        
        # Validar GAMMA (Ventoso)
        elif escenario == "GAMMA":
            umbrales = self.UMBRALES_COHERENCIA["GAMMA"]
            
            # Viento alto
            if condiciones.get("viento", 0) < umbrales["viento_min"]:
                self._registrar_error("GAMMA", "viento_bajo")
                return (False, f"GAMMA con viento {condiciones['viento']:.1f} m/s < {umbrales['viento_min']} m/s", 0.0)
        
        # DELTA (Estándar) siempre válido (es el catch-all)
        
        # Clasificación coherente
        self._registrar_exito(escenario)
        confianza = self._calcular_confianza_validacion(escenario, condiciones)
        
        return (True, "Escenario coherente con condiciones físicas", confianza)
    
    def validar_similitud_cluster(
        self,
        escenario: str,
        evento_nuevo: Dict,
        eventos_cluster: List[Dict]
    ) -> Tuple[bool, str, float]:
        """
        Valida que un evento nuevo sea similar a los eventos del cluster.
        
        Args:
            escenario: ALFA|BETA|GAMMA|DELTA
            evento_nuevo: Condiciones del evento nuevo
            eventos_cluster: Lista de eventos ya en el cluster
        
        Returns:
            (es_similar, razon, similitud_promedio)
        """
        if not eventos_cluster:
            return (True, "Primer evento del cluster", 100.0)
        
        similitudes = []
        
        for evento in eventos_cluster[-10:]:  # Últimos 10 eventos
            similitud = self._calcular_similitud(evento_nuevo, evento)
            similitudes.append(similitud)
        
        similitud_promedio = sum(similitudes) / len(similitudes)
        
        if similitud_promedio < self.SIMILITUD_MINIMA:
            return (
                False,
                f"Similitud {similitud_promedio:.1f}% < {self.SIMILITUD_MINIMA}%",
                similitud_promedio
            )
        
        return (True, f"Evento similar al cluster {escenario}", similitud_promedio)
    
    def detectar_drift_clasificacion(self) -> Tuple[bool, str, float]:
        """
        Detecta si la distribución de escenarios ha cambiado significativamente
        en los últimos 30 días (cambio climático, estacionalidad, etc.).
        
        Returns:
            (hay_drift, descripcion, magnitud_drift)
        """
        # Registrar distribución actual
        distribucion_actual = {
            esc: self.estado["escenarios_validados"][esc]["correctos"]
            for esc in ["ALFA", "BETA", "GAMMA", "DELTA"]
        }
        
        total = sum(distribucion_actual.values())
        if total == 0:
            return (False, "Sin datos suficientes", 0.0)
        
        distribucion_pct = {
            esc: (count / total) * 100
            for esc, count in distribucion_actual.items()
        }
        
        # Guardar en histórico
        self.estado["drift_historico"].append({
            "timestamp": datetime.now().isoformat(),
            "distribucion": distribucion_pct
        })
        
        # Mantener solo últimos 30 días
        fecha_limite = datetime.now() - timedelta(days=30)
        self.estado["drift_historico"] = [
            entry for entry in self.estado["drift_historico"]
            if datetime.fromisoformat(entry["timestamp"]) > fecha_limite
        ]
        
        # Comparar con distribución de hace 30 días
        if len(self.estado["drift_historico"]) < 2:
            return (False, "Histórico insuficiente", 0.0)
        
        distribucion_antigua = self.estado["drift_historico"][0]["distribucion"]
        
        # Calcular diferencia absoluta promedio
        diferencias = [
            abs(distribucion_pct[esc] - distribucion_antigua[esc])
            for esc in ["ALFA", "BETA", "GAMMA", "DELTA"]
        ]
        
        drift_promedio = sum(diferencias) / len(diferencias)
        
        if drift_promedio > self.DRIFT_MAX_CLASIFICACION * 100:
            return (
                True,
                f"Distribución cambió {drift_promedio:.1f}% en 30 días",
                drift_promedio
            )
        
        return (False, "Distribución estable", drift_promedio)
    
    def _calcular_similitud(self, evento1: Dict, evento2: Dict) -> float:
        """
        Calcula similitud entre dos eventos (0-100%).
        
        Usa la misma lógica que mos_clustering_v472.py
        """
        parametros = ["viento", "hr", "cobertura_nubes", "temperatura"]
        pesos = [0.3, 0.3, 0.2, 0.2]
        
        similitud_total = 0.0
        
        for param, peso in zip(parametros, pesos):
            val1 = evento1.get(param, 0)
            val2 = evento2.get(param, 0)
            
            if param == "viento":
                max_diff = 10.0
            elif param == "hr":
                max_diff = 30.0
            elif param == "cobertura_nubes":
                max_diff = 40.0
            elif param == "temperatura":
                max_diff = 8.0
            else:
                max_diff = 1.0
            
            diff = abs(val1 - val2)
            similitud_param = max(0, 100 * (1 - diff / max_diff))
            similitud_total += similitud_param * peso
        
        return similitud_total
    
    def _calcular_confianza_validacion(self, escenario: str, condiciones: Dict) -> float:
        """
        Calcula confianza de la validación basada en historial.
        
        Returns:
            Confianza (0-100%)
        """
        stats = self.estado["escenarios_validados"][escenario]
        total = stats["correctos"] + stats["incorrectos"]
        
        if total == 0:
            return 75.0  # Confianza inicial
        
        accuracy = (stats["correctos"] / total) * 100
        return accuracy
    
    def _registrar_exito(self, escenario: str):
        """Registra validación exitosa."""
        self.estado["escenarios_validados"][escenario]["correctos"] += 1
        self._guardar_estado()
    
    def _registrar_error(self, escenario: str, tipo_error: str):
        """Registra error de clasificación."""
        self.estado["escenarios_validados"][escenario]["incorrectos"] += 1
        self.estado["errores_detectados"] += 1
        
        logger.warning(
            f"⚠️ Error clasificación {escenario}: {tipo_error} "
            f"(Total errores: {self.estado['errores_detectados']})"
        )
        
        self._guardar_estado()
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas completas del validador.
        
        Returns:
            {
                "validaciones_totales": 1523,
                "errores_detectados": 18,
                "accuracy_global": 98.8,
                "accuracy_por_escenario": {...},
                "drift_actual": 2.3
            }
        """
        total = self.estado["validaciones_totales"]
        errores = self.estado["errores_detectados"]
        
        accuracy_global = ((total - errores) / total * 100) if total > 0 else 0.0
        
        accuracy_por_escenario = {}
        for esc in ["ALFA", "BETA", "GAMMA", "DELTA"]:
            stats = self.estado["escenarios_validados"][esc]
            total_esc = stats["correctos"] + stats["incorrectos"]
            accuracy_esc = (stats["correctos"] / total_esc * 100) if total_esc > 0 else 0.0
            accuracy_por_escenario[esc] = accuracy_esc
        
        # Drift actual
        hay_drift, _, magnitud_drift = self.detectar_drift_clasificacion()
        
        return {
            "validaciones_totales": total,
            "errores_detectados": errores,
            "accuracy_global": round(accuracy_global, 2),
            "accuracy_por_escenario": {
                esc: round(acc, 2) for esc, acc in accuracy_por_escenario.items()
            },
            "drift_actual": round(magnitud_drift, 2),
            "hay_drift": hay_drift
        }


# ============================================================================
# INTEGRACIÓN CON MOS CLUSTERING V47.2
# ============================================================================

def integrar_validador_en_mos():
    """
    Ejemplo de integración del validador en mos_clustering_v472.py
    
    Añadir al método clasificar_escenario():
    
    ```python
    # En mos_clustering_v472.py
    from core.validation.mos_clustering_validator import MOSClusteringValidator
    
    self.validador = MOSClusteringValidator()
    
    def clasificar_escenario(self, condiciones):
        escenario = self._determinar_escenario(condiciones)
        
        # VALIDAR CLASIFICACIÓN
        es_valido, razon, confianza = self.validador.validar_clasificacion(
            escenario, condiciones
        )
        
        if not es_valido:
            logger.error(f"❌ Clasificación inválida: {razon}")
            # Fallback a DELTA (estándar)
            escenario = "DELTA"
        
        return escenario
    ```
    """
    pass


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    validador = MOSClusteringValidator()
    
    # Test ALFA correcto
    es_valido, razon, conf = validador.validar_clasificacion(
        "ALFA",
        {"viento": 1.2, "hr": 55, "cobertura_nubes": 10, "hora": 22}
    )
    print(f"ALFA válido: {es_valido} - {razon} (confianza: {conf:.1f}%)")
    
    # Test ALFA incorrecto (viento alto)
    es_valido, razon, conf = validador.validar_clasificacion(
        "ALFA",
        {"viento": 5.0, "hr": 55, "cobertura_nubes": 10, "hora": 22}
    )
    print(f"ALFA inválido: {es_valido} - {razon} (confianza: {conf:.1f}%)")
    
    # Estadísticas
    stats = validador.obtener_estadisticas()
    print(f"\n📊 Estadísticas: {json.dumps(stats, indent=2)}")

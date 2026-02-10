"""
═══════════════════════════════════════════════════════════════════════════
[GUARDIAN] V47.0 MOS (MODEL OUTPUT STATISTICS) - VALIDACIÓN INTERNA
═══════════════════════════════════════════════════════════════════════════

PROPÓSITO:
    Auditoría continua de predicciones vs realidad.
    Detecta bias sistemático y auto-ajusta coeficientes.

ESTRATEGIA MOS:
    1. Registrar predicciones en momento T
    2. Esperar N horas
    3. Comparar con mediciones reales
    4. Calcular error: MAE, RMSE, BIAS
    5. Si BIAS > umbral → ajustar coeficiente
    6. Publicar confianza (0-100%)

PARÁMETROS VALIDADOS:
    - Temperatura mínima (Deardorff V47.0)
    - UTCI (v1 vs v2)
    - ET0 (FAO-56 vs Wright)
    - Kalman Soil (filtrado vs raw)
    - Probabilidad lluvia (Sundqvist)

AUTOR: V47.0 SUMMUM
FECHA: 2025-01-28
═══════════════════════════════════════════════════════════════════════════
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN MOS
# ═══════════════════════════════════════════════════════════════════════════

MOS_CONFIG = {
    "registro_path": "data/mos_predictions.json",
    "resultados_path": "data/mos_validation_results.json",
    
    "ventana_validacion_horas": {
        "temperatura_minima": 12,  # Validar al día siguiente
        "utci": 1,                 # Validar en 1 hora
        "et0": 24,                 # Validar diario
        "humedad_suelo": 6,        # Validar 6h después
        "probabilidad_lluvia": 3,  # Validar en 3 horas
    },
    
    "umbrales_bias": {
        "temperatura_minima": 0.5,  # ±0.5°C
        "utci": 2.0,                # ±2°C
        "et0": 0.3,                 # ±0.3 mm
        "humedad_suelo": 5.0,       # ±5%
        "probabilidad_lluvia": 15.0,# ±15%
    },
    
    "coeficientes_ajuste": {
        "temperatura_minima": 1.0,
        "utci_v2": 1.0,
        "et0_wright": 1.0,
        "kalman_soil": 1.0,
        "prob_lluvia": 1.0,
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# [STATS] CLASE MOS VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class MOSValidator:
    """Validador MOS para predicciones MeteoSerV3."""
    
    def __init__(self, bus=None):
        self.bus = bus
        self.registro_path = Path(MOS_CONFIG["registro_path"])
        self.resultados_path = Path(MOS_CONFIG["resultados_path"])
        self.predicciones: List[Dict] = []
        self.resultados: Dict = {"validaciones": [], "coeficientes": MOS_CONFIG["coeficientes_ajuste"]}
        
        # Cargar estado previo
        self._cargar_estado()
        
        logging.info("[GUARDIAN] MOS Validator V47.0 inicializado")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1️⃣ REGISTRO DE PREDICCIONES
    # ═══════════════════════════════════════════════════════════════════════
    
    def registrar_prediccion(
        self,
        parametro: str,
        valor_predicho: float,
        metadatos: Optional[Dict] = None,
    ) -> None:
        """
        Registra una predicción para validación futura.
        
        Args:
            parametro: Nombre del parámetro (temperatura_minima, utci, etc)
            valor_predicho: Valor predicho
            metadatos: Info adicional (método usado, confianza, etc)
        """
        timestamp = time.time()
        ventana_horas = MOS_CONFIG["ventana_validacion_horas"].get(parametro, 24)
        timestamp_validacion = timestamp + (ventana_horas * 3600)
        
        prediccion = {
            "parametro": parametro,
            "timestamp_prediccion": timestamp,
            "timestamp_validacion": timestamp_validacion,
            "valor_predicho": valor_predicho,
            "metadatos": metadatos or {},
            "validado": False,
        }
        
        self.predicciones.append(prediccion)
        self._guardar_estado()
        
        logging.debug(f"MOS: Predicción registrada - {parametro}={valor_predicho:.2f}, validar en {ventana_horas}h")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2️⃣ VALIDACIÓN DE PREDICCIONES
    # ═══════════════════════════════════════════════════════════════════════
    
    def validar_predicciones_pendientes(self) -> Dict:
        """
        Valida predicciones cuyo tiempo de ventana ha pasado.
        
        Returns:
            Diccionario con resultados de validación
        """
        timestamp_actual = time.time()
        validaciones_realizadas = []
        
        for prediccion in self.predicciones:
            if prediccion["validado"]:
                continue
            
            # Verificar si ha pasado el tiempo de validación
            if timestamp_actual < prediccion["timestamp_validacion"]:
                continue
            
            # Obtener valor real del Bus
            parametro = prediccion["parametro"]
            valor_real = self._obtener_valor_real(parametro)
            
            if valor_real is None:
                logging.warning(f"MOS: No hay valor real para {parametro}, saltando validación")
                continue
            
            # Calcular error
            valor_predicho = prediccion["valor_predicho"]
            error = valor_predicho - valor_real
            error_abs = abs(error)
            
            # Registrar validación
            validacion = {
                "parametro": parametro,
                "timestamp_validacion": timestamp_actual,
                "valor_predicho": valor_predicho,
                "valor_real": valor_real,
                "error": error,
                "error_abs": error_abs,
                "metadatos": prediccion["metadatos"],
            }
            
            validaciones_realizadas.append(validacion)
            self.resultados["validaciones"].append(validacion)
            prediccion["validado"] = True
            
            logging.info(f"[OK] MOS Validación: {parametro} - Predicho={valor_predicho:.2f}, Real={valor_real:.2f}, Error={error:+.2f}")
        
        # Actualizar coeficientes si hay bias
        if validaciones_realizadas:
            self._actualizar_coeficientes(validaciones_realizadas)
            self._guardar_estado()
        
        return {
            "validaciones_realizadas": len(validaciones_realizadas),
            "validaciones": validaciones_realizadas,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3️⃣ ANÁLISIS DE BIAS Y AJUSTE
    # ═══════════════════════════════════════════════════════════════════════
    
    def _actualizar_coeficientes(self, validaciones: List[Dict]) -> None:
        """
        Actualiza coeficientes si hay bias sistemático.
        
        Args:
            validaciones: Lista de validaciones recientes
        """
        # Agrupar por parámetro
        por_parametro = {}
        for val in validaciones:
            param = val["parametro"]
            if param not in por_parametro:
                por_parametro[param] = []
            por_parametro[param].append(val)
        
        # Analizar cada parámetro
        for parametro, vals in por_parametro.items():
            if len(vals) < 3:  # Mínimo 3 validaciones para ajustar
                continue
            
            # Calcular BIAS medio
            errores = [v["error"] for v in vals]
            bias = sum(errores) / len(errores)
            mae = sum(abs(e) for e in errores) / len(errores)
            
            umbral = MOS_CONFIG["umbrales_bias"].get(parametro, 1.0)
            
            # Si BIAS > umbral → ajustar coeficiente
            if abs(bias) > umbral:
                # Factor de ajuste simple
                factor_ajuste = 1.0 - (bias / (bias + 10.0))  # Suave
                factor_ajuste = max(0.8, min(1.2, factor_ajuste))  # Límites ±20%
                
                # Actualizar coeficiente
                coef_key = self._mapear_parametro_a_coef(parametro)
                if coef_key in self.resultados["coeficientes"]:
                    coef_anterior = self.resultados["coeficientes"][coef_key]
                    coef_nuevo = coef_anterior * factor_ajuste
                    self.resultados["coeficientes"][coef_key] = coef_nuevo
                    
                    logging.warning(
                        f"[WARNING] MOS AJUSTE: {parametro} - BIAS={bias:+.2f}, "
                        f"MAE={mae:.2f}, Coef: {coef_anterior:.3f} → {coef_nuevo:.3f}"
                    )
                    
                    # Publicar al Bus si disponible
                    if self.bus:
                        self.bus.publicar(f"mos_coef_{coef_key}", coef_nuevo, "factor")
    
    def _mapear_parametro_a_coef(self, parametro: str) -> str:
        """Mapea nombre de parámetro a clave de coeficiente."""
        mapeo = {
            "temperatura_minima": "temperatura_minima",
            "utci": "utci_v2",
            "et0": "et0_wright",
            "humedad_suelo": "kalman_soil",
            "probabilidad_lluvia": "prob_lluvia",
        }
        return mapeo.get(parametro, parametro)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4️⃣ ESTADÍSTICAS Y CONFIANZA
    # ═══════════════════════════════════════════════════════════════════════
    
    def calcular_estadisticas(self, parametro: str, ultimas_n: int = 50) -> Dict:
        """
        Calcula estadísticas de un parámetro (MAE, RMSE, confianza).
        
        Args:
            parametro: Nombre del parámetro
            ultimas_n: Últimas N validaciones a considerar
        
        Returns:
            Dict con MAE, RMSE, BIAS, confianza
        """
        validaciones = [v for v in self.resultados["validaciones"] if v["parametro"] == parametro]
        validaciones = validaciones[-ultimas_n:]  # Últimas N
        
        if not validaciones:
            return {
                "n_validaciones": 0,
                "mae": None,
                "rmse": None,
                "bias": None,
                "confianza": 0.0,
            }
        
        errores = [v["error"] for v in validaciones]
        errores_abs = [abs(e) for e in errores]
        
        mae = sum(errores_abs) / len(errores_abs)
        rmse = (sum(e**2 for e in errores) / len(errores)) ** 0.5
        bias = sum(errores) / len(errores)
        
        # Confianza: 100% si MAE=0, 0% si MAE > 2*umbral
        umbral = MOS_CONFIG["umbrales_bias"].get(parametro, 1.0)
        confianza = max(0.0, min(100.0, 100.0 * (1.0 - mae / (2.0 * umbral))))
        
        return {
            "n_validaciones": len(validaciones),
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "bias": round(bias, 3),
            "confianza": round(confianza, 1),
        }
    
    def obtener_confianza_global(self) -> float:
        """Calcula confianza global del sistema (promedio ponderado)."""
        parametros = ["temperatura_minima", "utci", "et0", "humedad_suelo", "probabilidad_lluvia"]
        pesos = [0.3, 0.25, 0.2, 0.15, 0.1]  # Importancia relativa
        
        confianzas = []
        for param, peso in zip(parametros, pesos):
            stats = self.calcular_estadisticas(param)
            conf = stats.get("confianza", 0.0)
            confianzas.append(conf * peso)
        
        return round(sum(confianzas), 1)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5️⃣ PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def _cargar_estado(self) -> None:
        """Carga predicciones y resultados previos."""
        try:
            if self.registro_path.exists():
                with open(self.registro_path, "r", encoding="utf-8") as f:
                    self.predicciones = json.load(f)
                logging.info(f"MOS: {len(self.predicciones)} predicciones cargadas")
        except Exception as e:
            logging.warning(f"MOS: Error cargando predicciones: {e}")
        
        try:
            if self.resultados_path.exists():
                with open(self.resultados_path, "r", encoding="utf-8") as f:
                    self.resultados = json.load(f)
                logging.info(f"MOS: {len(self.resultados['validaciones'])} validaciones cargadas")
        except Exception as e:
            logging.warning(f"MOS: Error cargando resultados: {e}")
    
    def _guardar_estado(self) -> None:
        """Guarda predicciones y resultados."""
        try:
            self.registro_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registro_path, "w", encoding="utf-8") as f:
                json.dump(self.predicciones, f, indent=2)
            
            with open(self.resultados_path, "w", encoding="utf-8") as f:
                json.dump(self.resultados, f, indent=2)
        except Exception as e:
            logging.error(f"MOS: Error guardando estado: {e}")
    
    def _obtener_valor_real(self, parametro: str) -> Optional[float]:
        """
        Obtiene el valor real del Bus para comparación.
        
        Args:
            parametro: Nombre del parámetro
        
        Returns:
            Valor real o None si no disponible
        """
        if not self.bus:
            return None
        
        # Mapeo de parámetros a claves del Bus
        mapeo_bus = {
            "temperatura_minima": "temperatura",  # Usar temperatura actual como proxy
            "utci": "utci",
            "et0": "et0_penman",
            "humedad_suelo": "humedad_suelo_relativa",
            "probabilidad_lluvia": "lluvia_rate",  # Proxy: si lluvia_rate > 0 → llovió
        }
        
        clave_bus = mapeo_bus.get(parametro)
        if not clave_bus:
            return None
        
        try:
            valor = self.bus.leer(clave_bus)
            if valor is not None:
                return float(valor)
        except Exception as e:
            logging.warning(f"MOS: Error leyendo {clave_bus} del Bus: {e}")
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# [LAUNCH] EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    
    # Crear validador
    validator = MOSValidator()
    
    # Ejemplo: Registrar predicciones
    validator.registrar_prediccion(
        parametro="temperatura_minima",
        valor_predicho=12.5,
        metadatos={"metodo": "Deardorff V47.0 + Prata"},
    )
    
    validator.registrar_prediccion(
        parametro="utci",
        valor_predicho=18.3,
        metadatos={"metodo": "UTCI v2 Blazejczyk"},
    )
    
    # Validar predicciones (simular después de N horas)
    # En producción esto se ejecutaría periódicamente
    # resultados = validator.validar_predicciones_pendientes()
    # print(f"Validaciones realizadas: {resultados['validaciones_realizadas']}")
    
    # Estadísticas
    stats_tmin = validator.calcular_estadisticas("temperatura_minima")
    print(f"\n[STATS] Estadísticas T_min: {stats_tmin}")
    
    confianza_global = validator.obtener_confianza_global()
    print(f"\n[GUARDIAN] Confianza global del sistema: {confianza_global}%")
    
    print("\n[OK] MOS Validator V47.0 - OPERATIVO")

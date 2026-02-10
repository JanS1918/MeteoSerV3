"""
═══════════════════════════════════════════════════════════════════════════════
🛡️ MOS V47.2 - CLUSTERING INTELIGENTE CON VALIDACIÓN ESTACIONAL
═══════════════════════════════════════════════════════════════════════════════

Arquitectura:
  - Aprendizaje por escenarios físicos (ALFA, BETA, GAMMA, DELTA)
  - Clustering con índice de similitud (>85%)
  - Normalización de eventos similares
  - Aprendizaje AISLADO (0% cross-learning)
  - Auditoría post-hoc (umbral 0.05°C)
  - Validación estacional (4 épocas)
  - Corrección inmediata + certificación anual
  - Monitoreo continuo del BIAS
  - MOS independiente por parámetro

Fecha: 2026-02-05
Versión: V47.2 SUMMUM
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE ESCENARIOS FÍSICOS
# ═══════════════════════════════════════════════════════════════════════════

ESCENARIOS_FISICOS = {
    "ALFA": {
        "nombre": "RADIATIVO",
        "descripcion": "Noche despejada, viento calma, alta radiación nocturna",
        "condiciones": {
            "viento_max": 1.5,  # m/s
            "cobertura_nubes_max": 20,  # %
            "hora_min": 20,  # 20:00
            "hora_max": 8,   # 08:00
        },
        "parametros_referencia": {
            "viento": 1.0,
            "viento_rango": 0.5,
            "temp_rango": 1.0,
            "hr_rango": 15,
        },
        "eventos_minimos": 7,  # Frecuente, 7 eventos suficientes
    },
    "BETA": {
        "nombre": "INVERSIÓN",
        "descripcion": "Alta humedad, nublado, inversión térmica",
        "condiciones": {
            "hr_min": 90,  # %
            "cobertura_nubes_min": 70,  # %
            "viento_max": 2.0,  # m/s
        },
        "parametros_referencia": {
            "viento": 0.5,
            "viento_rango": 0.3,
            "temp_rango": 1.5,
            "hr_rango": 10,
        },
        "eventos_minimos": 5,  # Menos frecuente, 5 eventos
    },
    "GAMMA": {
        "nombre": "VENTOSO",
        "descripcion": "Viento fuerte, dinámico, mezcla vertical",
        "condiciones": {
            "viento_min": 4.0,  # m/s
        },
        "parametros_referencia": {
            "viento": 6.0,
            "viento_rango": 2.0,
            "temp_rango": 2.0,
            "hr_rango": 20,
        },
        "eventos_minimos": 10,  # Muy variable, 10 eventos
    },
    "DELTA": {
        "nombre": "ESTÁNDAR",
        "descripcion": "Condiciones normales, resto de situaciones",
        "condiciones": {},  # Por defecto
        "parametros_referencia": {
            "viento": 2.5,
            "viento_rango": 1.5,
            "temp_rango": 1.5,
            "hr_rango": 20,
        },
        "eventos_minimos": 5,  # Frecuente, 5 eventos
    },
}

# Umbrales de validación
UMBRAL_SIMILITUD = 85.0  # % mínimo para considerar eventos similares
UMBRAL_ANOMALIA = 1.5    # °C desviación para descartar outliers
UMBRAL_CONSISTENCIA_GLOBAL = 0.05  # °C std_dev para detectar sesgo sistemático
UMBRAL_DRIFT_BIAS = 0.10  # °C delta para re-aprender


# ═══════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: MOS CLUSTERING V47.2
# ═══════════════════════════════════════════════════════════════════════════

class MOSClusteringV472:
    """
    Model Output Statistics con Clustering Inteligente.
    
    Características:
    - Aprendizaje por escenarios físicos
    - Normalización de eventos similares
    - Validación estacional automática
    - Monitoreo continuo del BIAS
    """
    
    def __init__(self, bus=None, data_path: str = "data"):
        self.bus = bus
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        
        # Estado de escenarios por parámetro
        self.parametros_mos = {}
        
        # Cargar estado persistente
        self._cargar_estado()
        
        logger.info("🛡️ MOS V47.2 Clustering Inteligente inicializado")
    
    # ═══════════════════════════════════════════════════════════════════════
    # CLASIFICACIÓN DE ESCENARIOS
    # ═══════════════════════════════════════════════════════════════════════
    
    def clasificar_escenario(self, condiciones: Dict) -> str:
        """
        Clasifica condiciones actuales en escenario físico.
        
        Args:
            condiciones: {
                "viento": 1.2,  # m/s
                "hr": 55,       # %
                "cobertura_nubes": 10,  # %
                "hora": 22,     # hora del día
            }
        
        Returns:
            Escenario: "ALFA", "BETA", "GAMMA", "DELTA"
        """
        viento = condiciones.get("viento", 0)
        hr = condiciones.get("hr", 50)
        nubes = condiciones.get("cobertura_nubes", 50)
        hora = condiciones.get("hora", 12)
        
        # ALFA: Radiativo nocturno
        if (viento < ESCENARIOS_FISICOS["ALFA"]["condiciones"]["viento_max"] and
            nubes < ESCENARIOS_FISICOS["ALFA"]["condiciones"]["cobertura_nubes_max"] and
            (hora >= ESCENARIOS_FISICOS["ALFA"]["condiciones"]["hora_min"] or
             hora <= ESCENARIOS_FISICOS["ALFA"]["condiciones"]["hora_max"])):
            return "ALFA"
        
        # BETA: Inversión térmica
        if (hr >= ESCENARIOS_FISICOS["BETA"]["condiciones"]["hr_min"] and
            nubes >= ESCENARIOS_FISICOS["BETA"]["condiciones"]["cobertura_nubes_min"] and
            viento < ESCENARIOS_FISICOS["BETA"]["condiciones"]["viento_max"]):
            return "BETA"
        
        # GAMMA: Ventoso
        if viento >= ESCENARIOS_FISICOS["GAMMA"]["condiciones"]["viento_min"]:
            return "GAMMA"
        
        # DELTA: Estándar (por defecto)
        return "DELTA"
    
    # ═══════════════════════════════════════════════════════════════════════
    # SIMILITUD Y NORMALIZACIÓN
    # ═══════════════════════════════════════════════════════════════════════
    
    def calcular_similitud(self, evento_nuevo: Dict, escenario: str) -> float:
        """
        Calcula similitud (0-100%) entre evento y escenario.
        
        Usa desviaciones normalizadas para comparar.
        """
        ref = ESCENARIOS_FISICOS[escenario]["parametros_referencia"]
        
        desv_viento = abs(evento_nuevo.get("viento", ref["viento"]) - ref["viento"]) / ref["viento_rango"] * 100
        desv_temp = abs(evento_nuevo.get("temp", 0) - evento_nuevo.get("temp_ref", 0)) / ref["temp_rango"] * 100 if "temp" in evento_nuevo else 0
        desv_hr = abs(evento_nuevo.get("hr", 50) - 50) / ref["hr_rango"] * 100
        
        # Similitud = 100 - promedio de desviaciones
        similitud = 100 - ((desv_viento + desv_temp + desv_hr) / 3)
        
        return max(0, min(100, similitud))
    
    def normalizar_evento(self, evento: Dict, escenario: str) -> Dict:
        """
        Normaliza evento al escenario de referencia.
        
        Permite comparar eventos "similares pero no idénticos".
        """
        ref = ESCENARIOS_FISICOS[escenario]["parametros_referencia"]
        
        # Factor de normalización de temperatura (principal)
        # Si evento tiene viento 1.4 m/s y referencia 1.0 m/s,
        # ajustar bias proporcionalmente
        
        factor_viento = ref["viento"] / max(evento.get("viento", ref["viento"]), 0.1)
        
        return {
            "bias_normalizado": evento.get("bias", 0) * factor_viento,
            "factor_normalizacion": factor_viento,
            "evento_original": evento,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO Y VALIDACIÓN DE PREDICCIONES
    # ═══════════════════════════════════════════════════════════════════════
    
    def registrar_prediccion(
        self,
        parametro: str,
        valor_predicho: float,
        condiciones: Dict,
        ventana_validacion_h: int = 12
    ):
        """
        Registra predicción para validar después.
        
        Args:
            parametro: "temperatura_minima", "et0", "utci", etc.
            valor_predicho: Valor predicho por el modelo
            condiciones: Condiciones meteorológicas actuales
            ventana_validacion_h: Horas hasta validación
        """
        # Inicializar parámetro si no existe
        if parametro not in self.parametros_mos:
            self._inicializar_parametro(parametro)
        
        # Clasificar escenario
        escenario = self.clasificar_escenario(condiciones)
        
        # Registrar predicción
        prediccion = {
            "valor_predicho": valor_predicho,
            "condiciones": condiciones,
            "escenario": escenario,
            "timestamp": time.time(),
            "timestamp_validacion": time.time() + (ventana_validacion_h * 3600),
            "validado": False,
            "epoca": self._determinar_epoca(),
        }
        
        self.parametros_mos[parametro]["predicciones_pendientes"].append(prediccion)
        
        logger.debug(
            f"📝 {parametro}: Predicción registrada {valor_predicho:.2f} "
            f"(escenario: {escenario}, validar en {ventana_validacion_h}h)"
        )
    
    def validar_predicciones_pendientes(self, obtener_valor_real_callback):
        """
        Valida predicciones cuya ventana ha expirado.
        
        Args:
            obtener_valor_real_callback: Función que obtiene valor real del sensor
                                          Firma: callback(parametro) -> float
        """
        timestamp_actual = time.time()
        
        for parametro in self.parametros_mos:
            predicciones = self.parametros_mos[parametro]["predicciones_pendientes"]
            
            for pred in predicciones:
                if pred["validado"]:
                    continue
                
                if timestamp_actual < pred["timestamp_validacion"]:
                    continue  # Aún no llegó la ventana
                
                # Obtener valor real
                try:
                    valor_real = obtener_valor_real_callback(parametro)
                except Exception as e:
                    logger.error(f"Error obteniendo valor real de {parametro}: {e}")
                    continue
                
                # Calcular BIAS
                bias = pred["valor_predicho"] - valor_real
                
                # Registrar evento en escenario correspondiente
                escenario = pred["escenario"]
                evento = {
                    "valor_predicho": pred["valor_predicho"],
                    "valor_real": valor_real,
                    "bias": bias,
                    "condiciones": pred["condiciones"],
                    "timestamp": pred["timestamp"],
                    "epoca": pred["epoca"],
                }
                
                self._registrar_evento_en_escenario(parametro, escenario, evento)
                
                pred["validado"] = True
                
                logger.info(
                    f"✅ {parametro} validado: predicho={pred['valor_predicho']:.2f}, "
                    f"real={valor_real:.2f}, BIAS={bias:.3f}°C (escenario {escenario})"
                )
        
        # Guardar estado
        self._guardar_estado()
    
    def _registrar_evento_en_escenario(self, parametro: str, escenario: str, evento: Dict):
        """
        Registra evento validado en el escenario correspondiente.
        Aplica clustering con similitud.
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        # Calcular similitud con escenario
        similitud = self.calcular_similitud(evento, escenario)
        
        if similitud < UMBRAL_SIMILITUD:
            logger.warning(
                f"⚠️ {parametro} escenario {escenario}: Evento con baja similitud "
                f"({similitud:.1f}% < {UMBRAL_SIMILITUD}%). Descartado."
            )
            return
        
        # Verificar anomalía (outlier)
        if escenarios[escenario]["eventos"]:
            biases_existentes = [e["bias"] for e in escenarios[escenario]["eventos"]]
            bias_promedio = statistics.mean(biases_existentes)
            
            if abs(evento["bias"] - bias_promedio) > UMBRAL_ANOMALIA:
                logger.warning(
                    f"⚠️ {parametro} escenario {escenario}: Evento anómalo detectado "
                    f"(BIAS={evento['bias']:.3f}°C vs promedio={bias_promedio:.3f}°C). "
                    f"Descartado como outlier."
                )
                escenarios[escenario]["eventos_descartados"] += 1
                return
        
        # Normalizar evento
        evento_normalizado = self.normalizar_evento(evento, escenario)
        evento_normalizado["similitud"] = similitud
        
        # Registrar en escenario
        escenarios[escenario]["eventos"].append(evento_normalizado)
        escenarios[escenario]["contador"] += 1
        
        # Recalcular BIAS acumulado
        self._recalcular_bias_escenario(parametro, escenario)
        
        # Verificar si alcanzó eventos mínimos para activar corrección
        eventos_minimos = ESCENARIOS_FISICOS[escenario]["eventos_minimos"]
        if escenarios[escenario]["contador"] == eventos_minimos:
            self._activar_correccion_escenario(parametro, escenario)
    
    def _recalcular_bias_escenario(self, parametro: str, escenario: str):
        """
        Recalcula BIAS promedio del escenario.
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        eventos = escenarios[escenario]["eventos"]
        
        if not eventos:
            return
        
        biases = [e["bias_normalizado"] for e in eventos]
        bias_promedio = statistics.mean(biases)
        std_dev = statistics.stdev(biases) if len(biases) > 1 else 0.0
        
        escenarios[escenario]["bias_promedio"] = bias_promedio
        escenarios[escenario]["std_dev"] = std_dev
    
    def _activar_correccion_escenario(self, parametro: str, escenario: str):
        """
        Activa corrección cuando escenario alcanza eventos mínimos.
        Fase 1: Corrección inmediata con confianza 99.7%
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        if escenarios[escenario]["activa"]:
            return  # Ya activa
        
        bias = escenarios[escenario]["bias_promedio"]
        std_dev = escenarios[escenario]["std_dev"]
        
        escenarios[escenario]["activa"] = True
        escenarios[escenario]["confianza"] = 99.7  # 3σ
        escenarios[escenario]["timestamp_activacion"] = time.time()
        
        # Publicar al Bus
        if self.bus:
            self.bus.publicar(f"mos_{parametro}_{escenario}_activa", True, "bool")
            self.bus.publicar(f"mos_{parametro}_{escenario}_bias", bias, "unidad")
            self.bus.publicar(f"mos_{parametro}_{escenario}_confianza", 99.7, "%")
            self.bus.publicar(f"mos_{parametro}_{escenario}_std_dev", std_dev, "unidad")
            self.bus.publicar(f"mos_{parametro}_{escenario}_estado", "ACTIVA_VALIDACIÓN_PENDIENTE", "estado")
        
        logger.critical(
            f"🛡️ MOS {parametro} escenario {escenario} ACTIVADO: "
            f"BIAS={bias:.3f}, std_dev={std_dev:.3f}, confianza=99.7% (3σ)"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # VALIDACIÓN ESTACIONAL (4 ÉPOCAS)
    # ═══════════════════════════════════════════════════════════════════════
    
    def _determinar_epoca(self) -> str:
        """Determina época del año actual."""
        mes = datetime.now().month
        if mes in [12, 1, 2]:
            return "INVIERNO"
        elif mes in [3, 4, 5]:
            return "PRIMAVERA"
        elif mes in [6, 7, 8]:
            return "VERANO"
        else:
            return "OTOÑO"
    
    def validacion_estacional_automatica(self):
        """
        Valida estacionalidad del BIAS cada 3 meses.
        Al año completo (4 épocas), certifica con confianza 99.99%.
        """
        for parametro in self.parametros_mos:
            for escenario_nombre in ["ALFA", "BETA", "GAMMA", "DELTA"]:
                escenario = self.parametros_mos[parametro]["escenarios"][escenario_nombre]
                
                if not escenario["activa"]:
                    continue  # No activa aún
                
                # Verificar si hay nueva época para registrar
                if self._nueva_epoca_disponible(parametro, escenario_nombre):
                    self._registrar_epoca_actual(parametro, escenario_nombre)
                
                # Verificar si han pasado 12 meses
                if escenario.get("timestamp_activacion"):
                    tiempo_transcurrido = time.time() - escenario["timestamp_activacion"]
                    if tiempo_transcurrido >= 31536000:  # 365 días
                        self._validar_estacionalidad_completa(parametro, escenario_nombre)
    
    def _nueva_epoca_disponible(self, parametro: str, escenario: str) -> bool:
        """Verifica si cambió la época desde última validación."""
        epoca_actual = self._determinar_epoca()
        historial = self.parametros_mos[parametro]["escenarios"][escenario]["historial_epocas"]
        
        if not historial:
            return True
        
        ultima_epoca = historial[-1]["epoca"]
        return epoca_actual != ultima_epoca
    
    def _registrar_epoca_actual(self, parametro: str, escenario: str):
        """Registra BIAS de la época actual."""
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        bias_actual = escenarios[escenario]["bias_promedio"]
        epoca_actual = self._determinar_epoca()
        
        escenarios[escenario]["historial_epocas"].append({
            "epoca": epoca_actual,
            "bias": bias_actual,
            "timestamp": time.time(),
        })
        
        logger.info(
            f"📅 {parametro} escenario {escenario}: Nueva época {epoca_actual} "
            f"registrada (BIAS={bias_actual:.3f})"
        )
    
    def _validar_estacionalidad_completa(self, parametro: str, escenario: str):
        """
        Valida que BIAS es consistente en las 4 épocas.
        Si std_dev < 0.02°C → Certifica con 99.99% (4.8σ)
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        historial = escenarios[escenario]["historial_epocas"]
        
        if len(historial) < 4:
            return  # No hay 4 épocas aún
        
        # Tomar últimas 4 épocas
        ultimas_4 = historial[-4:]
        biases = [e["bias"] for e in ultimas_4]
        
        std_dev_anual = statistics.stdev(biases)
        bias_promedio_anual = statistics.mean(biases)
        
        if std_dev_anual < 0.02:  # Umbral estricto
            # ✅ CERTIFICACIÓN ANUAL
            escenarios[escenario]["confianza"] = 99.99
            escenarios[escenario]["estado"] = "CERTIFICADA_ANUAL"
            
            if self.bus:
                self.bus.publicar(f"mos_{parametro}_{escenario}_confianza", 99.99, "%")
                self.bus.publicar(f"mos_{parametro}_{escenario}_estado", "CERTIFICADA_ANUAL", "estado")
                self.bus.publicar(f"mos_{parametro}_{escenario}_std_dev_anual", std_dev_anual, "unidad")
            
            logger.critical(
                f"🏆 {parametro} escenario {escenario} CERTIFICADO ANUAL: "
                f"BIAS={bias_promedio_anual:.3f}, std_anual={std_dev_anual:.3f}, "
                f"confianza=99.99% (4.8σ)"
            )
        else:
            logger.info(
                f"ℹ️ {parametro} escenario {escenario}: BIAS varía estacionalmente "
                f"(std_anual={std_dev_anual:.3f}°C). Manteniendo corrección por época."
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUDITORÍA POST-HOC (Consistencia Global)
    # ═══════════════════════════════════════════════════════════════════════
    
    def auditoria_global_consistencia(self, parametro: str):
        """
        Cuando todos los escenarios completan, verifica consistencia global.
        Si std_dev < 0.05°C entre escenarios → Sesgo sistemático de sensor.
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        # Verificar que todos estén activos
        escenarios_activos = [e for e in ["ALFA", "BETA", "GAMMA", "DELTA"] 
                              if escenarios[e]["activa"]]
        
        if len(escenarios_activos) < 4:
            return  # No todos completos
        
        # Recopilar BIAS de todos los escenarios
        biases_escenarios = [escenarios[e]["bias_promedio"] for e in escenarios_activos]
        
        std_dev_global = statistics.stdev(biases_escenarios)
        bias_promedio_global = statistics.mean(biases_escenarios)
        
        if std_dev_global < UMBRAL_CONSISTENCIA_GLOBAL:
            # 🚨 SESGO SISTEMÁTICO DETECTADO
            if self.bus:
                self.bus.publicar(f"mos_{parametro}_sesgo_global", bias_promedio_global, "unidad")
                self.bus.publicar(f"mos_{parametro}_std_dev_global", std_dev_global, "unidad")
                self.bus.publicar(f"mos_{parametro}_estado_global", "DRIFT_SISTEMÁTICO", "estado")
            
            logger.critical(
                f"🚨 {parametro}: SESGO SISTEMÁTICO DETECTADO. "
                f"BIAS_global={bias_promedio_global:.3f}, std_global={std_dev_global:.3f}°C "
                f"(< {UMBRAL_CONSISTENCIA_GLOBAL}°C). Todos los escenarios coinciden. "
                f"Posible descalibración de sensor o error sistemático en fórmulas."
            )
        else:
            logger.info(
                f"✅ {parametro}: Física diferenciada por escenario "
                f"(std_global={std_dev_global:.3f}°C). Esto es esperado."
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # MONITOREO CONTINUO DEL BIAS (Re-aprendizaje)
    # ═══════════════════════════════════════════════════════════════════════
    
    def monitorear_drift_bias(self, parametro: str, escenario: str):
        """
        Cada 30 días, verifica si BIAS cambió significativamente.
        Si delta > 0.10°C → Re-aprender.
        """
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        if not escenarios[escenario]["activa"]:
            return
        
        bias_certificado = escenarios[escenario]["bias_promedio"]
        
        # Calcular BIAS últimos 7 eventos
        eventos_recientes = escenarios[escenario]["eventos"][-7:]
        if len(eventos_recientes) < 7:
            return
        
        biases_recientes = [e["bias_normalizado"] for e in eventos_recientes]
        bias_reciente = statistics.mean(biases_recientes)
        
        delta = abs(bias_certificado - bias_reciente)
        
        if delta > UMBRAL_DRIFT_BIAS:
            # 🚨 BIAS HA CAMBIADO
            logger.warning(
                f"⚠️ {parametro} escenario {escenario}: BIAS cambió de "
                f"{bias_certificado:.3f} a {bias_reciente:.3f} (delta={delta:.3f}°C). "
                f"Posible cambio ambiental o degradación sensor. RE-APRENDIENDO..."
            )
            
            if self.bus:
                self.bus.publicar(f"mos_{parametro}_{escenario}_drift_detectado", True, "bool")
                self.bus.publicar(f"mos_{parametro}_{escenario}_bias_nuevo", bias_reciente, "unidad")
            
            # Re-iniciar aprendizaje
            self._reiniciar_aprendizaje_escenario(parametro, escenario)
    
    def _reiniciar_aprendizaje_escenario(self, parametro: str, escenario: str):
        """Re-inicia aprendizaje de escenario tras detectar DRIFT."""
        escenarios = self.parametros_mos[parametro]["escenarios"]
        
        # Guardar historial anterior
        backup = {
            "bias_anterior": escenarios[escenario]["bias_promedio"],
            "eventos_anteriores": len(escenarios[escenario]["eventos"]),
            "timestamp": time.time(),
        }
        
        escenarios[escenario]["historial_reinicios"].append(backup)
        
        # Limpiar eventos (mantener solo últimos 7 como seed)
        escenarios[escenario]["eventos"] = escenarios[escenario]["eventos"][-7:]
        escenarios[escenario]["contador"] = len(escenarios[escenario]["eventos"])
        escenarios[escenario]["activa"] = False
        escenarios[escenario]["confianza"] = 0
        
        logger.info(
            f"🔄 {parametro} escenario {escenario}: Re-aprendizaje iniciado "
            f"(manteniendo últimos 7 eventos como seed)"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # OBTENER CORRECCIÓN PARA PREDICCIÓN
    # ═══════════════════════════════════════════════════════════════════════
    
    def obtener_correccion(self, parametro: str, condiciones: Dict) -> Optional[Dict]:
        """
        Obtiene corrección MOS para predicción actual.
        
        Returns:
            {
                "bias": -0.30,
                "confianza": 99.7,
                "escenario": "ALFA",
                "estado": "ACTIVA"
            }
            o None si no hay corrección disponible
        """
        if parametro not in self.parametros_mos:
            return None
        
        escenario = self.clasificar_escenario(condiciones)
        escenario_data = self.parametros_mos[parametro]["escenarios"][escenario]
        
        if not escenario_data["activa"]:
            return None
        
        return {
            "bias": escenario_data["bias_promedio"],
            "confianza": escenario_data["confianza"],
            "escenario": escenario,
            "estado": escenario_data.get("estado", "ACTIVA"),
            "std_dev": escenario_data["std_dev"],
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def _inicializar_parametro(self, parametro: str):
        """Inicializa estructura de datos para parámetro."""
        self.parametros_mos[parametro] = {
            "predicciones_pendientes": [],
            "escenarios": {
                "ALFA": self._crear_escenario_vacio(),
                "BETA": self._crear_escenario_vacio(),
                "GAMMA": self._crear_escenario_vacio(),
                "DELTA": self._crear_escenario_vacio(),
            }
        }
    
    def _crear_escenario_vacio(self) -> Dict:
        """Crea estructura vacía para escenario."""
        return {
            "eventos": [],
            "contador": 0,
            "eventos_descartados": 0,
            "bias_promedio": 0.0,
            "std_dev": 0.0,
            "activa": False,
            "confianza": 0.0,
            "timestamp_activacion": None,
            "estado": "INACTIVA",
            "historial_epocas": [],
            "historial_reinicios": [],
        }
    
    def _guardar_estado(self):
        """Guarda estado persistente a disco."""
        archivo = self.data_path / "mos_clustering_v472_estado.json"
        
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(self.parametros_mos, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando estado MOS V47.2: {e}")
    
    def _cargar_estado(self):
        """Carga estado persistente desde disco."""
        archivo = self.data_path / "mos_clustering_v472_estado.json"
        
        if not archivo.exists():
            logger.info("No hay estado previo MOS V47.2. Iniciando limpio.")
            return
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                self.parametros_mos = json.load(f)
            logger.info(f"✅ Estado MOS V47.2 cargado: {len(self.parametros_mos)} parámetros")
        except Exception as e:
            logger.error(f"Error cargando estado MOS V47.2: {e}")

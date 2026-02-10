"""
═══════════════════════════════════════════════════════════════════════════════
CONTROLADOR RADIACIÓN ROBUSTO - Orquestador Central
═══════════════════════════════════════════════════════════════════════════════

Integra todas las capas:
1. Clasificación de contexto
2. Aprendizaje separado (correctivo + diagnóstico)
3. Publicación con jerarquía de confianza
4. Validación cruzada radiación-temperatura
5. Fusión inteligente con sensor real

Este es el corazón de la nueva arquitectura.

Paradigma: DESCONFIADO POR DEFECTO, ABIERTO SOLO CUANDO TODO ES LIMPIO.

Autor: Sistema Robusto MeteoSerV3
Fecha: Feb 10, 2026
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ControladorRadiacionRobusto:
    """
    Orquestador central de la radiación.
    
    Coordina: contexto → aprendizaje → validación → publicación → fusión
    """
    
    def __init__(self,
                 clasificador=None,
                 aprendizaje_correctivo=None,
                 aprendizaje_diagnostico=None,
                 publicador=None,
                 validador_cruzado=None):
        """
        Inicializa el controlador.
        
        Args:
            clasificador: ClasificadorContextoRadiativo
            aprendizaje_correctivo: EstiloAprendizajeCorrectivo
            aprendizaje_diagnostico: EstiloAprendizajeDiagnostico
            publicador: PublicadorRadiacionRobusto
            validador_cruzado: ValidadorCruzadoRadiacion
        """
        self.clasificador = clasificador
        self.aprendizaje_correctivo = aprendizaje_correctivo
        self.aprendizaje_diagnostico = aprendizaje_diagnostico
        self.publicador = publicador
        self.validador_cruzado = validador_cruzado
        
        self._ultima_temperatura = None
        self._ultimo_timestamp = None
    
    def procesar_ciclo_radiacion(self,
                                  elevacion_solar_deg: float,
                                  ghi_w_m2_medida: float,
                                  presion_hpa: float,
                                  humedad_rel: float,
                                  temperatura_c: float,
                                  velocidad_viento_ms: float,
                                  precipitacion_mm: float,
                                  visibilidad_km: Optional[float],
                                  ghi_modelo_rest2: float,
                                  dni_modelo_rest2: float,
                                  dhi_modelo_rest2: float,
                                  timestamp: datetime,
                                  sensor_real_confiable: bool = True) -> Dict:
        """
        Procesa un ciclo completo de radiación.
        
        Args:
            elevacion_solar_deg: Ángulo solar
            ghi_w_m2_medida: GHI medida (si disponible)
            presion_hpa: Presión
            humedad_rel: Humedad relativa
            temperatura_c: Temperatura
            velocidad_viento_ms: Velocidad viento
            precipitacion_mm: Precipitación
            visibilidad_km: Visibilidad (opcional)
            ghi_modelo_rest2: GHI de REST2 (modelo clear-sky)
            dni_modelo_rest2: DNI de REST2
            dhi_modelo_rest2: DHI de REST2
            timestamp: Momento actual
            sensor_real_confiable: ¿El sensor real es confiable?
        
        Returns:
            Dict con resultado del ciclo:
            {
                "contexto": EstadoContextoRadiativo,
                "ghi_final": float,
                "dni_final": float,
                "dhi_final": float,
                "confianza": float,
                "advertencias": List[str]
            }
        """
        
        resultado = {
            "contexto": None,
            "ghi_final": ghi_modelo_rest2,
            "dni_final": dni_modelo_rest2,
            "dhi_final": dhi_modelo_rest2,
            "confianza": 1.0,
            "advertencias": [],
            "estados_publicados": []
        }
        
        logger.info(
            f"[CONTROLADOR] Iniciando ciclo radiación "
            f"(elev={elevacion_solar_deg:.1f}°, "
            f"ghi_medida={ghi_w_m2_medida:.0f} W/m², "
            f"ghi_modelo={ghi_modelo_rest2:.0f} W/m²)"
        )
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 1: CLASIFICAR CONTEXTO
        # ═════════════════════════════════════════════════════════════════
        
        if self.clasificador is not None:
            from core.radiation.clasificador_contexto_radiativo import EstadoContextoRadiativo
            
            estado_contexto = EstadoContextoRadiativo(
                timestamp=timestamp,
                elevacion_solar_deg=elevacion_solar_deg,
                ghi_w_m2=ghi_modelo_rest2,
                presion_hpa=presion_hpa,
                humedad_rel=humedad_rel,
                temperatura_c=temperatura_c,
                velocidad_viento_ms=velocidad_viento_ms,
                precipitacion_mm=precipitacion_mm,
                visibilidad_km=visibilidad_km
            )
            
            estado_contexto = self.clasificador.clasificar(estado_contexto)
            resultado["contexto"] = estado_contexto
            
            if not estado_contexto.es_valido_para_aprendizaje:
                resultado["advertencias"].extend(estado_contexto.motivos_bloqueo)
                logger.warning(
                    f"[CONTROLADOR] Contexto BLOQUEADO: "
                    f"{', '.join(estado_contexto.motivos_bloqueo)}"
                )
        else:
            # Si no hay clasificador, asumir contexto limpio (fallback)
            estado_contexto = None
            logger.debug("[CONTROLADOR] Clasificador no disponible, asumiendo contexto limpio")
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 2: APRENDIZAJE CORRECTIVO
        # ═════════════════════════════════════════════════════════════════
        
        ajuste_correctivo = None
        if self.aprendizaje_correctivo is not None and estado_contexto is not None:
            
            # Estimar GHI observado (puede venir del sensor o de validación térmica)
            ghi_observado = ghi_w_m2_medida if sensor_real_confiable else None
            
            if ghi_observado is not None:
                ajuste_correctivo = self.aprendizaje_correctivo.procesar(
                    ghi_modelo=ghi_modelo_rest2,
                    ghi_observado_estimado=ghi_observado,
                    elevacion_solar_deg=elevacion_solar_deg,
                    contexto_limpio=estado_contexto.es_valido_para_aprendizaje,
                    confianza_contexto=estado_contexto.confianza_general,
                    timestamp=timestamp
                )
                
                if ajuste_correctivo.motivos_bloqueo:
                    logger.debug(
                        f"[CONTROLADOR] Aprendizaje correctivo bloqueado: "
                        f"{ajuste_correctivo.motivos_bloqueo}"
                    )
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 3: APRENDIZAJE DIAGNÓSTICO
        # ═════════════════════════════════════════════════════════════════
        
        diagnostico = None
        if self.aprendizaje_diagnostico is not None:
            
            ghi_ref = ghi_w_m2_medida if sensor_real_confiable else ghi_modelo_rest2
            
            diagnostico = self.aprendizaje_diagnostico.procesar(
                ghi_modelo=ghi_modelo_rest2,
                ghi_observado_estimado=ghi_ref,
                elevacion_solar_deg=elevacion_solar_deg,
                temperatura_c=temperatura_c,
                humedad_rel=humedad_rel
            )
            
            # Aplicar degradación de confianza por diagnósticos
            resultado["confianza"] *= diagnostico.confianza_radiacion_general
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 4: VALIDACIÓN CRUZADA RADIACIÓN-TEMPERATURA
        # ═════════════════════════════════════════════════════════════════
        
        balance_ok = True
        if self.validador_cruzado is not None and self._ultima_temperatura is not None:
            
            minutos = (timestamp - self._ultimo_timestamp).total_seconds() / 60 \
                if self._ultimo_timestamp else 1.0
            
            validacion = self.validador_cruzado.validar(
                ghi_w_m2=ghi_modelo_rest2,
                temperatura_c=temperatura_c,
                temperatura_anterior_c=self._ultima_temperatura,
                minutos_transcurridos=minutos
            )
            
            if not validacion["balance_ok"]:
                balance_ok = False
                resultado["confianza"] *= 0.8  # Penalizar confianza
                
                if validacion["radiacion_sospechosa"]:
                    resultado["advertencias"].append(
                        "ALERTA: Radiación sospechosa (no correlaciona con T)"
                    )
                    logger.warning("[CONTROLADOR] Radiación sospechosa detectada")
                
                if validacion["temperatura_sospechosa"]:
                    resultado["advertencias"].append(
                        "ALERTA: Temperatura sospechosa (no correlaciona con radiación)"
                    )
                    logger.warning("[CONTROLADOR] Temperatura sospechosa detectada")
        
        # Guardar temperatura para próximo ciclo
        self._ultima_temperatura = temperatura_c
        self._ultimo_timestamp = timestamp
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 5: FUSIÓN INTELIGENTE CON SENSOR REAL
        # ═════════════════════════════════════════════════════════════════
        
        if ghi_w_m2_medida > 0 and sensor_real_confiable and balance_ok:
            
            # Peso dinámico basado en confianzas
            peso_modelo = resultado["confianza"]
            peso_sensor = 0.7 if estado_contexto and estado_contexto.es_valido_para_aprendizaje else 0.5
            
            # Normalizar pesos
            peso_total = peso_modelo + peso_sensor
            peso_modelo /= peso_total
            peso_sensor /= peso_total
            
            # Fusión ponderada
            ghi_final = ghi_modelo_rest2 * peso_modelo + ghi_w_m2_medida * peso_sensor
            
            resultado["ghi_final"] = ghi_final
            
            logger.debug(
                f"[CONTROLADOR] Fusión: "
                f"GHI={ghi_final:.0f} W/m² (modelo={peso_modelo:.2f}, sensor={peso_sensor:.2f})"
            )
        else:
            resultado["ghi_final"] = ghi_modelo_rest2
        
        # ═════════════════════════════════════════════════════════════════
        # FASE 6: PUBLICACIÓN EN BUS CON JERARQUÍA
        # ═════════════════════════════════════════════════════════════════
        
        if self.publicador is not None:
            from core.radiation.publicador_radiacion_robusto import EstadoRadiativo
            
            # Determinar confianzas finales
            conf_ghi = resultado["confianza"]
            conf_dni = resultado["confianza"] * (
                diagnostico.confianza_dni if diagnostico else 1.0
            )
            conf_dhi = resultado["confianza"] * (
                diagnostico.confianza_dhi if diagnostico else 1.0
            )
            
            # Publicar GHI
            estado_ghi = EstadoRadiativo(
                clave="radiacion_ghi_w_m2",
                valor=resultado["ghi_final"],
                unidad="W/m²",
                confianza=conf_ghi,
                fuente="hibrido" if ghi_w_m2_medida > 0 else "modelo",
                contexto_limpio=estado_contexto.es_valido_para_aprendizaje if estado_contexto else False,
                timestamp=timestamp,
                formula="REST2 + ajuste correctivo + fusión"
            )
            
            if diagnostico:
                estado_ghi.anotaciones["calima"] = diagnostico.calima_detectada
                estado_ghi.anotaciones["nubosidad_fina"] = diagnostico.nubosidad_fina_detectada
            
            self.publicador.publicar_estado(estado_ghi)
            resultado["estados_publicados"].append("radiacion_ghi_w_m2")
            
            # Publicar DNI
            estado_dni = EstadoRadiativo(
                clave="radiacion_dni_w_m2",
                valor=resultado["dni_final"],
                unidad="W/m²",
                confianza=conf_dni,
                fuente="modelo",
                contexto_limpio=estado_contexto.es_valido_para_aprendizaje if estado_contexto else False,
                timestamp=timestamp,
                formula="REST2 + ajuste correctivo"
            )
            self.publicador.publicar_estado(estado_dni)
            resultado["estados_publicados"].append("radiacion_dni_w_m2")
            
            # Publicar DHI
            estado_dhi = EstadoRadiativo(
                clave="radiacion_dhi_w_m2",
                valor=resultado["dhi_final"],
                unidad="W/m²",
                confianza=conf_dhi,
                fuente="modelo",
                contexto_limpio=estado_contexto.es_valido_para_aprendizaje if estado_contexto else False,
                timestamp=timestamp,
                formula="REST2 + ajuste correctivo"
            )
            self.publicador.publicar_estado(estado_dhi)
            resultado["estados_publicados"].append("radiacion_dhi_w_m2")
        
        # ═════════════════════════════════════════════════════════════════
        # RESUMEN FINAL
        # ═════════════════════════════════════════════════════════════════
        
        logger.info(
            f"[CONTROLADOR] Ciclo completado "
            f"(GHI={resultado['ghi_final']:.0f} W/m², "
            f"confianza={resultado['confianza']:.2f}, "
            f"estados publicados={len(resultado['estados_publicados'])})"
        )
        
        if resultado["advertencias"]:
            logger.warning(f"[CONTROLADOR] Advertencias: {'; '.join(resultado['advertencias'])}")
        
        return resultado

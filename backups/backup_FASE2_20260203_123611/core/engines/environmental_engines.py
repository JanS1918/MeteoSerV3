import logging
"""
Motores ambientales principales de MeteoSer.

Incluye:
- MotorAmbiental
- MotorConfort
- MotorEdificio
- MotorMeteorologico
- MotorVentilacion
- MotorPrediccionLocal
- GestorHuellasAtmosfericas / PerfilAtmosfericoPersona

Todos trabajan sobre un `contexto` unificado proporcionado por ApiEngine/ContextEngine.
"""

from typing import Dict, Any, List, Optional
from core.indices.environmental_indices import (
    evaluar_indices_ambientales,
    indice_riesgo_moho,
    indice_riesgo_condensacion_ventanas,
    indice_riesgo_helada_local,
    indice_riesgo_micro_lluvias,
    indice_estabilidad_termica_futura,
    indice_condensacion_oculta_armarios,
    indice_renovacion_efectiva_aire,
    indice_ritmo_circadiano_ambiental,
    indice_riesgo_olor_cerrado,
    indice_deshidratacion_ambiental,
)
from core.indices.index_selection import mejor_valor_indices, mejor_entrada_indices
from core.logging.log_engine import LogEngine


class MotorBase:
    def __init__(self, log_engine: Optional[LogEngine] = None):
        self._log = log_engine

    def _log_debug(self, msg: str) -> None:
        if self._log:
            self._log.log("debug", msg)

    def _log_info(self, msg: str) -> None:
        if self._log:
            self._log.log("info", msg)


# ------------------------------------------------------------
# MOTOR AMBIENTAL
# ------------------------------------------------------------

class MotorAmbiental(MotorBase):
    """
    Analiza el estado global del ambiente interior:
    - estados de la casa (cargada, seca, fría, caliente, dormida, vacía, descompensada)
    - aire viejo, aire estancado, aire pegajoso, aire pesado, etc.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAmbiental] Analizando contexto ambiental")
        indices = evaluar_indices_ambientales(contexto)

        estados: List[str] = []

        ot = contexto.get("ot")
        hr = contexto.get("humedad_interior")
        co2 = contexto.get("co2")
        tiempo_sin_ventilar = contexto.get("tiempo_sin_ventilar_h", 0.0)

        if ot is not None:
            if ot < 18:
                estados.append("fria")
            elif ot > 26:
                estados.append("caliente")

        if hr is not None:
            if hr < 35:
                estados.append("seca")
            elif hr > 65:
                estados.append("humeda")

        if co2 is not None:
            if co2 > 1200:
                estados.append("cargada")
            if co2 > 1500 and tiempo_sin_ventilar > 3:
                estados.append("aire_viejo")

        if tiempo_sin_ventilar > 8:
            estados.append("cerrada")

        # Norma de Oro: seleccionar mejor estado de aire disponible
        aire_estado = mejor_entrada_indices(indices, ["aire_cargado", "aire_enrarecido", "ventilacion_ideal"])

        resultado = {
            "indices": indices,
            "estados": estados,
            "aire_estado_recomendado": aire_estado.get("valor") if aire_estado else None,
        }

        self._log_debug(f"[MotorAmbiental] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE CONFORT
# ------------------------------------------------------------

class MotorConfort(MotorBase):
    """
    Evalúa el confort humano:
    - confort general
    - confort nocturno
    - bochorno, frío incómodo, aire seco, aire pegajoso
    - ambiente que invita a dormir (IRCA-HUMANO)
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorConfort] Analizando confort")
        indices = evaluar_indices_ambientales(contexto)

        ot = contexto.get("ot")
        luz = contexto.get("luz", 30.0)
        ruido = contexto.get("ruido", 20.0)
        estabilidad = contexto.get("estabilidad_termica", 50.0)
        irin = contexto.get("irin", 50.0)

        irca_humano = None
        if ot is not None:
            irca_humano = indice_ritmo_circadiano_ambiental(
                ot=ot,
                luz=luz,
                ruido=ruido,
                estabilidad_termica=estabilidad,
                irin=irin,
            )

        # Norma de Oro: seleccionar mejor confort disponible
        confort_resultado = mejor_valor_indices(indices, ["confort_general", "confort_nocturno", "bochorno_real"], fallback=irca_humano)

        resultado = {
            "indices": indices,
            "ritmo_circadiano_ambiental": irca_humano,
            "confort_seleccionado": confort_resultado,
        }

        self._log_debug(f"[MotorConfort] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DEL EDIFICIO
# ------------------------------------------------------------

class MotorEdificio(MotorBase):
    """
    Diagnóstico del edificio:
    - salud del edificio
    - riesgo de moho
    - condensación en ventanas
    - condensación oculta en armarios
    - olor a cerrado
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorEdificio] Analizando edificio")

        t_int = contexto.get("temperatura_interior")
        hr_int = contexto.get("humedad_interior")
        t_ext = contexto.get("temperatura_exterior")
        humedad_media = contexto.get("humedad_media", hr_int or 50.0)
        tiempo_hr_alta = contexto.get("tiempo_hr_alta_h", 0.0)
        condensacion_eventos = contexto.get("condensacion_eventos", 0)
        tiempo_sin_ventilar = contexto.get("tiempo_sin_ventilar_h", 0.0)

        # Riesgo de moho
        riesgo_moho = None
        if hr_int is not None and t_int is not None:
            riesgo_moho = indice_riesgo_moho(hr_int, tiempo_hr_alta, t_int)

        # Condensación en ventanas
        riesgo_cond_ventanas = None
        if t_int is not None and hr_int is not None and t_ext is not None:
            riesgo_cond_ventanas = indice_riesgo_condensacion_ventanas(
                t_int, hr_int, t_ext
            )

        # Condensación oculta en armarios (IRCA)
        irsh = contexto.get("irsh", 0.0)
        irin = contexto.get("irin", 0.0)
        ersf = contexto.get("ersf", 0.0)
        historial_nocturno = contexto.get("historial_nocturno_hr_alta", 0.0)
        irca = indice_condensacion_oculta_armarios(irsh, irin, ersf, historial_nocturno)

        # Olor a cerrado
        olor_cerrado = None
        if hr_int is not None:
            from core.indices.environmental_indices import indice_riesgo_olor_cerrado
            olor_cerrado = indice_riesgo_olor_cerrado(hr_int, tiempo_sin_ventilar)

        resultado = {
            "riesgo_moho": riesgo_moho,
            "riesgo_condensacion_ventanas": riesgo_cond_ventanas,
            "riesgo_condensacion_armarios": irca,
            "olor_cerrado": olor_cerrado,
            "salud_edificio": None,  # se puede completar con un índice agregado
        }

        self._log_debug(f"[MotorEdificio] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR METEOROLÓGICO LOCAL
# ------------------------------------------------------------

class MotorMeteorologico(MotorBase):
    """
    Meteorología local avanzada:
    - riesgo de helada local
    - riesgo de micro-lluvias
    - integración con índices LCI, ASI, BLTI, etc. (cuando estén implementados)
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorMeteorologico] Analizando meteorología local")

        punto_rocio = contexto.get("punto_rocio")
        t_ext = contexto.get("temperatura_exterior")
        radiacion_nocturna = contexto.get("radiacion_nocturna", 0.0)
        viento = contexto.get("viento", 0.0)
        hr_ext = contexto.get("humedad_exterior")
        irll_base = contexto.get("irll_base", 0.0)
        cambio_viento = contexto.get("cambio_viento", 0.0)
        presion_tendencia = contexto.get("presion_tendencia", 0.0)

        riesgo_helada = None
        if punto_rocio is not None and t_ext is not None:
            riesgo_helada = indice_riesgo_helada_local(
                punto_rocio, t_ext, radiacion_nocturna, viento
            )

        riesgo_micro_lluvias = None
        if hr_ext is not None:
            riesgo_micro_lluvias = indice_riesgo_micro_lluvias(
                hr_ext, irll_base, cambio_viento, presion_tendencia
            )

        resultado = {
            "riesgo_helada_local": riesgo_helada,
            "riesgo_micro_lluvias": riesgo_micro_lluvias,
        }

        self._log_debug(f"[MotorMeteorologico] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE VENTILACIÓN
# ------------------------------------------------------------

class MotorVentilacion(MotorBase):
    """
    Decide sobre:
    - ventilar ahora / no ventilar
    - tiempo estimado de ventilación
    - recuperación térmica
    - riesgo de golpe térmico al abrir ventanas
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorVentilacion] Analizando ventilación")

        co2 = contexto.get("co2")
        hr_int = contexto.get("humedad_interior")
        ot = contexto.get("ot")
        t_int = contexto.get("temperatura_interior")
        t_ext = contexto.get("temperatura_exterior")
        viento_ext = contexto.get("viento", 0.0)
        try:
            viento_ext = float(viento_ext) if viento_ext is not None else 0.0
        except Exception:
            viento_ext = 0.0
        ireav = contexto.get("ireav")
        if ireav is None:
            ireav = 50.0
        ersf = contexto.get("ersf")
        if ersf is None:
            ersf = 50.0
        irsd = contexto.get("irsd")
        if irsd is None:
            irsd = 50.0
        radiacion_solar = contexto.get("radiacion_solar", 0.0)
        hr_ext = contexto.get("humedad_exterior")

        indices = evaluar_indices_ambientales(contexto)
        # Norma de Oro para ventilación: preferir el índice específico, luego VPD, WBGT, sensación de calor
        candidatos_vent = [
            "ventilacion_ideal",
            "vpd",
            "wbgt",
            "sensacion_calor",
        ]
        ventilacion_ideal = mejor_valor_indices(indices, candidatos_vent, fallback=contexto.get("co2", 0.0))
        ventilacion_entry = mejor_entrada_indices(indices, candidatos_vent)

        # Golpe térmico al abrir ventanas
        golpe_termico = None
        if t_int is not None and t_ext is not None:
            delta_t = t_int - t_ext
            golpe_termico = max(0.0, min(100.0, abs(delta_t) * 5 + viento_ext * 2))

        # Recuperación térmica (estimación simple)
        recuperacion_termica = None
        if t_int is not None and t_ext is not None:
            delta_t = abs(t_int - t_ext)
            base = max(1.0, delta_t)
            recuperacion_termica = max(5.0, 60.0 / base + (100 - ireav) * 0.3 + (100 - irsd) * 0.2)

        # Tiempo recomendado de ventilación (min)
        tiempo_ventilacion_min = None
        try:
            co2_val = float(co2) if co2 is not None else None
            hr_int_val = float(hr_int) if hr_int is not None else None
            hr_ext_val = float(hr_ext) if hr_ext is not None else None
            base = 10.0
            if co2_val is not None:
                if co2_val > 1500:
                    base = 35.0
                elif co2_val > 1200:
                    base = 25.0
                elif co2_val > 900:
                    base = 15.0
            if hr_int_val is not None and hr_ext_val is not None:
                if hr_int_val - hr_ext_val > 10:
                    base += 5.0
            tiempo_ventilacion_min = round(base, 1)
        except Exception:
            logging.exception("Silent except at 336 - revisar contexto")

        # Predicción de secado tras ventilar
        prediccion_secado = None
        try:
            if hr_int is not None and hr_ext is not None:
                delta_hr = float(hr_int) - float(hr_ext)
                if delta_hr > 15:
                    prediccion_secado = "rápido"
                elif delta_hr > 5:
                    prediccion_secado = "moderado"
                else:
                    prediccion_secado = "lento"
        except Exception:
            logging.exception("Silent except at 350 - revisar contexto")

        resultado = {
            "ventilar_ahora": ventilacion_ideal,
            "ventilar_ahora_estimado": ventilacion_entry.get("estimado") if ventilacion_entry else None,
            "golpe_termico_al_abrir": golpe_termico,
            "tiempo_recuperacion_termica_min": recuperacion_termica,
            "tiempo_ventilacion_min": tiempo_ventilacion_min,
            "prediccion_secado_post_ventilacion": prediccion_secado,
        }

        self._log_debug(f"[MotorVentilacion] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE PREDICCIÓN LOCAL
# ------------------------------------------------------------

class MotorPrediccionLocal(MotorBase):
    """
    Predicciones locales basadas SOLO en sensores propios:
    - noches incómodas
    - ambiente que invita a dormir
    - evolución térmica
    - evolución de humedad
    - riesgo de mojar la ropa (cuando se integre el índice específico)
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorPrediccionLocal] Analizando predicción local")
        tendencia_t = contexto.get("tendencia_temperatura")
        tendencia_h = contexto.get("tendencia_humedad")
        riesgo_lluvia = contexto.get("riesgo_lluvia")
        riesgo_micro = contexto.get("riesgo_micro_lluvias")
        alerta_tormenta = contexto.get("alerta_tormenta")
        riesgo_helada = contexto.get("riesgo_helada_local")
        hora = contexto.get("hora_local")
        confort_nocturno = None
        try:
            _indices = evaluar_indices_ambientales(contexto)
            confort_nocturno = mejor_valor_indices(_indices, ["confort_nocturno", "confort_general"], fallback=None)
        except Exception:
            confort_nocturno = None

        evolucion_termica = None
        if tendencia_t is not None:
            try:
                t = float(tendencia_t)
                if t > 0.05:
                    evolucion_termica = "subiendo"
                elif t < -0.05:
                    evolucion_termica = "bajando"
                else:
                    evolucion_termica = "estable"
            except Exception:
                logging.exception("Silent except at 406 - revisar contexto")

        evolucion_humedad = None
        if tendencia_h is not None:
            try:
                h = float(tendencia_h)
                if h > 0.05:
                    evolucion_humedad = "subiendo"
                elif h < -0.05:
                    evolucion_humedad = "bajando"
                else:
                    evolucion_humedad = "estable"
            except Exception:
                logging.exception("Silent except at 419 - revisar contexto")

        riesgo_mojar_ropa = None
        try:
            rl = float(riesgo_lluvia) if riesgo_lluvia is not None else 0.0
            rm = float(riesgo_micro) if riesgo_micro is not None else 0.0
            at = float(alerta_tormenta) if alerta_tormenta is not None else 0.0
            score = max(rl, rm, at)
            if score >= 70:
                riesgo_mojar_ropa = "alto"
            elif score >= 40:
                riesgo_mojar_ropa = "medio"
            else:
                riesgo_mojar_ropa = "bajo"
        except Exception:
            logging.exception("Silent except at 434 - revisar contexto")

        noche_incomoda = None
        try:
            if hora is not None:
                h = float(hora)
                es_noche = h >= 20 or h < 7
            else:
                es_noche = False
            if es_noche:
                if riesgo_helada is not None and float(riesgo_helada) > 60:
                    noche_incomoda = "fría"
                elif confort_nocturno is not None and float(confort_nocturno) < 40:
                    noche_incomoda = "incómoda"
                else:
                    noche_incomoda = "probablemente_ok"
        except Exception:
            logging.exception("Silent except at 451 - revisar contexto")

        ambiente_invita_dormir = None
        if confort_nocturno is not None:
            try:
                cn = float(confort_nocturno)
                if cn > 70:
                    ambiente_invita_dormir = "alto"
                elif cn > 50:
                    ambiente_invita_dormir = "medio"
                else:
                    ambiente_invita_dormir = "bajo"
            except Exception:
                logging.exception("Silent except at 464 - revisar contexto")

        resultado = {
            "prediccion_noche_incomoda": noche_incomoda,
            "prediccion_ambiente_invita_dormir": ambiente_invita_dormir,
            "prediccion_evolucion_termica": evolucion_termica,
            "prediccion_evolucion_humedad": evolucion_humedad,
            "prediccion_riesgo_mojar_ropa": riesgo_mojar_ropa,
        }

        self._log_debug(f"[MotorPrediccionLocal] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# GESTOR DE HUELLAS ATMOSFÉRICAS
# ------------------------------------------------------------

class PerfilAtmosfericoPersona:
    """
    Representa la huella atmosférica de una persona:
    - preferencias de confort
    - tolerancia a humedad, temperatura, ruido, luz
    - horarios típicos
    """

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.preferencias: Dict[str, Any] = {}
        self.historial: List[Dict[str, Any]] = []

    def registrar_contexto(self, contexto: Dict[str, Any]) -> None:
        self.historial.append(contexto)

    def ajustar_preferencias(self) -> None:
        # TODO: implementar aprendizaje real
        pass


class GestorHuellasAtmosfericas(MotorBase):
    """
    Gestiona perfiles atmosféricos por persona:
    - aprendizaje de huella
    - identificación de persona (futuro)
    - personalización de confort
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        super().__init__(log_engine)
        self._perfiles: Dict[str, PerfilAtmosfericoPersona] = {}

    def obtener_o_crear_perfil(self, nombre: str) -> PerfilAtmosfericoPersona:
        if nombre not in self._perfiles:
            self._perfiles[nombre] = PerfilAtmosfericoPersona(nombre)
        return self._perfiles[nombre]

    def analizar(self, nombre: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        perfil = self.obtener_o_crear_perfil(nombre)
        perfil.registrar_contexto(contexto)
        perfil.ajustar_preferencias()
        self._log_debug(f"[GestorHuellasAtmosfericas] Actualizado perfil de {nombre}")
        return {
            "perfil": perfil.preferencias,
            "historial_len": len(perfil.historial),
        }


# ------------------------------------------------------------
# MOTOR DE USO DE DISPOSITIVOS Y LUZ ARTIFICIAL
# ------------------------------------------------------------

class MotorUsoDispositivos(MotorBase):
    """
    Detecta uso de dispositivos y luz artificial de forma heurística.
    - luz artificial probable cuando hay alta luz interior con radiación baja
    - actividad sonora probable cuando hay ruido interior elevado
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorUsoDispositivos] Analizando uso de dispositivos")
        luz = contexto.get("luz")
        radiacion = contexto.get("radiacion_solar")
        ruido = contexto.get("ruido")
        hora = contexto.get("hora_local")

        luz_artificial = None
        if luz is not None:
            try:
                luz_val = float(luz)
                rad_val = float(radiacion) if radiacion is not None else 0.0
                if luz_val > 70 and rad_val < 50:
                    luz_artificial = "probable"
                elif luz_val > 70:
                    luz_artificial = "mixta"
                else:
                    luz_artificial = "baja"
            except Exception:
                logging.exception("Silent except at 561 - revisar contexto")

        actividad_sonora = None
        if ruido is not None:
            try:
                ruido_val = float(ruido)
                if ruido_val > 65:
                    actividad_sonora = "alta"
                elif ruido_val > 45:
                    actividad_sonora = "media"
                else:
                    actividad_sonora = "baja"
            except Exception:
                logging.exception("Silent except at 574 - revisar contexto")

        resultado = {
            "luz_artificial": luz_artificial,
            "actividad_sonora": actividad_sonora,
            "hora": hora,
        }

        self._log_debug(f"[MotorUsoDispositivos] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR NOCTURNO
# ------------------------------------------------------------

class MotorNocturno(MotorBase):
    """
    Capacidades nocturnas: enfriamiento radiativo, niebla y confort nocturno.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorNocturno] Analizando capacidades nocturnas")
        hora = contexto.get("hora_local")
        radiacion = contexto.get("radiacion_solar")
        humedad = contexto.get("humedad_exterior")
        viento = contexto.get("viento")
        temperatura = contexto.get("temperatura_exterior")

        es_noche = None
        if hora is not None:
            try:
                h = float(hora)
                es_noche = h >= 20 or h < 7
            except Exception:
                logging.exception("Silent except at 609 - revisar contexto")

        enfriamiento_radiativo = None
        if radiacion is not None and temperatura is not None:
            try:
                rad = float(radiacion)
                temp = float(temperatura)
                if rad < 20 and temp <= 10:
                    enfriamiento_radiativo = "alto"
                elif rad < 50:
                    enfriamiento_radiativo = "moderado"
                else:
                    enfriamiento_radiativo = "bajo"
            except Exception:
                logging.exception("Silent except at 623 - revisar contexto")

        niebla_nocturna = None
        if humedad is not None and viento is not None:
            try:
                hr = float(humedad)
                v = float(viento)
                if hr > 85 and v < 5:
                    niebla_nocturna = "probable"
                elif hr > 75:
                    niebla_nocturna = "posible"
                else:
                    niebla_nocturna = "baja"
            except Exception:
                logging.exception("Silent except at 637 - revisar contexto")

        resultado = {
            "es_noche": es_noche,
            "enfriamiento_radiativo": enfriamiento_radiativo,
            "niebla_nocturna": niebla_nocturna,
        }

        self._log_debug(f"[MotorNocturno] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE INTRUSIÓN AMBIENTAL
# ------------------------------------------------------------

class MotorIntrusion(MotorBase):
    """
    Detección de intrusión por firmas ambientales:
    - subidas repentinas de ruido, CO2 o luz en horarios inusuales
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorIntrusion] Analizando intrusión")
        hora = contexto.get("hora_local")
        ruido = contexto.get("ruido")
        co2 = contexto.get("co2")
        luz = contexto.get("luz")

        alerta = None
        detalles = []

        try:
            if hora is not None:
                h = float(hora)
                es_noche = h >= 22 or h < 6
            else:
                es_noche = False
        except Exception:
            es_noche = False

        try:
            if ruido is not None and float(ruido) > 70 and es_noche:
                alerta = "posible_intrusion"
                detalles.append("Ruido alto en horario nocturno")
        except Exception:
            logging.exception("Silent except at 683 - revisar contexto")

        try:
            if co2 is not None and float(co2) > 1400 and es_noche:
                alerta = alerta or "posible_intrusion"
                detalles.append("CO2 alto en horario nocturno")
        except Exception:
            logging.exception("Silent except at 690 - revisar contexto")

        try:
            if luz is not None and float(luz) > 75 and es_noche:
                alerta = alerta or "posible_intrusion"
                detalles.append("Luz alta en horario nocturno")
        except Exception:
            logging.exception("Silent except at 697 - revisar contexto")

        resultado = {
            "alerta": alerta,
            "detalles": detalles,
        }

        self._log_debug(f"[MotorIntrusion] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE RIESGOS PARA MATERIALES
# ------------------------------------------------------------

class MotorMateriales(MotorBase):
    """
    Riesgos para materiales y objetos sensibles (libros, madera, electrónica, instrumentos).
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorMateriales] Analizando riesgos de materiales")
        hr = contexto.get("humedad_interior")
        temp = contexto.get("temperatura_interior")

        riesgos = {}

        try:
            if hr is not None:
                h = float(hr)
                if h >= 70:
                    riesgos["libros_papel"] = "alto"
                    riesgos["madera_muebles"] = "alto"
                    riesgos["instrumentos"] = "alto"
                    riesgos["electronica"] = "medio"
                elif h >= 60:
                    riesgos["libros_papel"] = "medio"
                    riesgos["madera_muebles"] = "medio"
                    riesgos["instrumentos"] = "medio"
                elif h <= 35:
                    riesgos["instrumentos"] = "medio"
                    riesgos["madera_muebles"] = "medio"
        except Exception:
            logging.exception("Silent except at 740 - revisar contexto")

        try:
            if temp is not None:
                t = float(temp)
                if t <= 10:
                    riesgos["electronica"] = "medio"
                elif t >= 30:
                    riesgos["electronica"] = "medio"
        except Exception:
            logging.exception("Silent except at 750 - revisar contexto")

        resultado = {
            "riesgos": riesgos,
        }

        self._log_debug(f"[MotorMateriales] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE AVISOS PRÁCTICOS
# ------------------------------------------------------------

class MotorAvisosPracticos(MotorBase):
    """
    Avisos prácticos diarios: ventilar, tender ropa, persianas, paraguas.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAvisosPracticos] Analizando avisos prácticos")
        avisos = []

        riesgo_lluvia = contexto.get("riesgo_lluvia")
        alerta_tormenta = contexto.get("alerta_tormenta")
        radiacion = contexto.get("radiacion_solar")
        viento = contexto.get("viento")
        hr_ext = contexto.get("humedad_exterior")
        # Obtener mediante Norma de Oro: preferir índice calculado antes que contexto directo
        try:
            _indices = evaluar_indices_ambientales(contexto)
            ventilar_ideal = mejor_valor_indices(_indices, ["ventilacion_ideal", "vpd", "wbgt", "sensacion_calor"], fallback=contexto.get("ventilacion_ideal"))
        except Exception:
            ventilar_ideal = contexto.get("ventilacion_ideal")

        try:
            if riesgo_lluvia is not None and float(riesgo_lluvia) > 60:
                avisos.append("Lleva paraguas: riesgo de lluvia alto.")
        except Exception:
            logging.exception("Silent except at 789 - revisar contexto")

        try:
            if alerta_tormenta is not None and float(alerta_tormenta) > 60:
                avisos.append("Posible tormenta: evita tender ropa.")
        except Exception:
            logging.exception("Silent except at 795 - revisar contexto")

        try:
            if radiacion is not None and float(radiacion) > 500 and (riesgo_lluvia is None or float(riesgo_lluvia) < 40):
                avisos.append("Buen momento para tender ropa.")
        except Exception:
            logging.exception("Silent except at 801 - revisar contexto")

        try:
            if viento is not None and float(viento) > 30:
                avisos.append("Viento fuerte: asegura objetos exteriores.")
        except Exception:
            logging.exception("Silent except at 807 - revisar contexto")

        try:
            if hr_ext is not None and float(hr_ext) > 80:
                avisos.append("Humedad exterior alta: secado lento.")
        except Exception:
            logging.exception("Silent except at 813 - revisar contexto")

        try:
            if ventilar_ideal is not None and float(ventilar_ideal) > 60:
                avisos.append("Ventilar ahora es recomendable.")
        except Exception:
            logging.exception("Silent except at 819 - revisar contexto")

        resultado = {"avisos": avisos}
        self._log_debug(f"[MotorAvisosPracticos] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE SALUD DEL AIRE INTERIOR
# ------------------------------------------------------------

class MotorSaludAire(MotorBase):
    """
    Evalúa calidad de aire interior con CO2 y PM2.5.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorSaludAire] Analizando calidad de aire")
        co2 = contexto.get("co2")
        pm25 = contexto.get("pm25")

        calidad = "desconocida"
        detalles = []

        try:
            if co2 is not None:
                c = float(co2)
                if c < 800:
                    detalles.append("CO2 bueno")
                elif c < 1200:
                    detalles.append("CO2 moderado")
                else:
                    detalles.append("CO2 alto")
        except Exception:
            logging.exception("Silent except at 853 - revisar contexto")

        try:
            if pm25 is not None:
                p = float(pm25)
                if p <= 12:
                    detalles.append("PM2.5 bueno")
                elif p <= 35:
                    detalles.append("PM2.5 moderado")
                else:
                    detalles.append("PM2.5 alto")
        except Exception:
            logging.exception("Silent except at 865 - revisar contexto")

        if any("alto" in d for d in detalles):
            calidad = "mala"
        elif detalles:
            calidad = "media"

        resultado = {
            "calidad": calidad,
            "detalles": detalles,
        }

        self._log_debug(f"[MotorSaludAire] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE VENTANAS / PUERTAS (INFERIDO)
# ------------------------------------------------------------

class MotorVentanasPuertas(MotorBase):
    """
    Infere posibles aperturas por cambios de T/HR/CO2 y viento.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorVentanasPuertas] Analizando aperturas")
        t_int = contexto.get("temperatura_interior")
        t_ext = contexto.get("temperatura_exterior")
        hr_int = contexto.get("humedad_interior")
        hr_ext = contexto.get("humedad_exterior")
        co2 = contexto.get("co2")
        viento = contexto.get("viento")

        apertura_probable = None
        corrientes = None

        try:
            if t_int is not None and t_ext is not None:
                delta_t = abs(float(t_int) - float(t_ext))
                if delta_t > 6 and viento is not None and float(viento) > 15:
                    corrientes = "probables"
        except Exception:
            logging.exception("Silent except at 908 - revisar contexto")

        try:
            if co2 is not None and float(co2) < 700 and (hr_int is not None and hr_ext is not None):
                if abs(float(hr_int) - float(hr_ext)) < 5:
                    apertura_probable = "ventilacion_activa"
        except Exception:
            logging.exception("Silent except at 915 - revisar contexto")

        resultado = {
            "apertura_probable": apertura_probable,
            "corrientes": corrientes,
        }

        self._log_debug(f"[MotorVentanasPuertas] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE RIESGOS DE HUMEDAD (CONDENSACIÓN/MOHO)
# ------------------------------------------------------------

class MotorRiesgoHumedad(MotorBase):
    """
    Combina riesgo de condensación y moho usando índices existentes.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoHumedad] Analizando riesgos de humedad")
        t_int = contexto.get("temperatura_interior")
        hr_int = contexto.get("humedad_interior")
        t_ext = contexto.get("temperatura_exterior")
        tiempo_hr_alta = contexto.get("tiempo_hr_alta_h", 0.0)

        riesgo_moho = None
        riesgo_cond = None

        try:
            if hr_int is not None and t_int is not None:
                riesgo_moho = indice_riesgo_moho(float(hr_int), float(tiempo_hr_alta), float(t_int))
        except Exception:
            logging.exception("Silent except at 949 - revisar contexto")

        try:
            if t_int is not None and hr_int is not None and t_ext is not None:
                riesgo_cond = indice_riesgo_condensacion_ventanas(float(t_int), float(hr_int), float(t_ext))
        except Exception:
            logging.exception("Silent except at 955 - revisar contexto")

        resultado = {
            "riesgo_moho": riesgo_moho,
            "riesgo_condensacion": riesgo_cond,
        }

        self._log_debug(f"[MotorRiesgoHumedad] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE TEMPERATURA OPERATIVA (OT) REAL
# ------------------------------------------------------------

class MotorTemperaturaOperativa(MotorBase):
    """
    Estima OT (temperatura operativa) con T aire, radiación y viento.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorTemperaturaOperativa] Calculando OT")
        t_int = contexto.get("temperatura_interior")
        rad = contexto.get("radiacion_solar")
        viento = contexto.get("viento")

        ot = None
        try:
            if t_int is not None:
                t = float(t_int)
                r = float(rad) if rad is not None else 0.0
                v = float(viento) if viento is not None else 0.0
                ajuste_rad = min(2.5, r / 400.0)  # +0..2.5°C
                ajuste_viento = -min(1.5, v / 20.0)  # -0..-1.5°C
                ot = round(t + ajuste_rad + ajuste_viento, 2)
        except Exception:
            logging.exception("Silent except at 991 - revisar contexto")

        resultado = {"ot_real": ot}
        self._log_debug(f"[MotorTemperaturaOperativa] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RITMO CIRCADIANO PERSONAL
# ------------------------------------------------------------

class MotorRitmoCircadianoPersona(MotorBase):
    """
    Evalúa si el ambiente favorece sueño o vigilia (IRCA humano simplificado).
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRitmoCircadianoPersona] Analizando ritmo circadiano")
        luz = contexto.get("luz")
        ruido = contexto.get("ruido")
        ot = contexto.get("ot")
        estabilidad = contexto.get("estabilidad_termica", 50.0)
        irin = contexto.get("irin", 50.0)

        score = None
        try:
            score = indice_ritmo_circadiano_ambiental(
                ot=ot if ot is not None else 22.0,
                luz=float(luz) if luz is not None else 30.0,
                ruido=float(ruido) if ruido is not None else 20.0,
                estabilidad_termica=float(estabilidad) if estabilidad is not None else 50.0,
                irin=float(irin) if irin is not None else 50.0,
            )
        except Exception:
            logging.exception("Silent except at 1025 - revisar contexto")

        # Norma de Oro: usar mejor índice de confort nocturno disponible
        indices = evaluar_indices_ambientales(contexto)
        confort_nocturno_mejor = mejor_valor_indices(indices, ["confort_nocturno", "confort_general"], fallback=score)

        estado = None
        if confort_nocturno_mejor is not None:
            try:
                s = float(confort_nocturno_mejor)
                if s >= 70:
                    estado = "favorece_sueno"
                elif s >= 50:
                    estado = "neutro"
                else:
                    estado = "favorece_vigilia"
            except Exception:
                logging.exception("Silent except at 1042 - revisar contexto")

        resultado = {"irca_humano": score, "estado": estado}
        self._log_debug(f"[MotorRitmoCircadianoPersona] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE HABITABILIDAD / ESTABILIDAD TÉRMICA
# ------------------------------------------------------------

class MotorHabitabilidad(MotorBase):
    """
    Evalúa estabilidad térmica y confort general para habitabilidad.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorHabitabilidad] Analizando habitabilidad")
        indices = evaluar_indices_ambientales(contexto)
        confort = mejor_valor_indices(indices, ["confort_general", "confort_nocturno", "confort_ave"], fallback=indices.get("confort_general"))
        estabilidad = contexto.get("estabilidad_termica")

        estado = None
        try:
            c = float(confort) if confort is not None else None
            e = float(estabilidad) if estabilidad is not None else None
            if c is not None and e is not None:
                score = (c + e) / 2.0
            elif c is not None:
                score = c
            elif e is not None:
                score = e
            else:
                score = None

            if score is not None:
                if score >= 75:
                    estado = "estable"
                elif score >= 55:
                    estado = "moderada"
                else:
                    estado = "inestable"
        except Exception:
            logging.exception("Silent except at 1085 - revisar contexto")

        resultado = {
            "confort_general": confort,
            "estabilidad_termica": estabilidad,
            "estado": estado,
        }

        self._log_debug(f"[MotorHabitabilidad] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE CONFORT NOCTURNO
# ------------------------------------------------------------

class MotorConfortNocturno(MotorBase):
    """
    Evalúa confort nocturno con índices ambientales.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorConfortNocturno] Analizando confort nocturno")
        indices = evaluar_indices_ambientales(contexto)
        confort_nocturno = mejor_valor_indices(indices, ["confort_nocturno", "confort_general"], fallback=indices.get("confort_nocturno"))

        estado = None
        try:
            if confort_nocturno is not None:
                c = float(confort_nocturno)
                if c >= 70:
                    estado = "muy_bueno"
                elif c >= 50:
                    estado = "aceptable"
                else:
                    estado = "malo"
        except Exception:
            logging.exception("Silent except at 1122 - revisar contexto")

        resultado = {"confort_nocturno": confort_nocturno, "estado": estado}
        self._log_debug(f"[MotorConfortNocturno] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR METEOROLÓGICO AVANZADO (AGREGADOR)
# ------------------------------------------------------------

class MotorMeteorologiaAvanzada(MotorBase):
    """
    Agrega riesgos meteorológicos avanzados ya calculados.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorMeteorologiaAvanzada] Analizando meteorología avanzada")
        resultado = {
            "riesgo_lluvia": contexto.get("riesgo_lluvia"),
            "alerta_tormenta": contexto.get("alerta_tormenta"),
            "riesgo_micro_lluvias": contexto.get("riesgo_micro_lluvias"),
            "riesgo_helada_local": contexto.get("riesgo_helada_local"),
            "nubosidad_estimada": contexto.get("nubosidad_estimada"),
        }
        self._log_debug(f"[MotorMeteorologiaAvanzada] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE VIENTO / RACHAS
# ------------------------------------------------------------

class MotorVientoRachas(MotorBase):
    """
    Evalúa riesgo por viento y rachas peligrosas.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorVientoRachas] Analizando viento y rachas")
        viento = contexto.get("viento")
        rachas = contexto.get("racha_viento")

        riesgo = None
        try:
            v = float(rachas) if rachas is not None else float(viento) if viento is not None else None
            if v is not None:
                if v >= 60:
                    riesgo = "peligroso"
                elif v >= 40:
                    riesgo = "alto"
                elif v >= 25:
                    riesgo = "moderado"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1178 - revisar contexto")

        resultado = {"riesgo_viento": riesgo, "viento": viento, "racha_viento": rachas}
        self._log_debug(f"[MotorVientoRachas] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE VISIBILIDAD LOCAL
# ------------------------------------------------------------

class MotorVisibilidadLocal(MotorBase):
    """
    Estima visibilidad local usando riesgo de niebla y lluvia.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorVisibilidadLocal] Analizando visibilidad")
        riesgo_niebla = contexto.get("riesgo_niebla")
        riesgo_lluvia = contexto.get("riesgo_lluvia")

        visibilidad = None
        try:
            rn = float(riesgo_niebla) if riesgo_niebla is not None else 0.0
            rl = float(riesgo_lluvia) if riesgo_lluvia is not None else 0.0
            score = max(rn, rl)
            if score >= 70:
                visibilidad = "muy_baja"
            elif score >= 40:
                visibilidad = "baja"
            elif score >= 20:
                visibilidad = "media"
            else:
                visibilidad = "buena"
        except Exception:
            logging.exception("Silent except at 1213 - revisar contexto")

        resultado = {"visibilidad": visibilidad}
        self._log_debug(f"[MotorVisibilidadLocal] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE LUZ NATURAL
# ------------------------------------------------------------

class MotorLuzNatural(MotorBase):
    """
    Decide si es necesario encender luz artificial.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorLuzNatural] Analizando luz natural")
        luz = contexto.get("luz")
        radiacion = contexto.get("radiacion_solar")

        necesidad = None
        try:
            l = float(luz) if luz is not None else None
            r = float(radiacion) if radiacion is not None else None
            if l is not None:
                if l < 20:
                    necesidad = "encender_luz"
                elif l < 40 and (r is None or r < 80):
                    necesidad = "considerar_luz"
                else:
                    necesidad = "no_necesaria"
        except Exception:
            logging.exception("Silent except at 1246 - revisar contexto")

        resultado = {"necesidad_luz": necesidad}
        self._log_debug(f"[MotorLuzNatural] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DE CONFORT TÉRMICO (BOCHORNO / FRÍO)
# ------------------------------------------------------------

class MotorConfortTermico(MotorBase):
    """
    Evalúa bochorno real y frío incómodo.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorConfortTermico] Analizando confort térmico")
        indices = evaluar_indices_ambientales(contexto)
        bochorno = indices.get("bochorno_real")
        frio = indices.get("frio_incomodo")

        estado = None
        try:
            b = float(bochorno) if bochorno is not None else 0.0
            f = float(frio) if frio is not None else 0.0
            if b >= 60:
                estado = "bochorno"
            elif f >= 60:
                estado = "frio"
            else:
                estado = "neutral"
        except Exception:
            logging.exception("Silent except at 1279 - revisar contexto")

        resultado = {"bochorno_real": bochorno, "frio_incomodo": frio, "estado": estado}
        self._log_debug(f"[MotorConfortTermico] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR AIRE PEGajOSO / SECO
# ------------------------------------------------------------

class MotorAirePegajosoSeco(MotorBase):
    """
    Evalúa aire pegajoso o seco según índices.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAirePegajosoSeco] Analizando aire")
        indices = evaluar_indices_ambientales(contexto)
        aire_seco = indices.get("aire_seco")
        aire_pegajoso = indices.get("aire_pegajoso")

        estado = None
        try:
            s = float(aire_seco) if aire_seco is not None else 0.0
            p = float(aire_pegajoso) if aire_pegajoso is not None else 0.0
            if s >= 60:
                estado = "seco"
            elif p >= 60:
                estado = "pegajoso"
            else:
                estado = "normal"
        except Exception:
            logging.exception("Silent except at 1312 - revisar contexto")

        resultado = {"aire_seco": aire_seco, "aire_pegajoso": aire_pegajoso, "estado": estado}
        self._log_debug(f"[MotorAirePegajosoSeco] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR AIRE CARGADO / VIEJO
# ------------------------------------------------------------

class MotorAireCargado(MotorBase):
    """
    Evalúa aire cargado por CO2.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAireCargado] Analizando CO2")
        co2 = contexto.get("co2")
        estado = None
        try:
            if co2 is not None:
                c = float(co2)
                if c >= 1500:
                    estado = "muy_cargado"
                elif c >= 1200:
                    estado = "cargado"
                elif c >= 900:
                    estado = "moderado"
                else:
                    estado = "ok"
        except Exception:
            logging.exception("Silent except at 1344 - revisar contexto")

        resultado = {"co2": co2, "estado": estado}
        self._log_debug(f"[MotorAireCargado] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR AIRE ENRARECIDO (CO2 + PM2.5)
# ------------------------------------------------------------

class MotorAireEnrarecido(MotorBase):
    """
    Evalúa aire enrarecido combinando CO2 y PM2.5.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAireEnrarecido] Analizando aire enrarecido")
        indices = evaluar_indices_ambientales(contexto)
        aire_enrarecido = indices.get("aire_enrarecido")

        estado = None
        try:
            if aire_enrarecido is not None:
                v = float(aire_enrarecido)
                if v >= 70:
                    estado = "alto"
                elif v >= 40:
                    estado = "medio"
                else:
                    estado = "bajo"
        except Exception:
            logging.exception("Silent except at 1376 - revisar contexto")

        resultado = {"aire_enrarecido": aire_enrarecido, "estado": estado}
        self._log_debug(f"[MotorAireEnrarecido] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR DESHIDRATACIÓN AMBIENTAL
# ------------------------------------------------------------

class MotorDeshidratacionAmbiental(MotorBase):
    """
    Evalúa riesgo de deshidratación ambiental por baja humedad y tiempo.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorDeshidratacionAmbiental] Analizando deshidratación")
        hr = contexto.get("humedad_interior")
        tiempo_hr_baja = contexto.get("tiempo_hr_baja_h", 0.0)

        riesgo = None
        try:
            if hr is not None:
                riesgo = indice_deshidratacion_ambiental(float(hr), float(tiempo_hr_baja))
        except Exception:
            logging.exception("Silent except at 1402 - revisar contexto")

        resultado = {"deshidratacion_ambiental": riesgo}
        self._log_debug(f"[MotorDeshidratacionAmbiental] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR AIRE ESTANCADO
# ------------------------------------------------------------

class MotorAireEstancado(MotorBase):
    """
    Evalúa aire estancado con CO2 y tiempo sin ventilar.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorAireEstancado] Analizando aire estancado")
        co2 = contexto.get("co2")
        tiempo_sin_ventilar = contexto.get("tiempo_sin_ventilar_h", 0.0)

        estado = None
        try:
            if co2 is not None:
                c = float(co2)
                if c >= 1200 and float(tiempo_sin_ventilar) >= 3:
                    estado = "alto"
                elif c >= 900:
                    estado = "medio"
                else:
                    estado = "bajo"
        except Exception:
            logging.exception("Silent except at 1434 - revisar contexto")

        resultado = {"aire_estancado": estado}
        self._log_debug(f"[MotorAireEstancado] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RENOVACIÓN EFECTIVA DEL AIRE
# ------------------------------------------------------------

class MotorRenovacionAire(MotorBase):
    """
    Calcula la renovación efectiva del aire (IREA).
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRenovacionAire] Analizando renovación aire")
        co2 = contexto.get("co2")
        pm25 = contexto.get("pm25", 5.0)
        irin = contexto.get("irin", 50.0)
        irae = contexto.get("irae", 50.0)
        actividad = contexto.get("actividad_humana", 50.0)

        valor = None
        try:
            valor = indice_renovacion_efectiva_aire(
                float(co2) if co2 is not None else 600.0,
                float(pm25) if pm25 is not None else 5.0,
                float(irin) if irin is not None else 50.0,
                float(irae) if irae is not None else 50.0,
                float(actividad) if actividad is not None else 50.0,
            )
        except Exception:
            logging.exception("Silent except at 1468 - revisar contexto")

        resultado = {"renovacion_aire": valor}
        self._log_debug(f"[MotorRenovacionAire] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO OXIDACIÓN
# ------------------------------------------------------------

class MotorRiesgoOxidacion(MotorBase):
    """
    Riesgo de oxidación acelerada por humedad alta.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoOxidacion] Analizando oxidación")
        hr = contexto.get("humedad_interior")
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                if h >= 75:
                    riesgo = "alto"
                elif h >= 60:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1498 - revisar contexto")
        resultado = {"riesgo_oxidacion": riesgo}
        self._log_debug(f"[MotorRiesgoOxidacion] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO LIBROS/PAPEL
# ------------------------------------------------------------

class MotorRiesgoLibrosPapel(MotorBase):
    """
    Riesgo para libros/papel por humedad alta.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoLibrosPapel] Analizando libros/papel")
        hr = contexto.get("humedad_interior")
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                if h >= 70:
                    riesgo = "alto"
                elif h >= 55:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1527 - revisar contexto")
        resultado = {"riesgo_libros_papel": riesgo}
        self._log_debug(f"[MotorRiesgoLibrosPapel] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO ELECTRÓNICA
# ------------------------------------------------------------

class MotorRiesgoElectronica(MotorBase):
    """
    Riesgo para electrónica sensible por humedad/temperatura.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoElectronica] Analizando electrónica")
        hr = contexto.get("humedad_interior")
        temp = contexto.get("temperatura_interior")
        riesgo = None
        try:
            h = float(hr) if hr is not None else None
            t = float(temp) if temp is not None else None
            if h is not None and h >= 70:
                riesgo = "medio"
            if t is not None and (t <= 8 or t >= 32):
                riesgo = "medio" if riesgo is None else "alto"
            if riesgo is None:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1557 - revisar contexto")
        resultado = {"riesgo_electronica": riesgo}
        self._log_debug(f"[MotorRiesgoElectronica] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO PLÁSTICOS
# ------------------------------------------------------------

class MotorRiesgoPlasticos(MotorBase):
    """
    Riesgo de deformación de plásticos por calor/humedad.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoPlasticos] Analizando plásticos")
        hr = contexto.get("humedad_interior")
        temp = contexto.get("temperatura_interior")
        riesgo = None
        try:
            h = float(hr) if hr is not None else 50.0
            t = float(temp) if temp is not None else 22.0
            if t >= 32 or h >= 75:
                riesgo = "alto"
            elif t >= 28 or h >= 65:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1587 - revisar contexto")
        resultado = {"riesgo_plasticos": riesgo}
        self._log_debug(f"[MotorRiesgoPlasticos] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO ROPA GUARDADA
# ------------------------------------------------------------

class MotorRiesgoRopaGuardada(MotorBase):
    """
    Riesgo de humedad en ropa guardada.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoRopaGuardada] Analizando ropa guardada")
        hr = contexto.get("humedad_interior")
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                if h >= 70:
                    riesgo = "alto"
                elif h >= 60:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1616 - revisar contexto")
        resultado = {"riesgo_ropa_guardada": riesgo}
        self._log_debug(f"[MotorRiesgoRopaGuardada] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO COLCHONES
# ------------------------------------------------------------

class MotorRiesgoColchones(MotorBase):
    """
    Riesgo de humedad en colchones por HR alta prolongada.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoColchones] Analizando colchones")
        hr = contexto.get("humedad_interior")
        tiempo_hr_alta = contexto.get("tiempo_hr_alta_h", 0.0)
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                th = float(tiempo_hr_alta)
                if h >= 70 and th >= 6:
                    riesgo = "alto"
                elif h >= 65 and th >= 3:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1647 - revisar contexto")
        resultado = {"riesgo_colchones": riesgo}
        self._log_debug(f"[MotorRiesgoColchones] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO ALIMENTOS
# ------------------------------------------------------------

class MotorRiesgoAlimentos(MotorBase):
    """
    Riesgo de descomposición de alimentos por temperatura/humedad.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoAlimentos] Analizando alimentos")
        hr = contexto.get("humedad_interior")
        temp = contexto.get("temperatura_interior")
        riesgo = None
        try:
            h = float(hr) if hr is not None else 50.0
            t = float(temp) if temp is not None else 22.0
            if t >= 28 and h >= 65:
                riesgo = "alto"
            elif t >= 24 or h >= 60:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1677 - revisar contexto")
        resultado = {"riesgo_alimentos": riesgo}
        self._log_debug(f"[MotorRiesgoAlimentos] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO INSTRUMENTOS
# ------------------------------------------------------------

class MotorRiesgoInstrumentos(MotorBase):
    """
    Riesgo para instrumentos musicales por HR baja/alta.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoInstrumentos] Analizando instrumentos")
        hr = contexto.get("humedad_interior")
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                if h >= 70:
                    riesgo = "alto"
                elif h <= 35:
                    riesgo = "alto"
                elif h >= 60 or h <= 40:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1708 - revisar contexto")
        resultado = {"riesgo_instrumentos": riesgo}
        self._log_debug(f"[MotorRiesgoInstrumentos] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO MADERA/MUEBLES
# ------------------------------------------------------------

class MotorRiesgoMadera(MotorBase):
    """
    Riesgo para muebles de madera por humedad.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoMadera] Analizando madera")
        hr = contexto.get("humedad_interior")
        riesgo = None
        try:
            if hr is not None:
                h = float(hr)
                if h >= 70:
                    riesgo = "alto"
                elif h >= 60:
                    riesgo = "medio"
                elif h <= 35:
                    riesgo = "medio"
                else:
                    riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1739 - revisar contexto")
        resultado = {"riesgo_madera": riesgo}
        self._log_debug(f"[MotorRiesgoMadera] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR ACTIVIDAD HUMANA
# ------------------------------------------------------------

class MotorActividadHumana(MotorBase):
    """
    Infere nivel de actividad humana por CO2, ruido y luz.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorActividadHumana] Analizando actividad")
        co2 = contexto.get("co2")
        ruido = contexto.get("ruido")
        luz = contexto.get("luz")

        nivel = None
        try:
            c = float(co2) if co2 is not None else 0.0
            r = float(ruido) if ruido is not None else 0.0
            l = float(luz) if luz is not None else 0.0
            score = (c / 20.0) + (r) + (l / 2.0)
            if score >= 120:
                nivel = "alta"
            elif score >= 70:
                nivel = "media"
            else:
                nivel = "baja"
        except Exception:
            logging.exception("Silent except at 1773 - revisar contexto")

        resultado = {"actividad": nivel}
        self._log_debug(f"[MotorActividadHumana] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR PRESENCIA
# ------------------------------------------------------------

class MotorPresencia(MotorBase):
    """
    Infere presencia humana probable.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorPresencia] Analizando presencia")
        co2 = contexto.get("co2")
        ruido = contexto.get("ruido")

        presencia = None
        try:
            c = float(co2) if co2 is not None else 0.0
            r = float(ruido) if ruido is not None else 0.0
            if c >= 800 or r >= 45:
                presencia = "probable"
            else:
                presencia = "baja"
        except Exception:
            logging.exception("Silent except at 1803 - revisar contexto")

        resultado = {"presencia": presencia}
        self._log_debug(f"[MotorPresencia] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR CORRIENTES INTERNAS
# ------------------------------------------------------------

class MotorCorrientesInternas(MotorBase):
    """
    Infere corrientes internas por delta térmica y viento.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorCorrientesInternas] Analizando corrientes")
        t_int = contexto.get("temperatura_interior")
        t_ext = contexto.get("temperatura_exterior")
        viento = contexto.get("viento")

        corrientes = None
        try:
            if t_int is not None and t_ext is not None:
                delta = abs(float(t_int) - float(t_ext))
                v = float(viento) if viento is not None else 0.0
                if delta >= 6 and v >= 12:
                    corrientes = "probables"
                elif delta >= 4:
                    corrientes = "posibles"
                else:
                    corrientes = "bajas"
        except Exception:
            logging.exception("Silent except at 1837 - revisar contexto")

        resultado = {"corrientes": corrientes}
        self._log_debug(f"[MotorCorrientesInternas] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR PREDICCIÓN CORRIENTES INTERNAS FUTURAS
# ------------------------------------------------------------

class MotorPrediccionCorrientesFuturas(MotorBase):
    """
    Predice probabilidad de corrientes internas futuras.
    Factores: ΔT interior-exterior, viento exterior, estabilidad térmica y tendencia térmica.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorPrediccionCorrientesFuturas] Analizando corrientes futuras")
        t_int = contexto.get("temperatura_interior")
        t_ext = contexto.get("temperatura_exterior")
        viento = contexto.get("viento")
        estabilidad = contexto.get("estabilidad_termica", 50.0)
        tendencia_t = contexto.get("tendencia_temperatura", 0.0)

        riesgo = None
        etiqueta = None
        try:
            delta_t = abs(float(t_int) - float(t_ext)) if (t_int is not None and t_ext is not None) else 0.0
            v = float(viento) if viento is not None else 0.0
            est = float(estabilidad) if estabilidad is not None else 50.0
            trend = abs(float(tendencia_t)) if tendencia_t is not None else 0.0

            score = min(100.0, delta_t * 6 + v * 2 + (100 - est) * 0.3 + trend * 20)
            riesgo = round(score, 2)
            if score >= 70:
                etiqueta = "alta"
            elif score >= 40:
                etiqueta = "media"
            else:
                etiqueta = "baja"
        except Exception:
            logging.exception("Silent except at 1879 - revisar contexto")

        resultado = {
            "riesgo_corrientes_futuras": riesgo,
            "prediccion_corrientes_futuras": etiqueta,
        }
        self._log_debug(f"[MotorPrediccionCorrientesFuturas] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR ESTABILIDAD TÉRMICA FUTURA (IETF)
# ------------------------------------------------------------

class MotorEstabilidadTermicaFutura(MotorBase):
    """
    Predice estabilidad térmica futura (IETF) usando índices y delta térmica.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorEstabilidadTermicaFutura] Analizando estabilidad futura")
        ot = contexto.get("ot")
        ireav = contexto.get("ireav", 50.0)
        t_int = contexto.get("temperatura_interior")
        t_ext = contexto.get("temperatura_exterior")
        viento = contexto.get("viento", 0.0)

        valor = None
        try:
            delta_t = abs(float(t_int) - float(t_ext)) if t_int is not None and t_ext is not None else 0.0
            valor = indice_estabilidad_termica_futura(
                estabilidad_termica=float(ot) if ot is not None else 22.0,
                ireav=float(ireav) if ireav is not None else 50.0,
                delta_t=delta_t,
                viento=float(viento) if viento is not None else 0.0,
                historial_termico=50.0,
            )
        except Exception:
            logging.exception("Silent except at 1917 - revisar contexto")

        resultado = {"estabilidad_termica_futura": valor}
        self._log_debug(f"[MotorEstabilidadTermicaFutura] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR GOLPES DE PUERTA
# ------------------------------------------------------------

class MotorGolpesPuerta(MotorBase):
    """
    Evalúa probabilidad de golpes de puerta por viento/corrientes.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorGolpesPuerta] Analizando golpes de puerta")
        viento = contexto.get("viento")
        corrientes = contexto.get("corrientes_internas")

        riesgo = None
        try:
            v = float(viento) if viento is not None else 0.0
            if v >= 30:
                riesgo = "alto"
            elif v >= 18:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1948 - revisar contexto")

        if corrientes and corrientes in ("probables", "posibles"):
            riesgo = "medio" if riesgo == "bajo" else riesgo

        resultado = {"golpes_puerta": riesgo}
        self._log_debug(f"[MotorGolpesPuerta] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR RIESGO PLANTAS (HELADA)
# ------------------------------------------------------------

class MotorRiesgoPlantas(MotorBase):
    """
    Evalúa riesgo para plantas por helada local.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRiesgoPlantas] Analizando plantas")
        riesgo_helada = contexto.get("riesgo_helada_local")
        temp = contexto.get("temperatura_exterior")

        riesgo = None
        try:
            r = float(riesgo_helada) if riesgo_helada is not None else 0.0
            t = float(temp) if temp is not None else 10.0
            if r >= 60 or t <= 2:
                riesgo = "alto"
            elif r >= 35 or t <= 5:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 1983 - revisar contexto")

        resultado = {"riesgo_plantas": riesgo}
        self._log_debug(f"[MotorRiesgoPlantas] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR ROPA TENDIDA
# ------------------------------------------------------------

class MotorRopaTendida(MotorBase):
    """
    Riesgo de mojar ropa tendida por lluvia/tormenta.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorRopaTendida] Analizando ropa tendida")
        riesgo_lluvia = contexto.get("riesgo_lluvia")
        alerta_tormenta = contexto.get("alerta_tormenta")

        riesgo = None
        try:
            rl = float(riesgo_lluvia) if riesgo_lluvia is not None else 0.0
            at = float(alerta_tormenta) if alerta_tormenta is not None else 0.0
            score = max(rl, at)
            if score >= 70:
                riesgo = "alto"
            elif score >= 40:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 2016 - revisar contexto")

        resultado = {"riesgo_ropa_tendida": riesgo}
        self._log_debug(f"[MotorRopaTendida] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR VIENTO INCÓMODO PARA DORMIR
# ------------------------------------------------------------

class MotorVientoDormir(MotorBase):
    """
    Evalúa si el viento puede incomodar el sueño.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorVientoDormir] Analizando viento nocturno")
        viento = contexto.get("viento")
        riesgo = None
        try:
            v = float(viento) if viento is not None else 0.0
            if v >= 35:
                riesgo = "alto"
            elif v >= 20:
                riesgo = "medio"
            else:
                riesgo = "bajo"
        except Exception:
            logging.exception("Silent except at 2045 - revisar contexto")
        resultado = {"viento_dormir": riesgo}
        self._log_debug(f"[MotorVientoDormir] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR OLOR A CERRADO
# ------------------------------------------------------------

class MotorOlorCerrado(MotorBase):
    """
    Evalúa riesgo de olor a cerrado según humedad y tiempo sin ventilar.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorOlorCerrado] Analizando olor a cerrado")
        hr = contexto.get("humedad_interior")
        tiempo_sin_ventilar = contexto.get("tiempo_sin_ventilar_h", 0.0)

        riesgo = None
        try:
            if hr is not None:
                riesgo = indice_riesgo_olor_cerrado(float(hr), float(tiempo_sin_ventilar))
        except Exception:
            logging.exception("Silent except at 2070 - revisar contexto")

        resultado = {"riesgo_olor_cerrado": riesgo}
        self._log_debug(f"[MotorOlorCerrado] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR CONDENSACIÓN ARMARIOS
# ------------------------------------------------------------

class MotorCondensacionArmarios(MotorBase):
    """
    Evalúa condensación oculta en armarios.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorCondensacionArmarios] Analizando condensación armarios")
        irsh = contexto.get("irsh", 0.0)
        irin = contexto.get("irin", 0.0)
        ersf = contexto.get("ersf", 0.0)
        historial_nocturno = contexto.get("historial_nocturno_hr_alta", 0.0)

        irca = indice_condensacion_oculta_armarios(irsh, irin, ersf, historial_nocturno)
        resultado = {"riesgo_condensacion_armarios": irca}
        self._log_debug(f"[MotorCondensacionArmarios] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR SECADO DE ROPA
# ------------------------------------------------------------

class MotorSecadoRopa(MotorBase):
    """
    Estima si la ropa se secará bien según humedad, radiación y viento.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorSecadoRopa] Analizando secado de ropa")
        hr = contexto.get("humedad_exterior")
        rad = contexto.get("radiacion_solar")
        viento = contexto.get("viento")

        estado = None
        try:
            h = float(hr) if hr is not None else 60.0
            r = float(rad) if rad is not None else 0.0
            v = float(viento) if viento is not None else 0.0
            score = (100 - h) + (r / 10.0) + (v * 2.0)
            if score >= 90:
                estado = "excelente"
            elif score >= 60:
                estado = "bueno"
            elif score >= 40:
                estado = "regular"
            else:
                estado = "malo"
        except Exception:
            logging.exception("Silent except at 2129 - revisar contexto")

        resultado = {"secado_ropa": estado}
        self._log_debug(f"[MotorSecadoRopa] Resultado: {resultado}")
        return resultado


# ------------------------------------------------------------
# MOTOR LUZ/PERSIANAS
# ------------------------------------------------------------

class MotorPersianas(MotorBase):
    """
    Recomienda abrir/cerrar persianas según radiación y temperatura.
    """

    def analizar(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        self._log_debug("[MotorPersianas] Analizando persianas")
        rad = contexto.get("radiacion_solar")
        t_int = contexto.get("temperatura_interior")

        recomendacion = None
        try:
            r = float(rad) if rad is not None else 0.0
            t = float(t_int) if t_int is not None else 22.0
            if r > 600 and t > 26:
                recomendacion = "cerrar"
            elif r > 400 and t < 19:
                recomendacion = "abrir"
            else:
                recomendacion = "mantener"
        except Exception:
            logging.exception("Silent except at 2161 - revisar contexto")

        resultado = {"persianas": recomendacion}
        self._log_debug(f"[MotorPersianas] Resultado: {resultado}")
        return resultado

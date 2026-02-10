import logging
# ============================================================
# MÓDULO C — MOTOR DE RECOMENDACIONES UNIFICADO
# ============================================================

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

from core.prediction.prediction_engine import PredictionEngine

class UnifiedRecommendationEngine:
    """
    Motor central de recomendaciones.
    Combina sensores, índices y reglas simples para generar
    una recomendación general del sistema.
    """

    def __init__(self, system_core, indices_engine):
        self.system = system_core
        self.indices = indices_engine

    # --------------------------------------------------------
    # REGLA PRINCIPAL
    # --------------------------------------------------------
    def generar(self):
        """
        Produce una recomendación general basada en:
        - Sensación térmica
        - Riesgo de lluvia
        - Índice UV
        """

        datos = self.indices.obtener_todos()
        pred = PredictionEngine(self.system).predecir()


        st = datos.get("sensacion_termica")
        uv = datos.get("indice_uv")
        lluvia = datos.get("riesgo_lluvia")
        niebla = datos.get("riesgo_niebla")
        et = datos.get("evapotranspiracion")
        rayos = datos.get("contador_rayos")
        ultimo_rayo = datos.get("ultimo_rayo")
        suelo = datos.get("humedad_suelo")
        alerta_tormenta = datos.get("alerta_tormenta")
        alerta_calor = datos.get("alerta_calor_extremo")
        alerta_frio = datos.get("alerta_frio_extremo")
        alerta_polvo = datos.get("alerta_polvo")
        nubosidad = datos.get("nubosidad_estimada")
        cielo_astr = datos.get("indice_cielo_astronomico")
        cielo_obs = datos.get("cielo_observable_nocturno")
        cetreria = datos.get("indice_cetreria")
        calidad_ventilacion = datos.get("calidad_ventilacion_pct")
        ach = datos.get("ventilacion_ACH_renovaciones_h")

        motivos = {}

        def _val(x):
            return x.get("valor") if isinstance(x, dict) and "valor" in x else x

        def _to_float(x):
            try:
                return float(x)
            except Exception:
                return None

        def _get_first(keys, default=None):
            for k in keys:
                if k in datos and datos.get(k) is not None:
                    return _val(datos.get(k))
                if k in self.system.data and self.system.data.get(k) is not None:
                    return self.system.data.get(k)
                if k in (self.system.sensores or {}) and self.system.sensores.get(k) is not None:
                    return self.system.sensores.get(k)
            return default

        # Sensación térmica
        st_val = _val(st)
        if st_val is not None:
            if st_val < 10:
                motivos["sensacion_termica"] = "Hace frío, ponte abrigo."
                motivos["ropa_frio"] = "Ponte una chaqueta."
            elif st_val < 15:
                motivos["sensacion_termica"] = "Hace fresco, abrígate."
                motivos["ropa_frio"] = "Ponte una chaqueta."
            elif st_val > 28:
                motivos["sensacion_termica"] = "Hace calor, hidrátate y protégete del sol."

        # UV - Resolución de Diamante aplicada
        uv_val = _val(uv)
        if uv_val is not None:
            try:
                uv_val = float(uv_val)
                if uv_val > 6:
                    motivos["uv"] = f"Índice UV {uv_val:.2f if uv_val != int(uv_val) else int(uv_val)} alto, usa protección solar."
                    motivos["gorra_solar"] = "Ponte gorra o sombrero para el sol."
                elif uv_val > 3:
                    motivos["uv"] = f"Índice UV {uv_val:.2f if uv_val != int(uv_val) else int(uv_val)} moderado, considera protección."
                    motivos["gorra_solar"] = "Considera llevar gorra o sombrero."
            except Exception:
                if uv_val > 6:
                    motivos["uv"] = "Índice ultravioleta alto, usa protección solar."
                    motivos["gorra_solar"] = "Ponte gorra o sombrero para el sol."


        # Lluvia y redundancia: si ya está lloviendo, no mostrar probabilidad
        lluvia_val = _val(lluvia)
        lluvia_rate = _get_first([
            "lluvia_rate",
            "rainrate",
            "rainratein",
            "precipitacion_rate",
            "precipitacion_rate_mm_h",
            "lluvia_rate_actual",
        ], 0)
        lluvia_1h = self.system.sensores.get("lluvia_1h") or self.system.sensores.get("hourlyrainin")
        lluvia_24h = self.system.sensores.get("lluvia_24h") or self.system.sensores.get("dailyrainin")
        lluvia_acum = self.system.sensores.get("lluvia_acumulada") or self.system.sensores.get("rainin")
        try:
            lloviendo = float(lluvia_rate) > 0.2
        except Exception:
            lloviendo = False
        llovio_reciente = False
        for v in (lluvia_1h, lluvia_24h, lluvia_acum):
            try:
                if v is not None and float(v) > 0:
                    llovio_reciente = True
                    break
            except Exception:
                continue
        if lloviendo:
            motivos["lluvia"] = "Está lloviendo ahora mismo."
            motivos["paraguas"] = "Coge un paraguas."
        else:
            if lluvia_val is not None and lluvia_val > 60:
                motivos["lluvia"] = "Alta probabilidad de lluvia."
                motivos["paraguas"] = "Coge un paraguas."
            elif lluvia_val is not None and lluvia_val > 30:
                motivos["lluvia"] = "Riesgo moderado de lluvia."
                motivos["paraguas"] = "Coge un paraguas."
            elif llovio_reciente:
                motivos["lluvia"] = "Ha llovido recientemente."
                motivos["paraguas"] = "Coge un paraguas si sales."

            # Predicción de lluvia local (propia)
            prob_lluvia = pred.get("prob_lluvia")
            if isinstance(prob_lluvia, dict):
                prob_val = prob_lluvia.get("valor")
                if prob_val is not None and prob_val >= 70:
                    motivos["prob_lluvia"] = "Probabilidad alta de lluvia en breve."
                elif prob_val is not None and prob_val >= 50:
                    motivos["prob_lluvia"] = "Probabilidad moderada de lluvia en breve."

        # Niebla
        niebla_val = _val(niebla)
        if niebla_val is not None and niebla_val > 40:
            motivos["niebla"] = "Riesgo de niebla, precaución al conducir."

        # Evapotranspiración
        et_val = _val(et)
        if et_val is not None and et_val > 4:
            motivos["evapotranspiracion"] = "Evapotranspiración alta, riego recomendado."
        elif et_val is not None and et_val >= 3:
            motivos["evapotranspiracion"] = "Evapotranspiración moderada, considera regar si sigue subiendo."

        # Nubosidad estimada
        nub_val = _val(nubosidad)
        if nub_val is not None:
            if nub_val >= 80:
                motivos["sensacion_termica"] = "Hace frío, ponte abrigo."
                motivos["ropa_frio"] = "Ponte una chaqueta o abrigo."
                motivos["nubosidad"] = "Nubosidad alta, luz solar reducida."
                motivos["sensacion_termica"] = "Hace fresco, abrígate."
                motivos["ropa_frio"] = "Ponte una chaqueta."
        cielo_val = _val(cielo_astr)
        cielo_obs_val = _val(cielo_obs)
        if cielo_val is not None:
            if cielo_val >= 75:
                motivos["astronomia"] = "Noche excelente para observar el cielo."
            elif cielo_val >= 45:
                motivos["astronomia"] = "Noche regular para observación astronómica."
            else:
                motivos["astronomia"] = "Mala noche para observar el cielo."
        elif cielo_obs_val is not None and nub_val is not None:
            if cielo_obs_val >= 70 and nub_val < 40:
                motivos["astronomia"] = "Cielo bastante despejado para observar."

        # Cetrería local
        cetreria_val = _val(cetreria)
        if cetreria_val is not None:
            if cetreria_val >= 75:
                motivos["cetreria"] = "Condiciones excelentes para cetrería."
            elif cetreria_val >= 45:
                motivos["cetreria"] = "Condiciones aceptables para cetrería."
            else:
                motivos["cetreria"] = "Condiciones poco favorables para cetrería."

        # Rayos
        rayos_val = _val(rayos)
        if rayos_val is not None and rayos_val > 0:
            motivos["rayos"] = f"{rayos_val} rayos detectados recientemente."
            motivos["seguridad_rayos"] = "Evita exteriores y desconecta equipos sensibles."
        # Solo mostrar mensaje de último rayo si hay rayos recientes
        if ultimo_rayo and ultimo_rayo.get("valor") and (rayos_val is not None and rayos_val > 0):
            from datetime import datetime
            try:
                valor = ultimo_rayo["valor"]
                if isinstance(valor, (int, float)):
                    # Si es timestamp
                    if valor < 1e12:
                        valor = int(valor) * 1000
                    dt = datetime.fromtimestamp(int(valor) / 1000)
                    fecha_str = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    fecha_str = str(valor)
                motivos["ultimo_rayo"] = f"Último rayo registrado: {fecha_str}"
            except Exception:
                logging.exception("Silent except at 181 - revisar contexto")

        # Humedad de suelo
        suelo_val = _val(suelo)
        if suelo_val is not None:
            if suelo_val < 20:
                motivos["humedad_suelo"] = "Humedad del suelo muy baja, riego urgente."
            elif suelo_val < 40:
                motivos["humedad_suelo"] = "Humedad del suelo baja, considera regar."
            elif et_val is not None and et_val >= 3:
                motivos["humedad_suelo"] = "Humedad del suelo aceptable, pero la ET sugiere planificar riego."

        # Viento/rachas y alertas de rachas
        viento_val = _to_float(_get_first(["velocidad_viento", "viento", "wind_speed", "windspeed"], None))
        rachas_val = _to_float(_get_first(["viento_racha", "viento_ráfaga", "wind_gust", "racha", "gust", "velocidad_rachas"], None))
        alerta_rachas_score = _to_float(_get_first(["alerta_rachas_peligrosas_score", "alerta_rachas_peligrosas"], None))
        if alerta_rachas_score is not None and alerta_rachas_score >= 50:
            motivos["alerta_rachas"] = "Rachas peligrosas, asegura objetos y evita zonas expuestas."
        elif rachas_val is not None and rachas_val >= 15:
            motivos["rachas"] = "Rachas fuertes, asegúrate de objetos sueltos."
        elif viento_val is not None and viento_val >= 10:
            motivos["viento"] = "Viento fuerte, precaución al exterior."

        # Lluvia intensa / precipitación
        lluvia_rate = _to_float(_get_first([
            "lluvia_rate",
            "rainrate",
            "rainratein",
            "precipitacion_rate",
            "precipitacion_rate_mm_h",
            "lluvia_rate_actual",
        ], 0))
        if lluvia_rate is not None and lluvia_rate >= 5:
            motivos["lluvia_intensa"] = "Lluvia intensa, evita desplazamientos innecesarios."

        alerta_lluvia_score = _to_float(_get_first(["alerta_lluvia_intensa_score", "alerta_lluvia_intensa"], None))
        if alerta_lluvia_score is not None and alerta_lluvia_score >= 50:
            motivos["alerta_lluvia_intensa"] = "Alerta de lluvia intensa activa, evita zonas inundables."

        riego_suspendido = _get_first(["riego_suspendido_por_lluvia"], None)
        if riego_suspendido is True:
            motivos["riego_suspendido"] = "Riego suspendido por lluvia en curso."

        # Niebla/visibilidad
        visibilidad = _to_float(_get_first(["visibilidad", "visibilidad_gultepe_m", "visibilidad_local"], None))
        if visibilidad is not None and visibilidad < 1000:
            motivos["visibilidad_baja"] = "Visibilidad baja, conduce con mucha precaución."

        # Ventilación (si hay datos de calidad/ACH)
        calidad_vent_val = _val(calidad_ventilacion)
        ach_val = _val(ach)
        if calidad_vent_val is not None:
            try:
                if float(calidad_vent_val) < 40:
                    motivos["ventilacion"] = "Ventilación pobre, conviene ventilar."
                elif float(calidad_vent_val) < 70:
                    motivos["ventilacion"] = "Ventilación moderada, considera ventilar."
            except Exception:
                logging.exception("Silent except at 210 - revisar contexto")
        elif ach_val is not None:
            try:
                if float(ach_val) < 0.5:
                    motivos["ventilacion"] = "Baja renovación de aire, conviene ventilar."
            except Exception:
                logging.exception("Silent except at 217 - revisar contexto")

        # Alertas avanzadas
        if isinstance(alerta_tormenta, dict) and (alerta_tormenta.get("valor") or 0) >= 60:
            motivos["alerta_tormenta"] = "Riesgo alto de tormenta."
        if isinstance(alerta_calor, dict) and (alerta_calor.get("valor") or 0) >= 60:
            motivos["alerta_calor_extremo"] = "Riesgo alto de calor extremo."
        if isinstance(alerta_frio, dict) and (alerta_frio.get("valor") or 0) >= 60:
            motivos["alerta_frio_extremo"] = "Riesgo alto de frío extremo."
        if isinstance(alerta_polvo, dict) and (alerta_polvo.get("valor") or 0) >= 60:
            motivos["alerta_polvo"] = "Riesgo alto de polvo o mala calidad del aire."

        # Humedad alta/moho
        riesgo_moho = _to_float(_get_first(["riesgo_moho_pct", "indice_moho_vtt_M"], None))
        if riesgo_moho is not None and riesgo_moho >= 50:
            motivos["moho"] = "Riesgo de moho alto, ventila y reduce humedad interior."

        # Resumen de alertas/índices activos (genérico)
        try:
            max_resumen = 15
            resumen_count = 0
            resumen_alertas_riesgos = []
            for key, value in datos.items():
                if not isinstance(key, str):
                    continue
                if key.startswith("alerta_"):
                    valor = _to_float(_val(value))
                    if valor is not None:
                        resumen_alertas_riesgos.append(f"{key.replace('_', ' ')}: {valor:.0f}/100")
                        if valor >= 50:
                            motivos[f"{key}_activo"] = f"{key.replace('_', ' ')} activo ({valor:.0f}/100)."
                            resumen_count += 1
                if key.startswith("riesgo_"):
                    valor = _to_float(_val(value))
                    if valor is not None:
                        resumen_alertas_riesgos.append(f"{key.replace('_', ' ')}: {valor:.0f}/100")
                        if valor >= 60:
                            motivos[f"{key}_alto"] = f"{key.replace('_', ' ')} alto ({valor:.0f}/100)."
                            resumen_count += 1
                if resumen_count >= max_resumen:
                    break
            if resumen_alertas_riesgos:
                motivos["resumen_alertas_riesgos"] = " | ".join(resumen_alertas_riesgos)
        except Exception:
            logging.exception("Silent except at 235 - revisar contexto")

        # Resumen de predicciones (genérico)
        try:
            max_pred = 8
            pred_count = 0
            resumen_predicciones = []
            for key, value in (pred or {}).items():
                if not isinstance(key, str):
                    continue
                val = _val(value)
                val = val.get("valor") if isinstance(val, dict) else val
                num = _to_float(val)
                if num is None:
                    continue
                resumen_predicciones.append(f"{key.replace('_', ' ')}: {num:.2f}")
                if ("prob" in key or "lluv" in key or "tormenta" in key or "niebla" in key) and num >= 50:
                    motivos[f"pred_{key}"] = f"Predicción: {key.replace('_', ' ')} {num:.0f}%."
                    pred_count += 1
                if pred_count >= max_pred:
                    break
            if resumen_predicciones:
                motivos["resumen_predicciones"] = " | ".join(resumen_predicciones)
        except Exception:
            logging.exception("Silent except at 257 - revisar contexto")

        # Resumen de mediciones (sensores)
        try:
            resumen_sensores = []
            snapshot = dict(self.system.data) if isinstance(self.system.data, dict) else {}
            for k, v in (self.system.sensores or {}).items():
                if k not in snapshot and v is not None:
                    snapshot[k] = v
            for key, value in snapshot.items():
                if value is None:
                    continue
                num = _to_float(value)
                if num is None:
                    resumen_sensores.append(f"{key}: {value}")
                else:
                    resumen_sensores.append(f"{key}: {num:.2f}")
            if resumen_sensores:
                motivos["resumen_sensores"] = " | ".join(resumen_sensores)
        except Exception:
            logging.exception("Silent except at 285 - revisar contexto")

        # Recomendaciones completas desde alertas dinámicas (COJEO 6)
        try:
            from core.indices.soluciones_auditoría_v49 import generar_alertas_dinamicas

            temp_c = self.system.data.get("temperatura", self.system.sensores.get("temperatura", 15.0))
            humedad_rel = self.system.data.get("humedad", self.system.sensores.get("humedad", 50.0))
            presion_pa = self.system.data.get("presion_barometrica", self.system.sensores.get("presion", 101325.0))
            viento_ms = self.system.data.get("velocidad_viento", self.system.sensores.get("viento", 0.0))
            radiacion = self.system.data.get("radiacion_global", self.system.sensores.get("radiacion", 0.0))
            pm25 = self.system.data.get("pm25", 0.0)
            if presion_pa is None:
                presion_pa = 101325.0
            presion_hpa = presion_pa / 100.0 if presion_pa > 2000 else presion_pa

            historico_temp = getattr(self.system, "_historico_temp", None)
            historico_presion = getattr(self.system, "_historico_presion", None)

            alertas = generar_alertas_dinamicas(
                temp_c=float(temp_c),
                humedad_relativa=float(humedad_rel),
                presion_hpa=float(presion_hpa or 1013.25),
                viento_ms=float(viento_ms),
                radiacion_w_m2=float(radiacion),
                pm25=float(pm25),
                historico_temp=historico_temp,
                historico_presion=historico_presion,
            )

            for nombre_alerta, datos_alerta in alertas.items():
                recomendacion = datos_alerta.get("recomendacion")
                if recomendacion:
                    motivos[f"{nombre_alerta}_recomendacion"] = recomendacion
        except Exception:
            logging.exception("Silent except at 214 - revisar contexto")

        # Resultado final
        if len(motivos) > 0:
            estado_txt = " ".join(motivos.values())
            if len(motivos) > 12 or len(estado_txt) > 600:
                estado_txt = "Resumen completo disponible en motivos."
            return {
                "estado": estado_txt,
                "motivos": motivos
            }
        return {
            "estado": "Condiciones normales.",
            "motivos": {}
        }
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
        contexto = pred.get("contexto", {}) if isinstance(pred, dict) else {}
        es_noche = bool(contexto.get("es_noche", False))
        hora = float(contexto.get("hora", 0.0) or 0.0)


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

        motivos = {}

        # Sensación térmica
        st_val = st["valor"] if isinstance(st, dict) and "valor" in st else st
        if st_val is not None:
            if st_val < 10:
                motivos["sensacion_termica"] = "Hace frío, ponte abrigo."
                motivos["ropa_frio"] = "Ponte una chaqueta."
            elif st_val < 15:
                motivos["sensacion_termica"] = "Hace fresco, abrígate."
                motivos["ropa_frio"] = "Ponte una chaqueta."
            elif st_val > 28:
                motivos["sensacion_termica"] = "Hace calor, hidrátate y protégete del sol."

        # UV
        uv_val = uv["valor"] if isinstance(uv, dict) and "valor" in uv else uv
        if uv_val is not None and uv_val > 6:
            motivos["uv"] = "Índice ultravioleta alto, usa protección solar."


        # Lluvia y redundancia: si ya está lloviendo, no mostrar probabilidad
        lluvia_val = lluvia["valor"] if isinstance(lluvia, dict) and "valor" in lluvia else lluvia
        lluvia_rate = self.system.sensores.get("lluvia_rate") or self.system.sensores.get("rainratein") or 0
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
        niebla_val = niebla["valor"] if isinstance(niebla, dict) and "valor" in niebla else niebla
        if niebla_val is not None and niebla_val > 40:
            motivos["niebla"] = "Riesgo de niebla, precaución al conducir."

        # Evapotranspiración
        et_val = et["valor"] if isinstance(et, dict) and "valor" in et else et
        if et_val is not None and et_val > 4:
            motivos["evapotranspiracion"] = "Evapotranspiración alta, riego recomendado."

        # Nubosidad estimada
        nub_val = nubosidad["valor"] if isinstance(nubosidad, dict) and "valor" in nubosidad else nubosidad
        if nub_val is not None:
            if nub_val >= 80:
                motivos["nubosidad"] = "Cielo muy nublado." if es_noche else "Cielo muy nublado, baja radiación solar."
            elif nub_val >= 60:
                motivos["nubosidad"] = "Nubosidad alta." if es_noche else "Nubosidad alta, luz solar reducida."

        # Astronomía local — solo tiene sentido por la noche
        cielo_val = cielo_astr["valor"] if isinstance(cielo_astr, dict) and "valor" in cielo_astr else cielo_astr
        cielo_obs_val = cielo_obs["valor"] if isinstance(cielo_obs, dict) and "valor" in cielo_obs else cielo_obs
        if es_noche:
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

        # Cetrería local — no sugerir actividades diurnas si es de noche
        cetreria_val = cetreria["valor"] if isinstance(cetreria, dict) and "valor" in cetreria else cetreria
        if cetreria_val is not None:
            if es_noche:
                motivos["cetreria"] = "Es de noche — no recomendable programar cetrería ahora."
            else:
                if cetreria_val >= 75:
                    motivos["cetreria"] = "Condiciones excelentes para cetrería."
                elif cetreria_val >= 45:
                    motivos["cetreria"] = "Condiciones aceptables para cetrería."
                else:
                    motivos["cetreria"] = "Condiciones poco favorables para cetrería."

        # Rayos
        rayos_val = rayos["valor"] if isinstance(rayos, dict) and "valor" in rayos else rayos
        if rayos_val is not None and rayos_val > 0:
            motivos["rayos"] = f"{rayos_val} rayos detectados recientemente."
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
                pass

        # Humedad de suelo
        suelo_val = suelo["valor"] if isinstance(suelo, dict) and "valor" in suelo else suelo
        if suelo_val is not None:
            if suelo_val < 20:
                motivos["humedad_suelo"] = "Humedad del suelo muy baja, riego urgente."
            elif suelo_val < 40:
                motivos["humedad_suelo"] = "Humedad del suelo baja, considera regar."

        # Alertas avanzadas
        if isinstance(alerta_tormenta, dict) and (alerta_tormenta.get("valor") or 0) >= 60:
            motivos["alerta_tormenta"] = "Riesgo alto de tormenta."
        if isinstance(alerta_calor, dict) and (alerta_calor.get("valor") or 0) >= 60:
            motivos["alerta_calor_extremo"] = "Riesgo alto de calor extremo."
        if isinstance(alerta_frio, dict) and (alerta_frio.get("valor") or 0) >= 60:
            motivos["alerta_frio_extremo"] = "Riesgo alto de frío extremo."
        if isinstance(alerta_polvo, dict) and (alerta_polvo.get("valor") or 0) >= 60:
            motivos["alerta_polvo"] = "Riesgo alto de polvo o mala calidad del aire."

        # Resultado final
        if len(motivos) > 0:
            return {
                "estado": " ".join(motivos.values()),
                "motivos": motivos
            }
        return {
            "estado": "Condiciones normales.",
            "motivos": {}
        }
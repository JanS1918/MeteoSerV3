INDEX_CATALOG = {
    "riesgo_niebla": {
        "categoria": "meteorologia",
        "descripcion": "Riesgo de niebla por HR, T, radiación y viento",
        "sensores": ["temperatura", "humedad", "radiacion", "viento"],
        "tipo": "derivado"
    },
    "evapotranspiracion": {
        "categoria": "meteorologia",
        "descripcion": "Evapotranspiración simplificada (FAO PM)",
        "sensores": ["temperatura", "humedad", "radiacion", "viento"],
        "tipo": "derivado"
    },
    "humedad_suelo": {
        "categoria": "suelo",
        "descripcion": "Humedad del suelo medida por WH51",
        "sensores": ["wh51"],
        "tipo": "real"
    },
    "tendencia_humedad_suelo": {
        "categoria": "suelo",
        "descripcion": "Tendencia de humedad del suelo (%/h)",
        "sensores": ["wh51"],
        "tipo": "derivado"
    },
    "indice_sequia_suelo": {
        "categoria": "suelo",
        "descripcion": "Sequía del suelo por WH51 y ET",
        "sensores": ["wh51", "evapotranspiracion"],
        "tipo": "derivado"
    },
    "riesgo_lluvia": {
        "categoria": "meteorologia",
        "descripcion": "Riesgo de lluvia por HR y lluvia",
        "sensores": ["humedad", "lluvia"],
        "tipo": "hibrido"
    },
    "riesgo_micro_lluvias": {
        "categoria": "meteorologia",
        "descripcion": "Micro-lluvias por HR, tendencia presión y viento",
        "sensores": ["humedad", "presion", "viento"],
        "tipo": "derivado"
    },
    "riesgo_helada_local": {
        "categoria": "meteorologia",
        "descripcion": "Helada local por punto de rocío, T, radiación nocturna y viento",
        "sensores": ["temperatura", "humedad", "radiacion", "viento"],
        "tipo": "derivado"
    },
    "sensacion_termica": {
        "categoria": "meteorologia",
        "descripcion": "Sensación térmica simple",
        "sensores": ["temperatura", "viento"],
        "tipo": "derivado"
    },
    "sensacion_calor": {
        "categoria": "confort",
        "descripcion": "Heat Index (sensación de calor)",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "sensacion_frio": {
        "categoria": "confort",
        "descripcion": "Wind Chill (sensación de frío)",
        "sensores": ["temperatura", "viento"],
        "tipo": "derivado"
    },
    "wbgt": {
        "categoria": "confort",
        "descripcion": "WBGT aproximado (estrés térmico)",
        "sensores": ["temperatura", "humedad", "radiacion", "viento"],
        "tipo": "derivado"
    },
    # Humidex eliminado (EUTANASIA TÉCNICA 2026). Use `sensacion_calor`.
    "bulbo_humedo": {
        "categoria": "aire",
        "descripcion": "Temperatura de bulbo húmedo (aprox.)",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "humedad_absoluta": {
        "categoria": "aire",
        "descripcion": "Humedad absoluta (g/m3)",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "vpd": {
        "categoria": "aire",
        "descripcion": "Déficit de presión de vapor (kPa)",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "entalpia_aire": {
        "categoria": "aire",
        "descripcion": "Entalpía del aire húmedo (kJ/kg)",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "pmv": {
        "categoria": "confort",
        "descripcion": "PMV aproximado",
        "sensores": ["temperatura", "humedad", "viento"],
        "tipo": "derivado"
    },
    "ppd": {
        "categoria": "confort",
        "descripcion": "PPD aproximado",
        "sensores": ["temperatura", "humedad", "viento"],
        "tipo": "derivado"
    },
    "aqi_pm25": {
        "categoria": "aire",
        "descripcion": "AQI US EPA para PM2.5",
        "sensores": ["pm25"],
        "tipo": "derivado"
    },
    "sensacion_termica_compuesta": {
        "categoria": "confort",
        "descripcion": "Sensación térmica compuesta (fusión de índices)",
        "sensores": ["temperatura", "humedad", "viento", "radiacion"],
        "tipo": "derivado"
    },
    "calidad_aire_compuesta": {
        "categoria": "aire",
        "descripcion": "Calidad de aire compuesta (AQI+CO2+PM2.5)",
        "sensores": ["pm25", "co2"],
        "tipo": "derivado"
    },
    "ventilacion_compuesta": {
        "categoria": "aire",
        "descripcion": "Ventilación compuesta (fusión de indicadores)",
        "sensores": ["co2", "humedad_interior", "temperatura_interior"],
        "tipo": "derivado"
    },
    "punto_rocio": {
        "categoria": "meteorologia",
        "descripcion": "Punto de rocío por T y HR",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "indice_uv": {
        "categoria": "meteorologia",
        "descripcion": "Índice UV directo o derivado por radiación",
        "sensores": ["uv", "radiacion"],
        "tipo": "derivado"
    },
    "nubosidad": {
        "categoria": "meteorologia",
        "descripcion": "Radiación solar teórica astronómica",
        "sensores": ["latitud", "longitud"],
        "tipo": "derivado"
    },
    "nubosidad_estimada": {
        "categoria": "meteorologia",
        "descripcion": "Nubosidad estimada día/noche por radiación y atmósfera",
        "sensores": ["radiacion", "nubosidad", "temperatura", "humedad", "viento"],
        "tipo": "derivado"
    },
    "transparencia_atmosferica": {
        "categoria": "astronomia",
        "descripcion": "Transparencia atmosférica (sequedad + nubosidad + radiación)",
        "sensores": ["temperatura", "humedad", "nubosidad_estimada", "radiacion", "nubosidad"],
        "tipo": "derivado"
    },
    "riesgo_empaniamiento_optica": {
        "categoria": "astronomia",
        "descripcion": "Riesgo de empañamiento óptico por rocío, HR y viento",
        "sensores": ["temperatura", "humedad", "viento"],
        "tipo": "derivado"
    },
    "seeing_termico_basico": {
        "categoria": "astronomia",
        "descripcion": "Seeing térmico básico por variaciones de temperatura y viento",
        "sensores": ["temperatura", "viento"],
        "tipo": "derivado"
    },
    "fase_lunar": {
        "categoria": "astronomia",
        "descripcion": "Fase lunar estimada (iluminación %)",
        "sensores": [],
        "tipo": "derivado"
    },
    "cielo_observable_nocturno": {
        "categoria": "astronomia",
        "descripcion": "Cielo observable nocturno (calidad 0-100)",
        "sensores": ["nubosidad_estimada", "transparencia_atmosferica", "riesgo_niebla"],
        "tipo": "derivado"
    },
    "ventana_observacion_nocturna": {
        "categoria": "astronomia",
        "descripcion": "Horas útiles de observación nocturna",
        "sensores": ["amanecer", "atardecer", "cielo_observable_nocturno"],
        "tipo": "derivado"
    },
    "indice_cielo_astronomico": {
        "categoria": "astronomia",
        "descripcion": "Índice de cielo astronómico (0-100)",
        "sensores": ["cielo_observable_nocturno", "ventana_observacion_nocturna"],
        "tipo": "derivado"
    },
    "viento_cetreria": {
        "categoria": "cetreria",
        "descripcion": "Viento apto para cetrería (0-100)",
        "sensores": ["viento", "rachas"],
        "tipo": "derivado"
    },
    "visibilidad_terreno": {
        "categoria": "cetreria",
        "descripcion": "Visibilidad sobre terreno por nubosidad/HR/saturación",
        "sensores": ["temperatura", "humedad", "nubosidad_estimada"],
        "tipo": "derivado"
    },
    "termales_probabilidad": {
        "categoria": "cetreria",
        "descripcion": "Probabilidad de térmicas por radiación, nubosidad y variación térmica",
        "sensores": ["radiacion", "temperatura", "humedad", "viento", "nubosidad_estimada"],
        "tipo": "derivado"
    },
    "barro_campo": {
        "categoria": "cetreria",
        "descripcion": "Barro en campo por lluvia reciente y secado",
        "sensores": ["lluvia_1h", "lluvia_24h", "viento", "temperatura", "humedad"],
        "tipo": "derivado"
    },
    "confort_ave": {
        "categoria": "cetreria",
        "descripcion": "Confort térmico del ave por T, sensación, radiación y viento",
        "sensores": ["temperatura", "sensacion_termica", "radiacion", "viento"],
        "tipo": "derivado"
    },
    "indice_viento_cetreria": {
        "categoria": "cetreria",
        "descripcion": "Índice de viento para cetrería",
        "sensores": ["viento_cetreria"],
        "tipo": "derivado"
    },
    "indice_visibilidad_cetreria": {
        "categoria": "cetreria",
        "descripcion": "Índice de visibilidad para cetrería",
        "sensores": ["visibilidad_terreno"],
        "tipo": "derivado"
    },
    "indice_termales": {
        "categoria": "cetreria",
        "descripcion": "Índice de térmicas para vuelo",
        "sensores": ["termales_probabilidad"],
        "tipo": "derivado"
    },
    "indice_seguridad_vuelo": {
        "categoria": "cetreria",
        "descripcion": "Índice de seguridad de vuelo",
        "sensores": ["viento_cetreria", "visibilidad_terreno", "barro_campo", "termales_probabilidad"],
        "tipo": "derivado"
    },
    "indice_cetreria": {
        "categoria": "cetreria",
        "descripcion": "Índice final de condiciones para cetrería",
        "sensores": ["indice_seguridad_vuelo", "viento_cetreria", "visibilidad_terreno", "confort_ave"],
        "tipo": "derivado"
    },
    "confort_general": {
        "categoria": "confort",
        "descripcion": "Confort general por T_int, HR_int y CO2",
        "sensores": ["temperatura_interior", "humedad_interior", "co2"],
        "tipo": "derivado"
    },
    "bochorno_real": {
        "categoria": "confort",
        "descripcion": "Bochorno por T_int y HR_int",
        "sensores": ["temperatura_interior", "humedad_interior"],
        "tipo": "derivado"
    },
    "aire_seco": {
        "categoria": "confort",
        "descripcion": "Aire seco por HR_int",
        "sensores": ["humedad_interior"],
        "tipo": "derivado"
    },
    "aire_pegajoso": {
        "categoria": "confort",
        "descripcion": "Aire pegajoso por HR_int y T_int",
        "sensores": ["humedad_interior", "temperatura_interior"],
        "tipo": "derivado"
    },
    "frio_incomodo": {
        "categoria": "confort",
        "descripcion": "Frío incómodo por T_int",
        "sensores": ["temperatura_interior"],
        "tipo": "derivado"
    },
    "confort_nocturno": {
        "categoria": "confort",
        "descripcion": "Confort nocturno por T_int, ruido y luz",
        "sensores": ["temperatura_interior", "ruido", "luz"],
        "tipo": "derivado"
    },
    "aire_cargado": {
        "categoria": "aire",
        "descripcion": "Aire cargado por CO2 y tiempo sin ventilar",
        "sensores": ["co2"],
        "tipo": "derivado"
    },
    "aire_enrarecido": {
        "categoria": "aire",
        "descripcion": "Aire enrarecido por CO2 y PM2.5",
        "sensores": ["co2", "pm25"],
        "tipo": "derivado"
    },
    "ventilacion_ideal": {
        "categoria": "aire",
        "descripcion": "Ventilación ideal por CO2, HR_int y T_int",
        "sensores": ["co2", "humedad_interior", "temperatura_interior"],
        "tipo": "derivado"
    },
    "deshidratacion_ambiental": {
        "categoria": "aire",
        "descripcion": "Deshidratación ambiental por HR baja sostenida",
        "sensores": ["humedad_interior"],
        "tipo": "derivado"
    },
    "riesgo_moho": {
        "categoria": "edificio",
        "descripcion": "Riesgo de moho por HR alta sostenida y T_int",
        "sensores": ["humedad_interior", "temperatura_interior"],
        "tipo": "derivado"
    },
    "riesgo_olor_cerrado": {
        "categoria": "edificio",
        "descripcion": "Olor a cerrado por HR_int y CO2 alto",
        "sensores": ["humedad_interior", "co2"],
        "tipo": "derivado"
    },
    "salud_edificio": {
        "categoria": "edificio",
        "descripcion": "Salud del edificio por HR media y tiempo HR alta",
        "sensores": ["humedad_interior"],
        "tipo": "derivado"
    },
    "riesgo_condensacion_ventanas": {
        "categoria": "edificio",
        "descripcion": "Condensación en ventanas por T_int, HR_int y T_ext",
        "sensores": ["temperatura_interior", "humedad_interior", "temperatura"],
        "tipo": "derivado"
    },
    "alerta_tormenta": {
        "categoria": "alertas",
        "descripcion": "Alerta de tormenta por UV, radiación, presión y rayos",
        "sensores": ["uv", "radiacion", "presion", "rayos"],
        "tipo": "derivado"
    },
    "alerta_calor_extremo": {
        "categoria": "alertas",
        "descripcion": "Alerta de calor extremo",
        "sensores": ["temperatura", "humedad", "uv"],
        "tipo": "derivado"
    },
    "alerta_frio_extremo": {
        "categoria": "alertas",
        "descripcion": "Alerta de frío extremo",
        "sensores": ["temperatura", "viento", "humedad"],
        "tipo": "derivado"
    },
    "alerta_polvo": {
        "categoria": "alertas",
        "descripcion": "Alerta de polvo por PM2.5 y viento",
        "sensores": ["pm25", "viento"],
        "tipo": "derivado"
    },
    "tendencia_temperatura": {
        "categoria": "tendencias",
        "descripcion": "Tendencia T_ext desde histórico real",
        "sensores": ["temperatura"],
        "tipo": "derivado"
    },
    "tendencia_humedad": {
        "categoria": "tendencias",
        "descripcion": "Tendencia HR_ext desde histórico real",
        "sensores": ["humedad"],
        "tipo": "derivado"
    },
    "tendencia_presion": {
        "categoria": "tendencias",
        "descripcion": "Tendencia presión desde histórico real",
        "sensores": ["presion"],
        "tipo": "derivado"
    },
    "estabilidad_termica": {
        "categoria": "tendencias",
        "descripcion": "Estabilidad térmica según tendencia de T_ext",
        "sensores": ["temperatura"],
        "tipo": "derivado"
    },
    "riesgo_rachas_peligrosas": {
        "categoria": "meteorologia",
        "descripcion": "Riesgo de rachas peligrosas por viento exterior",
        "sensores": ["viento"],
        "tipo": "derivado"
    },
    "viento_incomodo_dormir": {
        "categoria": "meteorologia",
        "descripcion": "Viento incómodo para dormir",
        "sensores": ["viento"],
        "tipo": "derivado"
    },
    "visibilidad_local": {
        "categoria": "meteorologia",
        "descripcion": "Visibilidad local estimada por riesgo de niebla",
        "sensores": ["humedad", "temperatura", "radiacion", "viento"],
        "tipo": "derivado"
    },
    "estres_termico_exterior": {
        "categoria": "meteorologia",
        "descripcion": "Estrés térmico exterior por T_ext y HR_ext",
        "sensores": ["temperatura", "humedad"],
        "tipo": "derivado"
    },
    "inversion_termica": {
        "categoria": "meteorologia",
        "descripcion": "Inversión térmica local por T_int vs T_ext",
        "sensores": ["temperatura", "temperatura_interior"],
        "tipo": "derivado"
    },
    "micro_rafagas": {
        "categoria": "meteorologia",
        "descripcion": "Micro-ráfagas por cambio rápido de viento",
        "sensores": ["viento"],
        "tipo": "derivado"
    },
    "niebla_adveccion": {
        "categoria": "meteorologia",
        "descripcion": "Niebla de advección por HR alta y viento",
        "sensores": ["humedad", "viento"],
        "tipo": "derivado"
    },
    # ========================================================================
    # NUEVOS DOMINIOS v8 (Febrero 2026)
    # ========================================================================
    
    # RIEGO - Índices agrícolas
    "balance_hidrico_neto": {
        "categoria": "riego",
        "descripcion": "Balance hídrico neto (Lluvia - ET0 - Escorrentía - Infiltración)",
        "sensores": ["lluvia", "temperatura", "radiacion", "humedad", "viento"],
        "tipo": "derivado",
        "unidad": "mm",
        "rango": [-50, 100],
        "fuente": "FAO-56 (Allen et al., 1998)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "et0_fao56": {
        "categoria": "riego",
        "descripcion": "Evapotranspiración de referencia FAO-56 (Penman-Monteith)",
        "sensores": ["temperatura", "radiacion", "humedad", "viento"],
        "tipo": "derivado",
        "unidad": "mm/día",
        "rango": [0, 10],
        "fuente": "FAO-56 Penman-Monteith (Allen et al., 1998)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "estres_cultivo": {
        "categoria": "riego",
        "descripcion": "Factor de estrés hídrico del cultivo (0-1, parametrizable por cultivo)",
        "sensores": ["humedad_suelo", "evapotranspiracion", "temperatura"],
        "tipo": "derivado",
        "unidad": "ratio",
        "rango": [0, 1],
        "fuente": "FAO-56",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "disponibilidad_agua_cultivable": {
        "categoria": "riego",
        "descripcion": "Días hasta sequedad del suelo (proyección 7 días)",
        "sensores": ["humedad_suelo", "evapotranspiracion", "temperatura"],
        "tipo": "derivado",
        "unidad": "días",
        "rango": [0, 30],
        "fuente": "FAO-56",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "eficiencia_infiltracion": {
        "categoria": "riego",
        "descripcion": "Ratio infiltración/escorrentía (Green-Ampt), 0-100%",
        "sensores": ["lluvia", "humedad_suelo", "temperatura"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "Green-Ampt (1911)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "indice_riego_sintetico": {
        "categoria": "riego",
        "descripcion": "Índice sintético riego v2.0 (0-100, >60=riego recomendado)",
        "sensores": ["lluvia", "temperatura", "radiacion", "humedad", "humedad_suelo"],
        "tipo": "sintético",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "FAO-56 (Allen et al., 1998)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    
    # ASTRONOMÍA (v2.0) - Observación astronómica
    "horas_luz_diarias": {
        "categoria": "astronomia",
        "descripcion": "Duración del día solar (horas luz) - NREL SPA",
        "sensores": ["latitud", "longitud", "dia", "mes", "anio"],
        "tipo": "derivado",
        "unidad": "horas",
        "rango": [0, 24],
        "fuente": "NREL SPA (Reda & Andreas, 2003)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "observacion_nocturna": {
        "categoria": "astronomia",
        "descripcion": "Calidad cielo nocturno (0-100) - función elevación solar, bruma, humedad",
        "sensores": ["elevacion_solar", "radiacion", "visibilidad_km", "humedad"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "Astronómica WMO/OMS",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "amplitud_termica_diaria": {
        "categoria": "astronomia",
        "descripcion": "Variación de temperatura esperada (ΔT dia-noche)",
        "sensores": ["radiacion", "nubosidad_estimada", "altitud"],
        "tipo": "derivado",
        "unidad": "°C",
        "rango": [0, 30],
        "fuente": "NREL SPA",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "clearness_index_kt": {
        "categoria": "astronomia",
        "descripcion": "Índice de claridad atmosférica (Angström), 0=nublado, 1=despejado",
        "sensores": ["radiacion", "latitud", "dia"],
        "tipo": "derivado",
        "unidad": "ratio",
        "rango": [0, 1],
        "fuente": "NREL SPA",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "visibilidad_noche": {
        "categoria": "astronomia",
        "descripcion": "Magnitud estelar visible (2-6 escala), función bruma y humedad",
        "sensores": ["visibilidad_km", "humedad"],
        "tipo": "derivado",
        "unidad": "mag",
        "rango": [2, 6],
        "fuente": "Astronómica estándar",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "fase_lunar_factor": {
        "categoria": "astronomia",
        "descripcion": "Factor de iluminación lunar (0-1)",
        "sensores": [],
        "tipo": "derivado",
        "unidad": "ratio",
        "rango": [0, 1],
        "fuente": "Efemérides astronómicas",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "indice_astronomia_sintetico": {
        "categoria": "astronomia",
        "descripcion": "Índice sintético astronomía v2.0 (0-100, >70=excelente para observar)",
        "sensores": ["elevacion_solar", "radiacion", "visibilidad_km", "humedad"],
        "tipo": "sintético",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "NREL SPA (Reda & Andreas, 2003)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    
    # SALUD - Salud pública y riesgos ambientales
    "uvi_personal": {
        "categoria": "salud",
        "descripcion": "Exposición UV personalizada OMS/WMO (0-16+, penalizado hora solar)",
        "sensores": ["uv", "radiacion", "hora", "dia", "mes"],
        "tipo": "derivado",
        "unidad": "UVI",
        "rango": [0, 16],
        "fuente": "OMS/WMO UV Index (Vanicek et al., 2000)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "calor_extremo": {
        "categoria": "salud",
        "descripcion": "Probabilidad golpe de calor (0-100), función T, HR, radiación",
        "sensores": ["temperatura", "humedad", "radiacion"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "NOAA/NWS Heat Index",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "frio_extremo": {
        "categoria": "salud",
        "descripcion": "Probabilidad hipotermia/congelación (0-100), wind chill",
        "sensores": ["temperatura", "viento"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "NOAA Wind Chill Index",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "helada_riesgo": {
        "categoria": "salud",
        "descripcion": "Riesgo helada cultivos/infraestructura (Yates-McLean)",
        "sensores": ["punto_rocio", "temperatura", "viento"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "Yates-McLean Frost Model",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "aire_interior": {
        "categoria": "salud",
        "descripcion": "Calidad aire interior estimada (0-100), proxy CO2 por HR",
        "sensores": ["humedad", "punto_rocio"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "ASHRAE 62.1/160",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "aire_exterior": {
        "categoria": "salud",
        "descripcion": "Calidad aire exterior (0-100), proxy contaminación por visibilidad",
        "sensores": ["visibilidad_km"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "EPA AQI/WMO guidelines",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "indice_salud_sintetico": {
        "categoria": "salud",
        "descripcion": "Índice sintético salud v2.0 (0-100, >70=día saludable)",
        "sensores": ["temperatura", "humedad", "radiacion", "uv", "viento", "visibilidad_km"],
        "tipo": "sintético",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "OMS/WMO Guidelines",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    
    # HIDROLOGÍA - Ciclos hídricos y recursos acuáticos
    "infiltracion_mm_h": {
        "categoria": "hidrologia",
        "descripcion": "Tasa infiltración Green-Ampt (mm/h), función lluvia y suelo",
        "sensores": ["lluvia", "humedad_suelo", "temperatura"],
        "tipo": "derivado",
        "unidad": "mm/h",
        "rango": [0, 100],
        "fuente": "Green-Ampt (1911)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "escorrentia_superficial": {
        "categoria": "hidrologia",
        "descripcion": "Flujo agua en superficie (0-100), función lluvia e infiltración",
        "sensores": ["lluvia", "infiltracion_mm_h"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "Hidrología SCS/WMO",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "spi_indice": {
        "categoria": "hidrologia",
        "descripcion": "Índice Precipitación Estandarizado WMO (-2 a +2)",
        "sensores": ["lluvia", "lluvia_24h"],
        "tipo": "derivado",
        "unidad": "std",
        "rango": [-3, 3],
        "fuente": "WMO SPI (McKee et al., 1993)",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "humedad_suelo_tendencia": {
        "categoria": "hidrologia",
        "descripcion": "Tendencia humedad suelo 0-100, proyección 7 días",
        "sensores": ["humedad_suelo", "lluvia", "evapotranspiracion"],
        "tipo": "derivado",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "FAO-56",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    "indice_hidrologia_sintetico": {
        "categoria": "hidrologia",
        "descripcion": "Índice sintético hidrología v2.0 (0-100, >60=riesgo inundación, <40=sequia)",
        "sensores": ["lluvia", "humedad_suelo", "escorrentia_superficial"],
        "tipo": "sintético",
        "unidad": "%",
        "rango": [0, 100],
        "fuente": "WMO SPI + FAO-56",
        "version": "2.0",
        "fecha_ultima_actualizacion": "2026-02-10"
    },
    
    # RECOMENDACIONES - Capa de síntesis y recomendaciones inteligentes
    "rec_cetreria_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación cetrería (SÍ/NO)",
        "sensores": ["indice_cetreria_sintetico"],
        "tipo": "sintético"
    },
    "rec_cetreria_indice": {
        "categoria": "recomendaciones",
        "descripcion": "Índice cetrería para recomendación (0-100)",
        "sensores": ["indice_cetreria_sintetico"],
        "tipo": "sintético"
    },
    "rec_cetreria_confianza": {
        "categoria": "recomendaciones",
        "descripcion": "Confianza recomendación cetrería (0-100%)",
        "sensores": ["sensores_disponibles"],
        "tipo": "sintético"
    },
    "rec_lluvia_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación lluvia (SÍ/NO)",
        "sensores": ["indice_lluvia_sintetico"],
        "tipo": "sintético"
    },
    "rec_deporte_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación deporte (SÍ/NO)",
        "sensores": ["indice_deporte_sintetico"],
        "tipo": "sintético"
    },
    "rec_confort_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación confort (SÍ/NO)",
        "sensores": ["indice_confort_sintetico"],
        "tipo": "sintético"
    },
    "rec_riego_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación riego (SÍ/NO)",
        "sensores": ["indice_riego_sintetico"],
        "tipo": "sintético"
    },
    "rec_astronomia_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación astronomía (SÍ/NO)",
        "sensores": ["indice_astronomia_sintetico"],
        "tipo": "sintético"
    },
    "rec_salud_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación salud (SÍ/NO)",
        "sensores": ["indice_salud_sintetico"],
        "tipo": "sintético"
    },
    "rec_hidrologia_respuesta": {
        "categoria": "recomendaciones",
        "descripcion": "Recomendación hidrología (SÍ/NO)",
        "sensores": ["indice_hidrologia_sintetico"],
        "tipo": "sintético"
    }
}

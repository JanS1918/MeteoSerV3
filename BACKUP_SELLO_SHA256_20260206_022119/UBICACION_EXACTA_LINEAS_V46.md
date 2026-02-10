# 📍 UBICACIÓN EXACTA DE CADA CAMBIO V46.0

**Archivo principal**: `core/system/bus_expander.py` (6652 líneas)

---

## 🛑 WATCHDOG DATOS CADUCADOS

**Ubicación**: Líneas 2227-2250 (INICIO de función)  
**Función**: `_publish_predicciones_probabilidades()`

```python
2227: async def _publish_predicciones_probabilidades(self):
2228:     """Publica probabilidades y predicciones basadas en tendencias."""
2229:     try:
2230:         # 🛑 WATCHDOG DATOS CADUCADOS: Bloquear si datos >300s sin actualizar
2231:         import time
2232:         timestamp_datos = self.system.data.get("timestamp", None)
2233:         ahora = time.time()
2234:         
2235:         if timestamp_datos is not None:
2236:             segundos_sin_actualizar = ahora - float(timestamp_datos)
2237:             if segundos_sin_actualizar > 300:  # > 5 minutos
2238:                 self.bus.publicar("datos_caducados", True, "bool")
2239:                 self.bus.publicar("segundos_sin_actualizar", int(segundos_sin_actualizar), "s")
2240:                 self.logger.warning(f"⚠️ DATOS CADUCADOS: {segundos_sin_actualizar:.0f}s sin actualizar.")
2241:                 return  # ← BLOQUEA TODO
2242:             else:
2243:                 self.bus.publicar("datos_caducados", False, "bool")
2244:                 self.bus.publicar("segundos_sin_actualizar", int(segundos_sin_actualizar), "s")
2245:         else:
2246:             self.bus.publicar("datos_caducados", None, "bool")
2247:             self.bus.publicar("segundos_sin_actualizar", None, "s")
```

✅ **Estado**: IMPLEMENTADO  
✅ **Publicaciones**: `datos_caducados`, `segundos_sin_actualizar`

---

## 🔬 IMPORTS + PRE-CÁLCULOS

**Ubicación**: Líneas 2248-2310  
**Qué hace**: Importa módulos V46.0 y calcula Qnet + presión (reutilizable)

```python
2248:     temp_c = self.system.data.get("temperatura", 15.0)
...
2248-2276: [Imports de módulos, lectura de datos, CAPE/LI/SI/LCL]
2276-2310: [Pre-cálculo de Qnet (Brunt-Monteith) y tendencia presión]
```

✅ **Qnet**: Se usa en Stoelinga, Sundqvist, Deardorff, Probabilidad helada

---

## ⛈️ VGP + BRN + STP (Severidad Tormentas)

**Ubicación**: Líneas 2328-2345  
**Función**: Calcula rotación potencial y tipo de tormenta

```python
2328:         viento_dir = self.system.data.get("direccion_viento", 0.0)
2329:         sev = calcular_severidad_tormenta_vgp_brn(
2330:             temperatura_c=temp_c,
2331:             humedad_relativa=humedad,
2332:             presion_hpa=presion_hpa,
2333:             viento_ms=viento,
2334:             viento_dir_deg=viento_dir,     # ← NUEVO
2335:             cape_jkg=cape_jkg,
2336:             lcl_m=lcl_m,
2337:             cizalladura_0_6km_ms=None,    # ← Para mejorar con Gryning
2338:         )
2339:         prob_tormenta = max(0.0, min(100.0, float(sev.get("riesgo_tormenta_severa_pct", 0.0))))
2340:         self.bus.publicar("vgp", sev.get("vgp"), "adimensional")
2341:         self.bus.publicar("brn", sev.get("brn"), "adimensional")
2342:         self.bus.publicar("srh", sev.get("srh_m2s2"), "m²/s²")
2343:         self.bus.publicar("stp", sev.get("stp"), "adimensional")
2344:         self.bus.publicar("tipo_tormenta", sev.get("tipo_tormenta"), "string")
```

✅ **Estado**: INTEGRADO  
✅ **Publicaciones**: `vgp`, `brn`, `srh`, `stp`, `tipo_tormenta`

---

## ☔ SUNDQVIST (Probabilidad Lluvia) + 🌧️ LLOVIZNA

**Ubicación**: Líneas 2351-2386  
**Función**: Calcula PoP + flag de llovizna

```python
2351:         sundq = calcular_probabilidad_lluvia_sundqvist(
2352:             temperatura_c=temp_c,
2353:             humedad_relativa=humedad,
2354:             presion_hpa=presion_hpa,
2355:             qc=micro.get("qc_gkg", 0.0),        # ← Thompson
2356:             qr=micro.get("qr_gkg", 0.0),        # ← Thompson
2357:             tendencia_presion_hpa_h=tendencia_presion,
2358:             radiacion_neta_wm2=qnet_val,
2359:         )
2360:         prob_lluvia = max(0.0, min(100.0, float(sundq.get("prob_lluvia_pct", 0.0))))
2361:         self.bus.publicar("calor_latente_lluvia_wm2", sundq.get("calor_latente_wm2"), "W/m²")
2362:         self.bus.publicar("tasa_condensacion_lluvia_gkg_h", sundq.get("tasa_condensacion_gkg_h"), "g/kg/h")
2363:         self.bus.publicar("eficiencia_precipitacion", sundq.get("eficiencia_precipitacion"), "0-1")
2364:
2365:         # 🌧️ FLAG LLOVIZNA PROBABLE: Thompson detecta agua pero pluviómetro no la registra
2366:         qr_detectado = micro.get("qr_gkg", 0.0)
2367:         lluvia_actual = self.system.data.get("lluvia", 0.0)  # Tasa actual en mm/h
2368:         llovizna_probable = (qr_detectado > 0.01) and (lluvia_actual < 0.1)
2369:         self.bus.publicar("llovizna_probable", llovizna_probable, "bool")
2370:         if llovizna_probable and prob_lluvia > 30:
2371:             self.bus.publicar("senal_microprecipitacion_llovizna", True, "bool")
2372:         else:
2373:             self.bus.publicar("senal_microprecipitacion_llovizna", False, "bool")
2374:
2375:         if learning:
2376:             ...
```

✅ **Estado**: INTEGRADO + NUEVA FUNCIONALIDAD  
✅ **Publicaciones**: `calor_latente_lluvia_wm2`, `tasa_condensacion_lluvia_gkg_h`, `eficiencia_precipitacion`, `llovizna_probable`, `senal_microprecipitacion_llovizna`

---

## 🌡️ DEARDORFF (Mínimas) + 🪨 SOBERANÍA SUELO

**Ubicación**: Líneas 2388-2430  
**Función**: Calcula temperatura mínima con inercia térmica real

```python
2395:         lluvia_24h = self.system.data.get("lluvia_24h", 0.0)
2396:         
2397:         # 🪨 SOBERANÍA DEL SUELO: Usar tipo desde config, o fallback para Argentona
2398:         tipo_suelo = None
2399:         try:
2400:             tipo_suelo = self.system.config.get("soil_type")  # ¿Especificado por usuario?
2401:         except:
2402:             pass
2403:         
2404:         if not tipo_suelo:
2405:             try:
2406:                 lat = self.system.data.get("latitude", 41.55)
2406:                 lon = self.system.data.get("longitude", 2.38)
2407:                 if 41.4 < lat < 41.6 and 2.3 < lon < 2.5:  # Bounding box Argentona
2408:                     tipo_suelo = "arena_pura"  # Granito del Maresme
2409:             except:
2410:                 tipo_suelo = "arena_pura"
2411:         
2412:         deard = calcular_temperatura_minima_deardorff(
2413:             temperatura_actual_c=temp_c,
2414:             temperatura_suelo_profundo_c=None,
2415:             radiacion_neta_wm2=qnet_val if qnet_val is not None else -70.0,
2416:             viento_ms=viento_ms,
2417:             humedad_relativa=humedad,
2418:             tipo_suelo=tipo_suelo,                # ← REAL vs constante
2419:             horas_hasta_amanecer=8.0,
2420:             lluvia_ultimas_24h_mm=lluvia_24h,
2421:         )
2422:         self.bus.publicar("tipo_suelo_usado_deardorff", tipo_suelo, "string")  # DEBUG
2423:         self.bus.publicar("minima_temperatura_esperada_noche", deard.get("temperatura_minima_c"), "°C")
2424:         self.bus.publicar("temperatura_suelo_profundo_estimada", deard.get("temperatura_suelo_profundo_c"), "°C")
2425:         self.bus.publicar("flujo_calor_suelo", deard.get("flujo_calor_suelo_wm2"), "W/m²")
```

✅ **Estado**: INTEGRADO + NUEVA FUNCIONALIDAD  
✅ **Publicaciones**: `tipo_suelo_usado_deardorff`, `minima_temperatura_esperada_noche`, `temperatura_suelo_profundo_estimada`, `flujo_calor_suelo`

---

## 🌫️ STOELINGA-WARNER (Visibilidad)

**Ubicación**: Líneas 2476-2530  
**Función**: Calcula extinción de luz por gotas + riesgo niebla

```python
2476:         # SECCIÓN 13: CALIDAD DEL AIRE Y VISIBILIDAD
2477:         ...
2490:         visib_result = visibilidad_desde_sensores(
2491:             temperatura_c=temp_c,
2492:             humedad_relativa=humedad,
2493:             qc_gkg=micro.get("qc_gkg"),         # ← Thompson
2494:             qr_gkg=micro.get("qr_gkg"),         # ← Thompson
2495:             pm25=pm25,
2496:             presion_hpa=presion_hpa,
2497:         )
2498:         
2499:         self.bus.publicar("visibilidad_m", visib_result.get("visibilidad_m"), "m")
2500:         self.bus.publicar("visibilidad_km", visib_result.get("visibilidad_km"), "km")
2501:         self.bus.publicar("riesgo_niebla_0_100", visib_result.get("riesgo_niebla"), "0-100")
2502:         self.bus.publicar("lwc_cloud", visib_result.get("lwc_cloud"), "g/m³")
2503:         self.bus.publicar("lwc_rain", visib_result.get("lwc_rain"), "g/m³")
```

✅ **Estado**: INTEGRADO  
✅ **Publicaciones**: `visibilidad_m`, `visibilidad_km`, `riesgo_niebla_0_100`, `lwc_cloud`, `lwc_rain`

---

## 📊 RESUMEN DE CAMBIOS

| Líneas | Componente | Tipo | Status |
|--------|-----------|------|--------|
| 2227-2250 | Watchdog Datos | NUEVO | ✅ |
| 2276-2310 | Pre-cálculos Qnet | MEJORADO | ✅ |
| 2328-2345 | VGP+BRN Severidad | INTEGRADO | ✅ |
| 2351-2386 | Sundqvist + Llovizna | INTEGRADO + NUEVO | ✅ |
| 2388-2430 | Deardorff + Soberanía | INTEGRADO + NUEVO | ✅ |
| 2476-2530 | Stoelinga Visibilidad | INTEGRADO | ✅ |

**Total líneas nuevas/modificadas**: ~200  
**Errores de sintaxis**: 0 ✅

---

## 🔍 BUSCAR EN EDITOR

Para encontrar rápidamente cada sección:

```
Ctrl+G → Ir a línea 2227  (Watchdog)
Ctrl+G → Ir a línea 2328  (VGP+BRN)
Ctrl+G → Ir a línea 2351  (Sundqvist + Llovizna)
Ctrl+G → Ir a línea 2388  (Deardorff + Soberanía)
Ctrl+G → Ir a línea 2476  (Stoelinga)
```

O buscar (Ctrl+F):
```
"WATCHDOG DATOS CADUCADOS"
"VGP + BRN + STP"
"FLAG LLOVIZNA PROBABLE"
"SOBERANÍA DEL SUELO"
"STOELINGA-WARNER"
```

---

## ✅ CÓMO VERIFICAR QUE FUNCIONAN

```python
# En terminal
cd c:\Users\kioko\Desktop\MeteoSerV3
python -c "from core.system.bus_expander import BusExpander; print('✅ Imports OK')"

# O al iniciar servidor
uvicorn main_asgi:app --host 0.0.0.0 --port 8080

# Luego en navegador (si tienes endpoint)
http://localhost:8080/bus/datos?key=datos_caducados
http://localhost:8080/bus/datos?key=llovizna_probable
http://localhost:8080/bus/datos?key=tipo_suelo_usado_deardorff
```


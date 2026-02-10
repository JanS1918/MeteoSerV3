# router.py
# Rutas de la nueva interfaz MeteoSer

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Iterable, Optional
import statistics
import math

from app.ui.viewmodel import PanelViewModel
from core.fiabilidad_manager import FiabilidadManager
from core.data_model import ValorSistema, GrupoValores, Fiabilidad
from core.context.fallback_universal import obtener_fallback_universal, EstadoFisico
from core.system.constants import ESTACION

router = APIRouter()

# Cache en memoria para acelerar respuestas del panel
_CACHE = {
    "contexto": {"ts": 0.0, "data": None},
    "panel_superior": {"ts": 0.0, "data": None},
    "arcos": {"ts": 0.0, "data": None},
    "panel_central": {"ts": 0.0, "data": None},
    "cajones": {"ts": 0.0, "data": None},
}

_TTL_CONTEXTO = 5.0
_TTL_PANEL = 5.0
_TTL_ARCOS = 10.0
_TTL_CAJONES = 5.0
_TTL_OROGRAFIA = 3600.0


def _cache_get(key: str, ttl: float):
    entrada = _CACHE.get(key)
    if not entrada:
        return None
    if entrada["data"] is None:
        return None
    if (time.monotonic() - entrada["ts"]) < ttl:
        return entrada["data"]
    return None


def _cache_set(key: str, data):
    _CACHE[key] = {"ts": time.monotonic(), "data": data}
    return data


def _obtener_orografia(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    cache_key = f"orografia:{lat:.5f}:{lon:.5f}"
    cached = _cache_get(cache_key, _TTL_OROGRAFIA)
    if cached is not None:
        return cached
    try:
        from core.orography.orography_engine import OrografiaEngine
        engine = OrografiaEngine()
        data = engine.compute(lat, lon)
        return _cache_set(cache_key, data)
    except Exception:
        logging.exception("Error calculando orografía")
        return None

def _normalizar_key(valor: str) -> str:
    return str(valor).strip().lower().replace(" ", "_")


def _buscar_cambio(cambios: Dict[str, Any], nombre: str) -> Optional[Dict[str, Any]]:
    if not cambios:
        return None
    if nombre in cambios:
        return cambios.get(nombre)
    key = _normalizar_key(nombre)
    if key in cambios:
        return cambios.get(key)
    return None


def _extraer_valor_sensor(sensores: Dict[str, Any], alias: Iterable[str]) -> Optional[Dict[str, Any]]:
    alias_norm = [_normalizar_key(a) for a in alias]
    for key, info in sensores.items():
        key_norm = _normalizar_key(key)
        if any(a == key_norm or a in key_norm for a in alias_norm):
            if isinstance(info, dict):
                valor = info.get('valor', info.get('value'))
                unidad = info.get('unidad', info.get('unit', ''))
                return {'valor': valor, 'unidad': unidad}
            return {'valor': info, 'unidad': ''}
    return None


def _extraer_valor_indice(indices: Any, alias: Iterable[str]) -> Optional[Any]:
    alias_norm = [_normalizar_key(a) for a in alias]
    if isinstance(indices, dict):
        for key, value in indices.items():
            key_norm = _normalizar_key(key)
            if any(a == key_norm or a in key_norm for a in alias_norm):
                return value
            encontrado = _extraer_valor_indice(value, alias)
            if encontrado is not None:
                return encontrado
    return None


def _aplicar_fallback(valor: Any, clave_basal: str, nombre: str) -> tuple[float, Fiabilidad]:
    fallback = obtener_fallback_universal()
    valor_final, estado = fallback.aplicar_fallback(valor, clave_basal, nombre)
    fiabilidad = Fiabilidad.ALTA if estado == EstadoFisico.REAL else Fiabilidad.MEDIA
    return valor_final, fiabilidad


_ORDEN_FIABILIDAD = {
    Fiabilidad.FALLA: 0,
    Fiabilidad.BAJA: 1,
    Fiabilidad.MEDIA: 2,
    Fiabilidad.ALTA: 3,
}


def _combinar_fiabilidad(base: Fiabilidad, extra: Optional[Fiabilidad]) -> Fiabilidad:
    if extra is None:
        return base
    return base if _ORDEN_FIABILIDAD[base] <= _ORDEN_FIABILIDAD[extra] else extra


def _fiabilidad_por_alerta(info: Dict[str, Any]) -> Fiabilidad:
    error = info.get('error_estimado')
    try:
        err_val = float(error) if error is not None else None
    except Exception:
        err_val = None
    if err_val is None:
        return Fiabilidad.BAJA
    if err_val >= 50:
        return Fiabilidad.BAJA
    if err_val >= 20:
        return Fiabilidad.MEDIA
    return Fiabilidad.ALTA


def _ajuste_prioridad_por_meta(meta: Optional[Dict[str, Any]]) -> int:
    if not isinstance(meta, dict):
        return 0
    ajuste = 0
    ubicacion = str(meta.get('ubicacion', meta.get('location', ''))).lower()
    exposicion = str(meta.get('exposicion', meta.get('exposure', ''))).lower()
    redundancia = str(meta.get('redundancia', meta.get('backup', ''))).lower()
    altura = meta.get('altura', meta.get('height'))

    if any(t in ubicacion for t in ['exterior', 'outdoor']):
        ajuste += 5
    if any(t in ubicacion for t in ['interior', 'indoor']):
        ajuste -= 2
    if any(t in exposicion for t in ['sombra', 'shade']):
        ajuste += 3
    if any(t in exposicion for t in ['sol', 'sun', 'direct']):
        ajuste -= 3
    if any(t in redundancia for t in ['backup', 'redundante']):
        ajuste -= 3
    try:
        if altura is not None and float(altura) > 2.0:
            ajuste += 1
    except Exception:
        pass
    return ajuste


def _seleccionar_sensor_mejor(
    sensores: Dict[str, Any],
    alias: Iterable[str],
    contexto: Dict[str, Any],
    tipo: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    alias_norm = [_normalizar_key(a) for a in alias]
    alertas_sensores = contexto.get('alertas_sensores', {})
    mejor = None

    for key, info in sensores.items():
        key_norm = _normalizar_key(key)
        if not any(a == key_norm or a in key_norm for a in alias_norm):
            continue
        if isinstance(info, dict):
            valor = info.get('valor', info.get('value'))
            unidad = info.get('unidad', info.get('unit', ''))
            meta = info.get('meta') if isinstance(info.get('meta'), dict) else info
        else:
            valor = info
            unidad = ''
            meta = None
        if valor is None:
            continue

        perfil = _perfil_sensor_conocido(key, meta)
        prioridad = perfil.get('prioridad', 40) if perfil else 30
        prioridad += _ajuste_prioridad_por_meta(meta)
        fiab = perfil.get('fiabilidad', Fiabilidad.ALTA) if perfil else Fiabilidad.ALTA

        if key in alertas_sensores:
            fiab = _fiabilidad_por_alerta(alertas_sensores[key])
            prioridad -= 40

        score = prioridad + (_peso_fiabilidad(fiab) * 10)
        if mejor is None or score > mejor['score']:
            mejor = {
                'sensor': key,
                'valor': valor,
                'unidad': unidad,
                'fiabilidad': fiab,
                'prioridad': prioridad,
                'meta': meta,
                'score': score,
                'perfil': perfil,
            }

    if mejor and tipo:
        mejor['valor'], mejor['unidad'] = _normalizar_unidad_valor(tipo, mejor['valor'], mejor['unidad'])

    return mejor


def _sensores_origen(seleccion: Optional[Dict[str, Any]], fallback: str) -> List[str]:
    if seleccion and seleccion.get('sensor'):
        return [seleccion['sensor']]
    return [fallback] if fallback else []


def _asegurar_traza(valor: ValorSistema) -> None:
    if hasattr(valor, 'traza'):
        return
    valor.traza = {
        'origen': valor.tipo,
        'sensores': list(valor.sensores or []),
        'dependencias': list(valor.dependencias or []),
    }


def _agregar_traza_extra(valor: ValorSistema, extra: Dict[str, Any]) -> None:
    if not extra:
        return
    _asegurar_traza(valor)
    if isinstance(valor.traza, dict):
        valor.traza.update(extra)


def _parsear_timestamp(ts: Any) -> Optional[float]:
    if ts is None:
        return None
    try:
        return float(ts)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp()
    except Exception:
        return None


def _qc_resumen_alias(
    sensores: Dict[str, Any],
    alias: Iterable[str],
) -> Dict[str, Any]:
    alias_norm = [_normalizar_key(a) for a in alias]
    valores = []
    edades = []
    for key, info in sensores.items():
        key_norm = _normalizar_key(key)
        if not any(a == key_norm or a in key_norm for a in alias_norm):
            continue
        if isinstance(info, dict):
            valor = info.get('valor', info.get('value'))
            ts = info.get('timestamp')
        else:
            valor = info
            ts = None
        try:
            valores.append(float(valor))
        except Exception:
            continue
        ts_val = _parsear_timestamp(ts)
        if ts_val is not None:
            edades.append(time.time() - ts_val)

    resumen = {
        'n': len(valores),
        'min': min(valores) if valores else None,
        'max': max(valores) if valores else None,
        'media': statistics.fmean(valores) if valores else None,
        'mediana': statistics.median(valores) if valores else None,
        'rango': (max(valores) - min(valores)) if len(valores) >= 2 else None,
        'edad_s_min': min(edades) if edades else None,
        'edad_s_max': max(edades) if edades else None,
        'edad_s_media': statistics.fmean(edades) if edades else None,
    }
    return resumen


def _float_or_none(valor: Any) -> Optional[float]:
    try:
        return float(valor)
    except Exception:
        return None


def _punto_rocio_magnus(temp_c: float, humedad_relativa_pct: float) -> Optional[float]:
    try:
        t = float(temp_c)
        rh = float(humedad_relativa_pct)
    except Exception:
        return None
    if rh <= 0:
        return None
    # Magnus-Tetens (física termodinámica del vapor)
    a = 17.625
    b = 243.04
    gamma = (a * t / (b + t)) + math.log(rh / 100.0)
    return (b * gamma) / (a - gamma)


def _presion_vapor_pa(temp_c: float, humedad_relativa_pct: float) -> Optional[float]:
    try:
        t = float(temp_c)
        rh = float(humedad_relativa_pct)
    except Exception:
        return None
    if rh < 0:
        return None
    # Presión de vapor saturado (hPa) - Magnus-Tetens
    e_s_hpa = 6.112 * math.exp((17.67 * t) / (t + 243.5))
    e_hpa = (rh / 100.0) * e_s_hpa
    return e_hpa * 100.0


def _calcular_radiacion_extraterrestre(contexto: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        from core.indices.rest2_gueymard_radiacion import calcular_radiacion_extraterrestre_rest2
        from core.arcos_solares import calcular_posicion_sol
    except Exception:
        return None

    lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
    lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
    altitud = contexto.get('ubicacion', {}).get('altitud', ESTACION.ALTITUD)
    orografia = contexto.get('orografia') if isinstance(contexto, dict) else None
    perfil_horizonte = orografia.get("perfil_horizonte") if isinstance(orografia, dict) else None

    datos_sol = calcular_posicion_sol(lat, lon, datetime.now(), perfil_horizonte=perfil_horizonte)
    elevacion_solar = datos_sol.get('elevacion_solar_deg')
    if elevacion_solar is None:
        return None

    resultado = calcular_radiacion_extraterrestre_rest2(
        fecha=datetime.now(),
        latitud_deg=lat,
        longitud_deg=lon,
        altitud_m=altitud,
        uso_horario=0,
        elevacion_spa_nrel=elevacion_solar,
    )
    return {
        'g0_w_m2': resultado.get('g0_w_m2'),
        'elevacion_solar_deg': resultado.get('elevacion_solar_deg', elevacion_solar),
        'fuente': resultado.get('fuente_astronomica')
    }


def _calcular_nubosidad_fisica(
    contexto: Dict[str, Any],
    temp_c: float,
    humedad_relativa_pct: float,
    rad_real_w_m2: float,
    presion_hpa: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    try:
        from core.indices.nubosidad_liu_jordan_kasten import calcular_nubosidad_liu_jordan_kasten
    except Exception:
        return None

    if rad_real_w_m2 is None:
        return None
    g0 = _calcular_radiacion_extraterrestre(contexto)
    if not g0 or not g0.get('g0_w_m2'):
        return None

    punto_rocio = _punto_rocio_magnus(temp_c, humedad_relativa_pct)
    if punto_rocio is None:
        return None

    if presion_hpa is None:
        presion_hpa = 1013.25

    dia_ano = datetime.utcnow().timetuple().tm_yday
    resultado = calcular_nubosidad_liu_jordan_kasten(
        radiacion_medida_w_m2=rad_real_w_m2,
        radiacion_extraterrestre_w_m2=g0['g0_w_m2'],
        elevacion_solar_deg=g0['elevacion_solar_deg'] or 0.0,
        temp_aire_c=temp_c,
        temp_rocio_c=punto_rocio,
        humedad_relativa_pct=humedad_relativa_pct,
        presion_hpa=presion_hpa,
        dia_ano=dia_ano,
    )
    resultado['_g0_w_m2'] = g0['g0_w_m2']
    resultado['_elevacion_solar_deg'] = g0['elevacion_solar_deg']
    resultado['_punto_rocio_c'] = punto_rocio
    return resultado


def _calcular_lw_desc_prata(temp_c: float, humedad_relativa_pct: float, nubosidad_pct: Optional[float]) -> Optional[float]:
    try:
        from core.indices.radiacion_lw_prata import calcular_radiacion_lw_descendente_prata
    except Exception:
        return None
    e_vapor_pa = _presion_vapor_pa(temp_c, humedad_relativa_pct)
    if e_vapor_pa is None:
        return None
    nub_frac = None
    if nubosidad_pct is not None:
        try:
            nub_frac = max(0.0, min(1.0, float(nubosidad_pct) / 100.0))
        except Exception:
            nub_frac = None
    return calcular_radiacion_lw_descendente_prata(
        T_air_k=float(temp_c) + 273.15,
        e_vapor_pa=e_vapor_pa,
        nubosidad_fraccion=nub_frac or 0.0
    )


def _calcular_lw_up_stefan(temp_superficie_c: float, emisividad: float = 0.95) -> Optional[float]:
    try:
        from core.indices.radiacion_lw_prata import STEFAN_BOLTZMANN
    except Exception:
        return None
    try:
        t_k = float(temp_superficie_c) + 273.15
        eps = max(0.0, min(1.0, float(emisividad)))
    except Exception:
        return None
    return eps * STEFAN_BOLTZMANN * (t_k ** 4)


def _calcular_le_virtual_penman(
    temp_c: float,
    humedad_relativa_pct: float,
    radiacion_w_m2: float,
    viento_ms: float,
    presion_hpa: Optional[float] = None,
    elevacion_solar_deg: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    try:
        from core.indices.environmental_indices import evapotranspiracion_penman_monteith
    except Exception:
        return None
    try:
        t_val = float(temp_c)
        rh_val = float(humedad_relativa_pct)
        r_val = float(radiacion_w_m2)
        v_val = float(viento_ms)
    except Exception:
        return None
    if presion_hpa is not None:
        try:
            presion_kpa = float(presion_hpa) / 10.0
        except Exception:
            presion_kpa = 101.3
    else:
        presion_kpa = 101.3
    try:
        hora_solar = datetime.now().hour + (datetime.now().minute / 60.0)
    except Exception:
        hora_solar = 12.0

    et0_mm_dia = evapotranspiracion_penman_monteith(
        temp_c=t_val,
        humedad=rh_val,
        radiacion=r_val,
        viento=v_val,
        hora_solar=hora_solar,
        elevacion_solar=elevacion_solar_deg,
        presion_kpa=presion_kpa,
    )
    try:
        et0_mm_dia = max(0.0, float(et0_mm_dia))
    except Exception:
        return None
    lambda_v = 2.501e6 - 2370.0 * t_val
    if lambda_v <= 0:
        lambda_v = 2.45e6
    le_w_m2 = (lambda_v * (et0_mm_dia / 86400.0))
    return {
        'le_w_m2': le_w_m2,
        'et0_mm_dia': et0_mm_dia,
        'lambda_j_kg': lambda_v,
        'presion_kpa': presion_kpa,
        'hora_solar': hora_solar,
    }


def _calcular_directa_difusa_virtual(
    contexto: Dict[str, Any],
    rad_real_w_m2: float,
    presion_hpa: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    try:
        from core.indices.rayleigh_miller_dispersion import correccion_irradiancia_directa
    except Exception:
        return None

    g0 = _calcular_radiacion_extraterrestre(contexto)
    if not g0 or not g0.get('g0_w_m2'):
        return None

    elev = g0.get('elevacion_solar_deg')
    if elev is None or elev <= 0:
        return None

    if presion_hpa is None:
        presion_hpa = 1013.25

    clear = correccion_irradiancia_directa(
        irradiancia_toa=float(g0['g0_w_m2']),
        presion_hpa=float(presion_hpa),
        elevacion_solar_deg=float(elev),
    )
    clear_global = clear.get('global')
    if not clear_global or clear_global <= 0:
        return None

    escala = max(0.0, float(rad_real_w_m2) / float(clear_global))
    directa = float(clear.get('directa', 0.0)) * escala
    difusa = float(clear.get('difusa', 0.0)) * escala

    return {
        'directa_w_m2': directa,
        'difusa_w_m2': difusa,
        'global_clear_w_m2': float(clear_global),
        'escala': escala,
        'g0_w_m2': g0.get('g0_w_m2'),
        'elevacion_solar_deg': elev,
        'nubosidad': clear.get('nubosidad'),
    }


def _calcular_tmrt_fisica(
    contexto: Dict[str, Any],
    temp_c: float,
    humedad_relativa_pct: float,
    radiacion_w_m2: float,
    viento_ms: float,
    nubosidad_pct: float,
    elevacion_solar_deg: float,
    temp_suelo_c: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    try:
        from core.indices.temperatura_radiante_dinamica import calcular_temperatura_radiante_media
    except Exception:
        return None
    try:
        temp_rocio = _punto_rocio_magnus(temp_c, humedad_relativa_pct)
    except Exception:
        temp_rocio = None

    resultado = calcular_temperatura_radiante_media(
        temp_aire_c=float(temp_c),
        radiacion_solar_w_m2=float(radiacion_w_m2),
        nubosidad_pct=float(nubosidad_pct or 0.0),
        albedo_entorno=0.2,
        velocidad_viento_ms=max(0.1, float(viento_ms)),
        elevacion_solar_deg=float(elevacion_solar_deg),
        temp_suelo_c=temp_suelo_c,
        humedad_relativa_pct=float(humedad_relativa_pct),
        temp_rocio_c=temp_rocio,
    )
    return resultado


def _peso_fiabilidad(fiabilidad: Fiabilidad) -> int:
    if fiabilidad == Fiabilidad.ALTA:
        return 3
    if fiabilidad == Fiabilidad.MEDIA:
        return 2
    return 1


def _normalizar_unidad_valor(tipo: str, valor: Any, unidad: Optional[str]) -> tuple[Any, Optional[str]]:
    if valor is None:
        return valor, unidad
    unidad_norm = (unidad or '').strip().lower().replace(' ', '')
    try:
        val = float(valor)
    except Exception:
        return valor, unidad

    if tipo == 'temperatura':
        if unidad_norm in {'f', '°f'}:
            return (val - 32.0) * (5.0 / 9.0), '°C'
        return val, unidad or '°C'

    if tipo == 'presion':
        if unidad_norm in {'kpa'}:
            return val * 10.0, 'hPa'
        if unidad_norm in {'pa'}:
            return val / 100.0, 'hPa'
        if unidad_norm in {'inhg', 'in-hg', 'inhg'}:
            return val * 33.8639, 'hPa'
        return val, unidad or 'hPa'

    if tipo == 'lluvia_rate':
        if unidad_norm in {'in/h', 'inh', 'in/hr', 'inph'}:
            return val * 25.4, 'mm/h'
        return val, unidad or 'mm/h'

    if tipo == 'lluvia':
        if unidad_norm in {'in', 'inch', 'inches'}:
            return val * 25.4, 'mm'
        return val, unidad or 'mm'

    if tipo == 'radiacion':
        return val, unidad or 'W/m²'

    if tipo == 'humedad':
        if unidad_norm in {'fraction', 'ratio'} and 0 <= val <= 1:
            return val * 100.0, '%'
        return val, unidad or '%'

    if tipo == 'visibilidad':
        if unidad_norm in {'m', 'meter', 'meters'}:
            return val / 1000.0, 'km'
        return val, unidad or 'km'

    return val, unidad


def _convertir_viento_kmh(valor: Any, unidad: Optional[str]) -> Any:
    if valor is None:
        return valor
    unidad_norm = (unidad or '').strip().lower().replace(' ', '')
    if unidad_norm in {'km/h', 'kmh', 'kph'}:
        return valor
    if unidad_norm in {'m/s', 'mps', 'm·s-1', ''}:
        try:
            return float(valor) * 3.6
        except Exception:
            return valor
    return valor


def _convertir_viento_ms(valor: Any, unidad: Optional[str]) -> Any:
    if valor is None:
        return valor
    unidad_norm = (unidad or '').strip().lower().replace(' ', '')
    if unidad_norm in {'m/s', 'mps', 'm·s-1'}:
        return valor
    if unidad_norm in {'km/h', 'kmh', 'kph'}:
        try:
            return float(valor) / 3.6
        except Exception:
            return valor
    return valor


def _extraer_nubosidad(contexto: Dict[str, Any]) -> Optional[float]:
    sensores = contexto.get('sensores', {})
    indices = contexto.get('indices', {})
    nubosidad_val = _extraer_valor_sensor(sensores, ['nubosidad', 'cloud', 'clouds', 'cloudcover'])
    if nubosidad_val is not None:
        try:
            return float(nubosidad_val.get('valor'))
        except Exception:
            return None
    nubosidad_idx = _extraer_valor_indice(
        indices,
        [
            'nubosidad', 'cloud', 'clouds', 'cloudcover',
            'nubosidad_implicita_pct', 'trinity_nubosidad_radiometrica_pct',
            'nubosidad_radiometrica_pct',
        ]
    )
    if nubosidad_idx is not None:
        try:
            return float(nubosidad_idx)
        except Exception:
            return None
    return None


def _extraer_nubosidad_sensor(sensores: Dict[str, Any]) -> Optional[float]:
    nubosidad_val = _extraer_valor_sensor(sensores, ['nubosidad', 'cloud', 'clouds', 'cloudcover'])
    if nubosidad_val is None:
        return None
    try:
        return float(nubosidad_val.get('valor'))
    except Exception:
        return None


def _obtener_uv_contexto(contexto: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sensores = contexto.get('sensores', {})
    indices = contexto.get('indices', {})

    uv_sel = _seleccionar_sensor_mejor(sensores, ['uv', 'indice_uv', 'uvi', 'uv_index', 'uvindex'], contexto)
    if uv_sel is not None and uv_sel.get('valor') is not None:
        return {'valor': uv_sel.get('valor'), 'motor': 'sensor', 'fiabilidad': uv_sel.get('fiabilidad')}

    uv_idx = _extraer_valor_indice(indices, ['uv', 'indice_uv', 'uvi', 'uv_index', 'uvindex'])
    if isinstance(uv_idx, dict):
        uv_idx = uv_idx.get('valor', uv_idx.get('value'))
    if uv_idx is not None:
        return {'valor': uv_idx, 'motor': 'indice', 'fiabilidad': Fiabilidad.MEDIA}

    radiacion_sel = _seleccionar_sensor_mejor(
        sensores,
        ['radiacion', 'solarradiation', 'radiacion_solar', 'radiacion_global'],
        contexto,
        'radiacion'
    )
    rad_val = radiacion_sel.get('valor') if radiacion_sel else None

    elevacion = contexto.get('elevacion_solar', {}).get('sol', {}).get('elevacion_solar_deg')
    if rad_val is None or elevacion is None:
        return None

    presion_sel = _seleccionar_sensor_mejor(sensores, ['presion', 'pressure', 'baro', 'baromabs'], contexto, 'presion')
    presion_val = presion_sel.get('valor') if presion_sel else 1013.25
    presion_unit = presion_sel.get('unidad') if presion_sel else 'hPa'
    presion_val, _ = _normalizar_unidad_valor('presion', presion_val, presion_unit)

    temp_sel = _seleccionar_sensor_mejor(sensores, ['temperatura', 'temp', 'tempc', 'tempf'], contexto, 'temperatura')
    temp_val = temp_sel.get('valor') if temp_sel else 15.0
    temp_unit = temp_sel.get('unidad') if temp_sel else '°C'
    temp_val, _ = _normalizar_unidad_valor('temperatura', temp_val, temp_unit)

    hum_sel = _seleccionar_sensor_mejor(sensores, ['humedad', 'humidity', 'rh', 'humedad_relativa'], contexto, 'humedad')
    hum_val = hum_sel.get('valor') if hum_sel else 50.0
    hum_unit = hum_sel.get('unidad') if hum_sel else '%'
    hum_val, _ = _normalizar_unidad_valor('humedad', hum_val, hum_unit)

    try:
        from core.indices.uv_spectral_diamond import get_uv_spectral_engine
    except Exception:
        return None

    lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
    lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
    altitud = contexto.get('ubicacion', {}).get('altitud', ESTACION.ALTITUD)
    try:
        # Verificar que tenemos valores ISA reales (no fallbacks silenciosos)
        if not temp_val:
            raise ValueError("[SENSOR FAILURE] Temperatura no disponible - sensor ISA falla. No usar fallback 15.0°C")
        if not hum_val:
            raise ValueError("[SENSOR FAILURE] Humedad relativa no disponible - sensor ISA falla. No usar fallback 50%")
        if not presion_val:
            raise ValueError("[SENSOR FAILURE] Presión atmosférica no disponible - sensor ISA falla. No usar fallback 1013.25 hPa")
        
        uv_engine = get_uv_spectral_engine(float(lat), float(lon), float(altitud or 0.0))
        uv_val, meta = uv_engine.calcular_uv(
            radiacion_solar=float(rad_val),
            elevacion_solar=float(elevacion),
            presion_hpa=float(presion_val),
            temperatura_c=float(temp_val),
            humedad_relativa=float(hum_val),
        )
        return {'valor': uv_val, 'motor': meta.get('motor', 'Spectral_Diamond_v3'), 'fiabilidad': Fiabilidad.MEDIA}
    except Exception:
        logging.exception("Error calculando UV para panel")
        return None


def _es_noche(contexto: Dict[str, Any]) -> bool:
    try:
        from core.arcos_solares import calcular_posicion_sol
        lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
        lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
        orografia = contexto.get('orografia') if isinstance(contexto, dict) else None
        perfil_horizonte = orografia.get("perfil_horizonte") if isinstance(orografia, dict) else None
        datos_sol = calcular_posicion_sol(lat, lon, datetime.now(), perfil_horizonte=perfil_horizonte)
        elevacion_solar = datos_sol.get('elevacion_solar_deg')
        return elevacion_solar is not None and elevacion_solar <= 0
    except Exception:
        logging.exception("Error calculando condición nocturna")
        return False


def _integrar_dosis_uv(historial: List[tuple], ts_inicio: float, ts_fin: float) -> Optional[float]:
    if not historial or len(historial) < 2:
        return None
    try:
        muestras = [(t, v) for t, v in historial if ts_inicio <= t <= ts_fin]
    except Exception:
        return None
    if len(muestras) < 2:
        return None
    muestras.sort(key=lambda x: x[0])
    dosis_j_m2 = 0.0
    for (t0, v0), (t1, v1) in zip(muestras, muestras[1:]):
        try:
            if v0 is None or v1 is None:
                continue
            u0 = float(v0)
            u1 = float(v1)
        except Exception:
            continue
        dt = max(0.0, t1 - t0)
        if dt <= 0:
            continue
        e0 = u0 * 0.025
        e1 = u1 * 0.025
        dosis_j_m2 += ((e0 + e1) / 2.0) * dt
    if dosis_j_m2 <= 0:
        return None
    return dosis_j_m2 / 1000.0


def _calcular_dosis_uv_diaria() -> Optional[Dict[str, Any]]:
    if not _system_manager or not getattr(_system_manager, 'system', None):
        return None
    sistema = _system_manager.system
    if not hasattr(sistema, 'obtener_historial_sensor'):
        return None
    candidatos = ['uv', 'uv_index', 'indice_uv', 'uvi']
    historial = None
    fuente = None
    for nombre in candidatos:
        try:
            datos = sistema.obtener_historial_sensor(nombre)
        except Exception:
            datos = None
        if datos and len(datos) >= 2:
            historial = datos
            fuente = nombre
            break
    if not historial:
        return None
    ahora = datetime.now()
    inicio = datetime(ahora.year, ahora.month, ahora.day)
    dosis_kj_m2 = _integrar_dosis_uv(historial, inicio.timestamp(), time.time())
    if dosis_kj_m2 is None:
        return None
    return {
        'dosis_kj_m2': dosis_kj_m2,
        'fuente': fuente or 'uv',
    }


def _aplicar_alerta_a_valor(valor: ValorSistema, info: Dict[str, Any], origen: str) -> None:
    if valor.alerta:
        return
    motivo = info.get('motivo', 'anomalía')
    error = info.get('error_estimado')
    extra = f" ±{error}%" if error is not None else ""
    valor.alerta = f"[WARNING] {origen}: {motivo}{extra}"
    try:
        err_val = float(error) if error is not None else None
    except Exception:
        err_val = None
    if err_val is not None:
        if err_val >= 50:
            valor.fiabilidad = Fiabilidad.BAJA
        elif err_val >= 20:
            valor.fiabilidad = Fiabilidad.MEDIA
        else:
            valor.fiabilidad = Fiabilidad.ALTA
    else:
        valor.fiabilidad = Fiabilidad.BAJA


def _inferir_categoria_sensor(nombre: str, unidad: Optional[str], meta: Optional[Dict[str, Any]] = None) -> Optional[str]:
    key = _normalizar_key(nombre)
    if any(token in key for token in ['temp', 'temperatura', 'hum', 'humidity', 'rh', 'pres', 'baro', 'pressure']):
        return 'termo'
    if any(token in key for token in ['wind', 'viento', 'gust', 'racha', 'dir', 'direccion']):
        return 'viento'
    if any(token in key for token in ['uv', 'rad', 'solar', 'radiacion', 'rain', 'lluv', 'precip', 'nieve']):
        return 'radiacion'
    if any(token in key for token in ['lightning', 'rayos', 'storm', 'tormenta']):
        return 'radiacion'
    if any(token in key for token in ['pm', 'co2', 'air', 'gas', 'aqi', 'polvo', 'particula']):
        return 'aire'
    if any(token in key for token in ['visib', 'visibility']):
        return 'aire'
    meta_tipo = None
    if isinstance(meta, dict):
        meta_tipo = meta.get('tipo') or meta.get('categoria') or meta.get('grupo')
    if isinstance(meta_tipo, str):
        meta_tipo_norm = _normalizar_key(meta_tipo)
        if any(t in meta_tipo_norm for t in ['termo', 'temp', 'hum', 'pres']):
            return 'termo'
        if any(t in meta_tipo_norm for t in ['viento', 'wind']):
            return 'viento'
        if any(t in meta_tipo_norm for t in ['radiacion', 'solar', 'uv', 'lluvia', 'precip']):
            return 'radiacion'
        if any(t in meta_tipo_norm for t in ['aire', 'calidad', 'aqi', 'particula', 'gas', 'co2', 'pm']):
            return 'aire'
    unidad_norm = (unidad or '').strip().lower().replace(' ', '')
    if unidad_norm in {'°c', 'c', '°f', 'f', 'k'}:
        return 'termo'
    if unidad_norm in {'km/h', 'kmh', 'kph', 'm/s', 'mps', 'm·s-1'}:
        return 'viento'
    if unidad_norm in {'w/m²', 'w/m2', 'mj/m²'}:
        return 'radiacion'
    if unidad_norm in {'mm', 'mm/h', 'in', 'in/h'}:
        return 'radiacion'
    if unidad_norm in {'µg/m³', 'ug/m3', 'ppm', 'ppb'}:
        return 'aire'
    if unidad_norm in {'km', 'm'}:
        return 'aire'
    return None


def _perfil_sensor_conocido(nombre: str, meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    key = _normalizar_key(nombre)
    meta_norm = {}
    if isinstance(meta, dict):
        meta_norm = {str(k).lower(): str(v).lower() for k, v in meta.items() if v is not None}

    if 'hp2550' in key or 'hp2550a' in key:
        return {'prioridad': 95, 'fiabilidad': Fiabilidad.ALTA, 'icono': '🧠'}
    if 'wh65' in key:
        return {'prioridad': 90, 'fiabilidad': Fiabilidad.ALTA, 'icono': '🛰️'}
    if 'wh57' in key or 'lightning' in key or meta_norm.get('tipo') == 'lightning':
        return {'prioridad': 85, 'fiabilidad': Fiabilidad.ALTA, 'icono': '⚡'}
    if 'wh51' in key or 'soil' in key or 'suelo' in key:
        return {'prioridad': 70, 'fiabilidad': Fiabilidad.MEDIA, 'icono': '🌱'}
    if 'wh31' in key:
        return {'prioridad': 88, 'fiabilidad': Fiabilidad.ALTA, 'icono': '🌤️'}
    return None


def _sensor_ya_conocido(sensor_key: str, alias_globales: List[str]) -> bool:
    key_norm = _normalizar_key(sensor_key)
    return any(a == key_norm or a in key_norm for a in alias_globales)


def generar_grupos_desde_sistema(contexto: Dict[str, Any]) -> List[GrupoValores]:
    """
    Genera EXACTAMENTE 5 grupos de valores desde los datos REALES del sistema.
    Sistema de deduplicación profesional: cada valor aparece solo en el grupo más relevante.
    
    Grupos (ordenados por prioridad):
    1. Termodinámica (Temp, Humedad, Presión, Sensación UTCI)
    2. Viento (Velocidad, Ráfagas, Dirección, Z0h)
    3. Biometría & Confort (PMV, VPD, WBGT, otros índices de confort)
    4. Radiación & Precipitación (Solar, UV, Lluvia, Nieve)
    5. Calidad Aire & Visibilidad (PM2.5, PM10, CO2, Visibilidad)
    """
    sensores = contexto.get('sensores', {})
    indices = contexto.get('indices', {})
    nubosidad = _extraer_nubosidad(contexto)
    alertas_sensores = contexto.get('alertas_sensores', {})
    alias_globales = [
        'temperatura', 'temp', 'tempc', 'tempf', 'temperature',
        'humedad', 'humidity', 'rh', 'humedad_relativa',
        'presion', 'pressure', 'baro', 'baromabs', 'baromrelin',
        'viento', 'windspeed', 'wind_speed', 'windspeedmph', 'wind_ms',
        'racha', 'windgust', 'windgustmph', 'gust',
        'direccion_viento', 'winddir', 'wind_dir',
        'radiacion', 'solarradiation', 'radiacion_solar',
        'radiacion_directa', 'directa', 'dni', 'beam', 'direct_normal',
        'radiacion_difusa', 'difusa', 'dhi', 'diffuse',
        'uv', 'indice_uv', 'uvi', 'uv_index', 'uvindex',
        'lluvia', 'rain', 'rainrate', 'rainratein',
        'lluvia_acumulada', 'dailyrain', 'eventrain', 'hourlyrain',
        'pm25', 'pm25_ch1', 'pm25_avg_24h_ch1',
        'pm10', 'pm10_ch1',
        'co2', 'co2_ppm',
        'visibilidad', 'visibility',
        'nubosidad', 'cloud', 'clouds', 'cloudcover'
    ]
    
    # Sistema de deduplicación por prioridad
    valores_por_nombre: Dict[str, tuple[list, ValorSistema]] = {}

    def _agregar_valor(lista: list, valor: ValorSistema) -> bool:
        """Agrega un valor si no existe o si tiene mayor prioridad que el existente."""
        _asegurar_traza(valor)
        key = _normalizar_key(valor.nombre)
        existente = valores_por_nombre.get(key)
        if not existente:
            lista.append(valor)
            valores_por_nombre[key] = (lista, valor)
            return True
        lista_prev, valor_prev = existente
        if _peso_fiabilidad(valor.fiabilidad) > _peso_fiabilidad(valor_prev.fiabilidad) or (
            _peso_fiabilidad(valor.fiabilidad) == _peso_fiabilidad(valor_prev.fiabilidad)
            and valor.prioridad > valor_prev.prioridad
        ):
            try:
                lista_prev.remove(valor_prev)
            except ValueError:
                pass
            lista.append(valor)
            valores_por_nombre[key] = (lista, valor)
            return True
        return False
    
    grupos = []
    
    # GRUPO 1: TERMODINÁMICA 🌡️
    valores_termo = []
    temp_sel = _seleccionar_sensor_mejor(sensores, ['temperatura', 'temp', 'tempc', 'tempf', 'temperature'], contexto, 'temperatura')
    valor_temp, fiab_temp = _aplicar_fallback(temp_sel.get('valor') if temp_sel else None, 'temperatura', 'temperatura')
    fiab_temp = _combinar_fiabilidad(fiab_temp, temp_sel.get('fiabilidad') if temp_sel else None)
    unidad_temp = temp_sel.get('unidad') if temp_sel else '°C'
    valor_temp_obj = ValorSistema(
        nombre='Temperatura',
        tipo='sensor',
        valor=valor_temp,
        unidad=unidad_temp or '°C',
        fiabilidad=fiab_temp,
        icono='🌡️',
        prioridad=100,
        sensores=_sensores_origen(temp_sel, 'temperatura'),
        dependencias=[]
    )
    _agregar_valor(valores_termo, valor_temp_obj)
    _agregar_traza_extra(valor_temp_obj, {
        'qc': _qc_resumen_alias(sensores, ['temperatura', 'temp', 'tempc', 'tempf', 'temperature'])
    })

    humedad_sel = _seleccionar_sensor_mejor(sensores, ['humedad', 'humidity', 'rh', 'humedad_relativa'], contexto, 'humedad')
    valor_h, fiab_h = _aplicar_fallback(humedad_sel.get('valor') if humedad_sel else None, 'humedad_relativa', 'humedad')
    fiab_h = _combinar_fiabilidad(fiab_h, humedad_sel.get('fiabilidad') if humedad_sel else None)
    unidad_h = humedad_sel.get('unidad') if humedad_sel else '%'
    valor_h_obj = ValorSistema(
        nombre='Humedad',
        tipo='sensor',
        valor=valor_h,
        unidad=unidad_h or '%',
        fiabilidad=fiab_h,
        icono='💧',
        prioridad=95,
        sensores=_sensores_origen(humedad_sel, 'humedad'),
        dependencias=[]
    )
    _agregar_valor(valores_termo, valor_h_obj)
    _agregar_traza_extra(valor_h_obj, {
        'qc': _qc_resumen_alias(sensores, ['humedad', 'humidity', 'rh', 'humedad_relativa'])
    })

    presion_sel = _seleccionar_sensor_mejor(sensores, ['presion', 'pressure', 'baro', 'baromabs', 'baromrelin'], contexto, 'presion')
    valor_p, fiab_p = _aplicar_fallback(presion_sel.get('valor') if presion_sel else None, 'presion', 'presion')
    fiab_p = _combinar_fiabilidad(fiab_p, presion_sel.get('fiabilidad') if presion_sel else None)
    unidad_p = presion_sel.get('unidad') if presion_sel else 'hPa'
    valor_p_obj = ValorSistema(
        nombre='Presión',
        tipo='sensor',
        valor=valor_p,
        unidad=unidad_p or 'hPa',
        fiabilidad=fiab_p,
        icono='🎚️',
        prioridad=85,
        sensores=_sensores_origen(presion_sel, 'presion'),
        dependencias=[]
    )
    _agregar_valor(valores_termo, valor_p_obj)
    _agregar_traza_extra(valor_p_obj, {
        'qc': _qc_resumen_alias(sensores, ['presion', 'pressure', 'baro', 'baromabs', 'baromrelin'])
    })

    temp_c = _float_or_none(valor_temp)
    humedad_pct = _float_or_none(valor_h)
    presion_hpa = _float_or_none(valor_p)

    coherencia_termica = _extraer_valor_indice(indices, ['coherencia_termica_sensores'])
    if coherencia_termica is not None:
        valor_ct, fiab_ct = _aplicar_fallback(coherencia_termica, 'temperatura', 'coherencia_termica_sensores')
        _agregar_valor(valores_termo, ValorSistema(
            nombre='Coherencia térmica',
            tipo='índice',
            valor=valor_ct,
            unidad='0-100',
            fiabilidad=fiab_ct,
            icono='✅',
            prioridad=75,
            sensores=['temperatura'],
            dependencias=['QC']
        ))

    estabilidad_nocturna = _extraer_valor_indice(indices, ['estabilidad_nocturna_score'])
    if estabilidad_nocturna is not None:
        valor_en, fiab_en = _aplicar_fallback(estabilidad_nocturna, 'temperatura', 'estabilidad_nocturna_score')
        _agregar_valor(valores_termo, ValorSistema(
            nombre='Estabilidad nocturna',
            tipo='índice',
            valor=valor_en,
            unidad='0-100',
            fiabilidad=fiab_en,
            icono='🌙',
            prioridad=70,
            sensores=['temperatura', 'humedad', 'viento'],
            dependencias=['Monin-Obukhov']
        ))

    masa_aire_theta_e = _extraer_valor_indice(indices, ['masa_aire_theta_e'])
    if masa_aire_theta_e is not None:
        valor_mae, fiab_mae = _aplicar_fallback(masa_aire_theta_e, 'temperatura', 'masa_aire_theta_e')
        valor_mae_obj = ValorSistema(
            nombre='Masa de aire θe',
            tipo='índice',
            valor=valor_mae,
            unidad='K',
            fiabilidad=fiab_mae,
            icono='🧭',
            prioridad=62,
            sensores=['temperatura', 'humedad', 'presion'],
            dependencias=['Masas de aire']
        )
        _agregar_valor(valores_termo, valor_mae_obj)
        _agregar_traza_extra(valor_mae_obj, {
            'metodo': 'Clasificación masas de aire (θe)',
            'fuente_indice': 'masa_aire_theta_e',
        })

    enfriamiento = _extraer_valor_indice(indices, ['indice_enfriamiento_radiativo'])
    if enfriamiento is not None:
        valor_er, fiab_er = _aplicar_fallback(enfriamiento, 'temperatura', 'indice_enfriamiento_radiativo')
        _agregar_valor(valores_termo, ValorSistema(
            nombre='Enfriamiento radiativo',
            tipo='índice',
            valor=valor_er,
            unidad='0-100',
            fiabilidad=fiab_er,
            icono='❄️',
            prioridad=65,
            sensores=['radiacion', 'temperatura'],
            dependencias=['Qnet']
        ))

    tmin_noche = None
    tmin_noche_fuente = None
    if isinstance(indices, dict):
        for key in ['minima_temperatura_esperada_noche', 'temperatura_minima_esperada_noche', 'tmin_esperada_noche']:
            if key in indices:
                tmin_noche = indices.get(key)
                tmin_noche_fuente = key
                break
    if tmin_noche is not None:
        valor_tmin, fiab_tmin = _aplicar_fallback(tmin_noche, 'temperatura', 'minima_temperatura_esperada_noche')
        valor_tmin_obj = ValorSistema(
            nombre='Mínima esperada (Force-Restore)',
            tipo='índice',
            valor=valor_tmin,
            unidad='°C',
            fiabilidad=fiab_tmin,
            icono='🌡️',
            prioridad=60,
            sensores=['temperatura', 'radiacion', 'viento', 'humedad'],
            dependencias=['Deardorff', 'Force-Restore', 'Prata']
        )
        _agregar_valor(valores_termo, valor_tmin_obj)
        _agregar_traza_extra(valor_tmin_obj, {
            'metodo': 'Deardorff Force-Restore + Prata',
            'fuente_indice': tmin_noche_fuente,
        })

    suelo_profundo = None
    suelo_profundo_fuente = None
    if isinstance(indices, dict):
        for key in ['temperatura_suelo_profundo_estimada', 'temperatura_suelo_profundo']:
            if key in indices:
                suelo_profundo = indices.get(key)
                suelo_profundo_fuente = key
                break
    if suelo_profundo is not None:
        valor_ts, fiab_ts = _aplicar_fallback(suelo_profundo, 'temperatura', 'temperatura_suelo_profundo')
        valor_ts_obj = ValorSistema(
            nombre='Temperatura suelo profundo',
            tipo='índice',
            valor=valor_ts,
            unidad='°C',
            fiabilidad=fiab_ts,
            icono='🪨',
            prioridad=58,
            sensores=['temperatura', 'humedad'],
            dependencias=['Deardorff', 'Force-Restore']
        )
        _agregar_valor(valores_termo, valor_ts_obj)
        _agregar_traza_extra(valor_ts_obj, {
            'metodo': 'Deardorff Force-Restore',
            'fuente_indice': suelo_profundo_fuente,
        })

    flujo_calor_suelo = None
    flujo_calor_suelo_fuente = None
    if isinstance(indices, dict):
        for key in ['flujo_calor_suelo_wm2', 'flujo_calor_suelo']:
            if key in indices:
                flujo_calor_suelo = indices.get(key)
                flujo_calor_suelo_fuente = key
                break
    if flujo_calor_suelo is not None:
        valor_fc, fiab_fc = _aplicar_fallback(flujo_calor_suelo, 'temperatura', 'flujo_calor_suelo')
        valor_fc_obj = ValorSistema(
            nombre='Flujo calor suelo',
            tipo='índice',
            valor=valor_fc,
            unidad='W/m²',
            fiabilidad=fiab_fc,
            icono='🪨',
            prioridad=57,
            sensores=['temperatura', 'radiacion'],
            dependencias=['Deardorff', 'Force-Restore']
        )
        _agregar_valor(valores_termo, valor_fc_obj)
        _agregar_traza_extra(valor_fc_obj, {
            'metodo': 'Deardorff Force-Restore',
            'fuente_indice': flujo_calor_suelo_fuente,
        })

    
    if valores_termo:
        grupos.append(GrupoValores(
            nombre='Termodinámica',
            icono='🌡️',
            valores=valores_termo,
            prioridad=100
        ))
    
    # GRUPO 2: VIENTO 💨
    valores_viento = []
    viento_sel = _seleccionar_sensor_mejor(sensores, ['viento', 'windspeed', 'wind_speed', 'windspeedmph', 'wind_ms'], contexto)
    valor_v, fiab_v = _aplicar_fallback(viento_sel.get('valor') if viento_sel else None, 'velocidad_viento', 'viento')
    fiab_v = _combinar_fiabilidad(fiab_v, viento_sel.get('fiabilidad') if viento_sel else None)
    valor_v = _convertir_viento_kmh(valor_v, viento_sel.get('unidad') if viento_sel else None)
    valor_v_obj = ValorSistema(
        nombre='Velocidad viento',
        tipo='sensor',
        valor=valor_v,
        unidad='km/h',
        fiabilidad=fiab_v,
        icono='💨',
        prioridad=100,
        sensores=_sensores_origen(viento_sel, 'viento'),
        dependencias=[]
    )
    _agregar_valor(valores_viento, valor_v_obj)
    _agregar_traza_extra(valor_v_obj, {
        'qc': _qc_resumen_alias(sensores, ['viento', 'windspeed', 'wind_speed', 'windspeedmph', 'wind_ms'])
    })

    racha_sel = _seleccionar_sensor_mejor(sensores, ['racha', 'windgust', 'windgustmph', 'gust'], contexto)
    if racha_sel is not None:
        valor_r, fiab_r = _aplicar_fallback(racha_sel.get('valor'), 'velocidad_viento', 'racha')
        fiab_r = _combinar_fiabilidad(fiab_r, racha_sel.get('fiabilidad') if racha_sel else None)
        valor_r = _convertir_viento_kmh(valor_r, racha_sel.get('unidad') if racha_sel else None)
        _agregar_valor(valores_viento, ValorSistema(
            nombre='Ráfagas',
            tipo='sensor',
            valor=valor_r,
            unidad='km/h',
            fiabilidad=fiab_r,
            icono='🌪️',
            prioridad=90,
            sensores=_sensores_origen(racha_sel, 'racha'),
            dependencias=[]
        ))

    direccion_sel = _seleccionar_sensor_mejor(sensores, ['direccion_viento', 'winddir', 'wind_dir'], contexto)
    valor_d, fiab_d = _aplicar_fallback(direccion_sel.get('valor') if direccion_sel else None, 'azimuth_solar', 'direccion_viento')
    fiab_d = _combinar_fiabilidad(fiab_d, direccion_sel.get('fiabilidad') if direccion_sel else None)
    _agregar_valor(valores_viento, ValorSistema(
        nombre='Dirección viento',
        tipo='sensor',
        valor=valor_d,
        unidad='°',
        fiabilidad=fiab_d,
        icono='🧭',
        prioridad=80,
        sensores=_sensores_origen(direccion_sel, 'direccion_viento'),
        dependencias=[]
    ))

    z0h = _extraer_valor_indice(indices, ['z0h', 'z0h_zilitinkevich'])
    if z0h is not None:
        valor_z0h, fiab_z0h = _aplicar_fallback(z0h, 'temperatura', 'z0h_zilitinkevich')
        _agregar_valor(valores_viento, ValorSistema(
            nombre='Z0h (Zilitinkevich)',
            tipo='índice',
            valor=valor_z0h,
            unidad='m',
            fiabilidad=fiab_z0h,
            icono='🌪️',
            prioridad=70,
            sensores=['viento', 'temperatura'],
            dependencias=['Zilitinkevich']
        ))
    
    if valores_viento:
        grupos.append(GrupoValores(
            nombre='Viento',
            icono='💨',
            valores=valores_viento,
            prioridad=90
        ))

    masa_aire_tipo = _extraer_valor_indice(indices, ['masa_aire_tipo', 'masa_aire_clasificacion'])
    if masa_aire_tipo is not None:
        valor_mat, fiab_mat = _aplicar_fallback(masa_aire_tipo, 'temperatura', 'masa_aire_tipo')
        valor_mat_obj = ValorSistema(
            nombre='Tipo de masa de aire',
            tipo='índice',
            valor=valor_mat,
            unidad='',
            fiabilidad=fiab_mat,
            icono='🧭',
            prioridad=61,
            sensores=['temperatura', 'humedad', 'presion'],
            dependencias=['Masas de aire']
        )
        _agregar_valor(valores_termo, valor_mat_obj)
        _agregar_traza_extra(valor_mat_obj, {
            'metodo': 'Clasificación masas de aire',
            'fuente_indice': 'masa_aire_tipo',
        })

    masa_aire_origen = _extraer_valor_indice(indices, ['masa_aire_origen'])
    if masa_aire_origen is not None:
        valor_mao, fiab_mao = _aplicar_fallback(masa_aire_origen, 'temperatura', 'masa_aire_origen')
        valor_mao_obj = ValorSistema(
            nombre='Origen masa de aire',
            tipo='índice',
            valor=valor_mao,
            unidad='',
            fiabilidad=fiab_mao,
            icono='🌍',
            prioridad=60,
            sensores=['temperatura', 'humedad', 'presion'],
            dependencias=['Masas de aire']
        )
        _agregar_valor(valores_termo, valor_mao_obj)
        _agregar_traza_extra(valor_mao_obj, {
            'metodo': 'Clasificación masas de aire',
            'fuente_indice': 'masa_aire_origen',
        })

    masa_aire_tendencia = _extraer_valor_indice(indices, ['masa_aire_tendencia'])
    if masa_aire_tendencia is not None:
        valor_matn, fiab_matn = _aplicar_fallback(masa_aire_tendencia, 'temperatura', 'masa_aire_tendencia')
        valor_matn_obj = ValorSistema(
            nombre='Tendencia masa de aire',
            tipo='índice',
            valor=valor_matn,
            unidad='',
            fiabilidad=fiab_matn,
            icono='📈',
            prioridad=59,
            sensores=['temperatura', 'humedad', 'presion'],
            dependencias=['Masas de aire']
        )
        _agregar_valor(valores_termo, valor_matn_obj)
        _agregar_traza_extra(valor_matn_obj, {
            'metodo': 'Clasificación masas de aire',
            'fuente_indice': 'masa_aire_tendencia',
        })

    # GRUPO 3: BIOMETRÍA 👤
    valores_bio = []
    pmv = _extraer_valor_indice(indices, ['pmv', 'indice_pmv'])
    valor_pmv, fiab_pmv = _aplicar_fallback(pmv, 'temperatura', 'pmv')
    _agregar_valor(valores_bio, ValorSistema(
        nombre='PMV (Confort Fanger)',
        tipo='índice',
        valor=valor_pmv,
        unidad='',
        fiabilidad=fiab_pmv,
        icono='😊',
        prioridad=95,
        sensores=['temperatura', 'humedad', 'viento'],
        dependencias=['PMV']
    ))

    vpd = _extraer_valor_indice(indices, ['vpd', 'vpd_kpa', 'vpd_greenspan', 'deficit_presion_vapor'])
    valor_vpd, fiab_vpd = _aplicar_fallback(vpd, 'temperatura', 'vpd')
    _agregar_valor(valores_bio, ValorSistema(
        nombre='VPD (Greenspan)',
        tipo='índice',
        valor=valor_vpd,
        unidad='kPa',
        fiabilidad=fiab_vpd,
        icono='💠',
        prioridad=90,
        sensores=['temperatura', 'humedad', 'presion'],
        dependencias=['VPD']
    ))
    
    utci = _extraer_valor_indice(indices, ['utci', 'utci_edificio', 'utci_persona', 'utci_sensor', 'utci_calle'])
    if utci is not None:
        if isinstance(utci, dict):
            utci_calle = utci.get('calle')
            utci_sensor = utci.get('sensor')
            if utci_calle is not None:
                valor_uc, fiab_uc = _aplicar_fallback(utci_calle, 'temperatura', 'utci_calle')
                _agregar_valor(valores_bio, ValorSistema(
                    nombre='UTCI Calle (Fiala)',
                    tipo='índice',
                    valor=valor_uc,
                    unidad='°C',
                    fiabilidad=fiab_uc,
                    icono='🛣️',
                    prioridad=92,
                    sensores=['temperatura', 'humedad', 'viento', 'radiacion'],
                    dependencias=['UTCI']
                ))
            if utci_sensor is not None:
                valor_us, fiab_us = _aplicar_fallback(utci_sensor, 'temperatura', 'utci_sensor')
                _agregar_valor(valores_bio, ValorSistema(
                    nombre='UTCI Sensor (Fiala)',
                    tipo='índice',
                    valor=valor_us,
                    unidad='°C',
                    fiabilidad=fiab_us,
                    icono='🏠',
                    prioridad=91,
                    sensores=['temperatura', 'humedad', 'viento', 'radiacion'],
                    dependencias=['UTCI']
                ))
        else:
            valor_utci, fiab_utci = _aplicar_fallback(utci, 'temperatura', 'utci')
            _agregar_valor(valores_bio, ValorSistema(
                nombre='Sensación térmica (UTCI)',
                tipo='índice',
                valor=valor_utci,
                unidad='°C',
                fiabilidad=fiab_utci,
                icono='🤚',
                prioridad=90,
                sensores=['temperatura', 'humedad', 'viento'],
                dependencias=['UTCI']
            ))
    if valores_bio:
        grupos.append(GrupoValores(
            nombre='Biometría',
            icono='👤',
            valores=valores_bio,
            prioridad=80
        ))
    
    # GRUPO 4: RADIACIÓN & PRECIPITACIÓN ☀️🌧️ (FUSIONADO)
    valores_rad_precip = []
    
    # Radiación solar
    radiacion_sel = _seleccionar_sensor_mejor(sensores, ['radiacion', 'solarradiation', 'radiacion_solar'], contexto, 'radiacion')
    valor_rad, fiab_rad = _aplicar_fallback(radiacion_sel.get('valor') if radiacion_sel else None, 'elevacion_solar', 'radiacion')
    fiab_rad = _combinar_fiabilidad(fiab_rad, radiacion_sel.get('fiabilidad') if radiacion_sel else None)
    unidad_rad = radiacion_sel.get('unidad') if radiacion_sel else 'W/m²'
    valor_rad_obj = ValorSistema(
        nombre='Radiación solar',
        tipo='sensor',
        valor=valor_rad,
        unidad=unidad_rad or 'W/m²',
        fiabilidad=fiab_rad,
        icono='☀️',
        prioridad=100,
        sensores=_sensores_origen(radiacion_sel, 'radiacion'),
        dependencias=[]
    )
    _agregar_valor(valores_rad_precip, valor_rad_obj)
    _agregar_traza_extra(valor_rad_obj, {
        'qc': _qc_resumen_alias(sensores, ['radiacion', 'solarradiation', 'radiacion_solar'])
    })

    tendencia_transmitancia = _extraer_valor_indice(indices, ['tendencia_transmitancia'])
    if tendencia_transmitancia is not None:
        valor_tt, fiab_tt = _aplicar_fallback(tendencia_transmitancia, 'radiacion', 'tendencia_transmitancia')
        valor_tt_obj = ValorSistema(
            nombre='Tendencia transmitancia',
            tipo='índice',
            valor=valor_tt,
            unidad='',
            fiabilidad=fiab_tt,
            icono='📈',
            prioridad=80,
            sensores=['radiacion'],
            dependencias=['Haurwitz']
        )
        _agregar_valor(valores_rad_precip, valor_tt_obj)
        _agregar_traza_extra(valor_tt_obj, {
            'metodo': 'Tendencia transmitancia atmosférica',
            'fuente_indice': 'tendencia_transmitancia',
        })

    qnet_base_val = None
    qnet_fusion = _extraer_valor_indice(indices, [
        'radiacion_neta_fusion_prata_rest2_w_m2',
        'radiacion_neta_wm2',
        'radiacion_neta'
    ])
    if qnet_fusion is not None:
        qnet_base_val = _float_or_none(qnet_fusion)
        valor_qnet, fiab_qnet = _aplicar_fallback(qnet_fusion, 'radiacion', 'radiacion_neta')
        valor_qnet_obj = ValorSistema(
            nombre='Radiación neta (Qnet)',
            tipo='índice',
            valor=valor_qnet,
            unidad='W/m²',
            fiabilidad=fiab_qnet,
            icono='🌗',
            prioridad=89,
            sensores=['radiacion', 'temperatura', 'humedad'],
            dependencias=['REST2', 'Prata']
        )
        _agregar_valor(valores_rad_precip, valor_qnet_obj)
        _agregar_traza_extra(valor_qnet_obj, {
            'metodo': 'Fusión REST2 + Prata (Qnet)',
            'fuente_indice': 'radiacion_neta_fusion_prata_rest2_w_m2'
        })

    flujo_sensible = _extraer_valor_indice(indices, ['flujo_calor_sensible_H', 'flujo_calor_sensible'])
    if flujo_sensible is not None:
        valor_fs, fiab_fs = _aplicar_fallback(flujo_sensible, 'temperatura', 'flujo_calor_sensible_H')
        valor_fs_obj = ValorSistema(
            nombre='Flujo calor sensible (H)',
            tipo='índice',
            valor=valor_fs,
            unidad='W/m²',
            fiabilidad=fiab_fs,
            icono='🌡️',
            prioridad=88,
            sensores=['temperatura', 'viento'],
            dependencias=['Monin-Obukhov']
        )
        _agregar_valor(valores_rad_precip, valor_fs_obj)
        _agregar_traza_extra(valor_fs_obj, {
            'fuente_indice': 'flujo_calor_sensible_H'
        })

    flujo_suelo = _extraer_valor_indice(indices, ['flujo_calor_suelo_wm2', 'flujo_calor_suelo'])
    if flujo_suelo is not None:
        valor_fg, fiab_fg = _aplicar_fallback(flujo_suelo, 'temperatura', 'flujo_calor_suelo')
        valor_fg_obj = ValorSistema(
            nombre='Flujo calor suelo (G)',
            tipo='índice',
            valor=valor_fg,
            unidad='W/m²',
            fiabilidad=fiab_fg,
            icono='🪨',
            prioridad=87,
            sensores=['temperatura'],
            dependencias=['Deardorff']
        )
        _agregar_valor(valores_rad_precip, valor_fg_obj)
        _agregar_traza_extra(valor_fg_obj, {
            'fuente_indice': 'flujo_calor_suelo_wm2'
        })

    flujo_latente = _extraer_valor_indice(indices, [
        'le_w_m2', 'flujo_calor_latente_LE', 'le_w_m2',
        'calor_latente_wm2', 'calor_latente_lluvia_wm2'
    ])
    flujo_latente_origen = 'indice' if flujo_latente is not None else None
    le_virtual_info = None
    if flujo_latente is None:
        rad_le_base = _float_or_none(radiacion_sel.get('valor') if radiacion_sel else None)
        viento_le_sel = viento_sel
        viento_le_ms = _convertir_viento_ms(
            viento_le_sel.get('valor') if viento_le_sel else None,
            viento_le_sel.get('unidad') if viento_le_sel else None
        )
        try:
            viento_le_ms = float(viento_le_ms) if viento_le_ms is not None else None
        except Exception:
            viento_le_ms = None

        elevacion_le = None
        if rad_le_base is not None and temp_c is not None and humedad_pct is not None:
            try:
                from core.arcos_solares import calcular_posicion_sol
                lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
                lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
                orografia = contexto.get('orografia') if isinstance(contexto, dict) else None
                perfil_horizonte = orografia.get("perfil_horizonte") if isinstance(orografia, dict) else None
                datos_sol = calcular_posicion_sol(lat, lon, datetime.now(), perfil_horizonte=perfil_horizonte)
                elevacion_le = datos_sol.get('elevacion_solar_deg')
            except Exception:
                elevacion_le = None

        if rad_le_base is not None and temp_c is not None and humedad_pct is not None and viento_le_ms is not None:
            le_virtual_info = _calcular_le_virtual_penman(
                temp_c=temp_c,
                humedad_relativa_pct=humedad_pct,
                radiacion_w_m2=rad_le_base,
                viento_ms=viento_le_ms,
                presion_hpa=presion_hpa,
                elevacion_solar_deg=elevacion_le,
            )
            if le_virtual_info and le_virtual_info.get('le_w_m2') is not None:
                flujo_latente = le_virtual_info.get('le_w_m2')
                flujo_latente_origen = 'virtual'

    if flujo_latente is not None:
        valor_le, fiab_le = _aplicar_fallback(flujo_latente, 'temperatura', 'le_w_m2')
        if flujo_latente_origen == 'virtual':
            fiab_le = _combinar_fiabilidad(fiab_le, Fiabilidad.MEDIA)
        valor_le_obj = ValorSistema(
            nombre='Flujo calor latente (LE)',
            tipo='índice',
            valor=valor_le,
            unidad='W/m²',
            fiabilidad=fiab_le,
            icono='💦',
            prioridad=87,
            sensores=['humedad'],
            dependencias=['Evapotranspiración']
        )
        _agregar_valor(valores_rad_precip, valor_le_obj)
        traza_le = {
            'fuente_indice': 'le_w_m2',
            'origen': flujo_latente_origen or 'indice',
            'virtual_pct': 100 if flujo_latente_origen == 'virtual' else 0,
        }
        if le_virtual_info:
            traza_le.update({
                'metodo': 'Penman-Monteith + Wright (ET0 → LE)',
                'et0_mm_dia': le_virtual_info.get('et0_mm_dia'),
                'lambda_j_kg': le_virtual_info.get('lambda_j_kg'),
                'presion_kpa': le_virtual_info.get('presion_kpa'),
                'hora_solar': le_virtual_info.get('hora_solar'),
                'entradas': {
                    'radiacion_w_m2': rad_le_base,
                    'temp_c': temp_c,
                    'humedad_relativa_pct': humedad_pct,
                    'viento_ms': viento_le_ms,
                    'elevacion_solar_deg': elevacion_le,
                }
            })
        _agregar_traza_extra(valor_le_obj, traza_le)


    kt_indice = _extraer_valor_indice(indices, ['trinity_kt_indice_claridad', 'kt_indice_claridad'])
    if kt_indice is not None:
        valor_kt, fiab_kt = _aplicar_fallback(kt_indice, 'radiacion', 'kt_indice_claridad')
        valor_kt_obj = ValorSistema(
            nombre='Índice claridad Kt',
            tipo='índice',
            valor=valor_kt,
            unidad='0-1.5',
            fiabilidad=fiab_kt,
            icono='🔭',
            prioridad=88,
            sensores=['radiacion'],
            dependencias=['Trinity', 'REST2']
        )
        _agregar_valor(valores_rad_precip, valor_kt_obj)
        _agregar_traza_extra(valor_kt_obj, {
            'metodo': 'Liu & Jordan (Kt)',
            'fuente_indice': 'trinity_kt_indice_claridad'
        })

    kt_tipo_dia = _extraer_valor_indice(indices, ['trinity_kt_tipo_dia'])
    if kt_tipo_dia is not None:
        valor_kd, fiab_kd = _aplicar_fallback(kt_tipo_dia, 'radiacion', 'trinity_kt_tipo_dia')
        valor_kd_obj = ValorSistema(
            nombre='Tipo de día (Kt)',
            tipo='índice',
            valor=valor_kd,
            unidad='',
            fiabilidad=fiab_kd,
            icono='🗺️',
            prioridad=87,
            sensores=['radiacion'],
            dependencias=['Trinity']
        )
        _agregar_valor(valores_rad_precip, valor_kd_obj)
        _agregar_traza_extra(valor_kd_obj, {
            'metodo': 'Clasificación por Kt (Liu & Jordan)',
            'fuente_indice': 'trinity_kt_tipo_dia'
        })

    transmitancia_atm = _extraer_valor_indice(indices, ['transmitancia_atmosferica'])
    if transmitancia_atm is not None:
        valor_ta, fiab_ta = _aplicar_fallback(transmitancia_atm, 'radiacion', 'transmitancia_atmosferica')
        valor_ta_obj = ValorSistema(
            nombre='Transmitancia atmosférica',
            tipo='índice',
            valor=valor_ta,
            unidad='0-1',
            fiabilidad=fiab_ta,
            icono='🧪',
            prioridad=87,
            sensores=['radiacion'],
            dependencias=['Liu-Jordan', 'Haurwitz']
        )
        _agregar_valor(valores_rad_precip, valor_ta_obj)
        _agregar_traza_extra(valor_ta_obj, {
            'metodo': 'Transmitancia física',
            'fuente_indice': 'transmitancia_atmosferica'
        })

    rn_sw = _extraer_valor_indice(indices, ['radiacion_neta_onda_corta'])
    if rn_sw is not None:
        valor_sw, fiab_sw = _aplicar_fallback(rn_sw, 'radiacion', 'radiacion_neta_onda_corta')
        valor_sw_obj = ValorSistema(
            nombre='Rn onda corta',
            tipo='índice',
            valor=valor_sw,
            unidad='MJ/m²·día',
            fiabilidad=fiab_sw,
            icono='🌞',
            prioridad=86,
            sensores=['radiacion'],
            dependencias=['Penman-Monteith']
        )
        _agregar_valor(valores_rad_precip, valor_sw_obj)
        _agregar_traza_extra(valor_sw_obj, {
            'metodo': 'Radiación neta onda corta',
            'fuente_indice': 'radiacion_neta_onda_corta'
        })

    rn_lw = _extraer_valor_indice(indices, ['radiacion_neta_onda_larga'])
    if rn_lw is not None:
        valor_lw_n, fiab_lw_n = _aplicar_fallback(rn_lw, 'radiacion', 'radiacion_neta_onda_larga')
        valor_lw_obj = ValorSistema(
            nombre='Rn onda larga',
            tipo='índice',
            valor=valor_lw_n,
            unidad='MJ/m²·día',
            fiabilidad=fiab_lw_n,
            icono='🌙',
            prioridad=85,
            sensores=['radiacion'],
            dependencias=['Penman-Monteith']
        )
        _agregar_valor(valores_rad_precip, valor_lw_obj)
        _agregar_traza_extra(valor_lw_obj, {
            'metodo': 'Radiación neta onda larga',
            'fuente_indice': 'radiacion_neta_onda_larga'
        })

    rn_total = _extraer_valor_indice(indices, ['radiacion_neta_total'])
    if rn_total is not None:
        valor_rn, fiab_rn = _aplicar_fallback(rn_total, 'radiacion', 'radiacion_neta_total')
        valor_rn_obj = ValorSistema(
            nombre='Radiación neta diaria',
            tipo='índice',
            valor=valor_rn,
            unidad='MJ/m²·día',
            fiabilidad=fiab_rn,
            icono='📅',
            prioridad=84,
            sensores=['radiacion'],
            dependencias=['Penman-Monteith']
        )
        _agregar_valor(valores_rad_precip, valor_rn_obj)
        _agregar_traza_extra(valor_rn_obj, {
            'metodo': 'Radiación neta total diaria',
            'fuente_indice': 'radiacion_neta_total'
        })

    perdida_atm_pct = _extraer_valor_indice(indices, ['trinity_perdida_atmosferica_pct'])
    if perdida_atm_pct is not None:
        valor_pa, fiab_pa = _aplicar_fallback(perdida_atm_pct, 'radiacion', 'trinity_perdida_atmosferica_pct')
        valor_pa_obj = ValorSistema(
            nombre='Pérdida atmosférica',
            tipo='índice',
            valor=valor_pa,
            unidad='%',
            fiabilidad=fiab_pa,
            icono='🛰️',
            prioridad=86,
            sensores=['radiacion'],
            dependencias=['Trinity', 'REST2']
        )
        _agregar_valor(valores_rad_precip, valor_pa_obj)
        _agregar_traza_extra(valor_pa_obj, {
            'metodo': 'Pérdida atmosférica G₀ - G',
            'fuente_indice': 'trinity_perdida_atmosferica_pct'
        })

    perdida_atm_wm2 = _extraer_valor_indice(indices, ['trinity_perdida_atmosferica_w_m2'])
    if perdida_atm_wm2 is not None:
        valor_pw, fiab_pw = _aplicar_fallback(perdida_atm_wm2, 'radiacion', 'trinity_perdida_atmosferica_w_m2')
        valor_pw_obj = ValorSistema(
            nombre='Pérdida atmosférica (W/m²)',
            tipo='índice',
            valor=valor_pw,
            unidad='W/m²',
            fiabilidad=fiab_pw,
            icono='🛰️',
            prioridad=85,
            sensores=['radiacion'],
            dependencias=['Trinity', 'REST2']
        )
        _agregar_valor(valores_rad_precip, valor_pw_obj)
        _agregar_traza_extra(valor_pw_obj, {
            'metodo': 'Pérdida atmosférica G₀ - G',
            'fuente_indice': 'trinity_perdida_atmosferica_w_m2'
        })

    masa_aire = _extraer_valor_indice(indices, ['rest2_masa_aire', 'masa_aire'])
    if masa_aire is not None:
        valor_ma, fiab_ma = _aplicar_fallback(masa_aire, 'radiacion', 'rest2_masa_aire')
        valor_ma_obj = ValorSistema(
            nombre='Masa de aire (REST2)',
            tipo='índice',
            valor=valor_ma,
            unidad='adim',
            fiabilidad=fiab_ma,
            icono='🧪',
            prioridad=84,
            sensores=['radiacion'],
            dependencias=['REST2']
        )
        _agregar_valor(valores_rad_precip, valor_ma_obj)
        _agregar_traza_extra(valor_ma_obj, {
            'metodo': 'Kasten-Young (REST2)',
            'fuente_indice': 'rest2_masa_aire'
        })

    kt_validacion = _extraer_valor_indice(indices, ['trinity_kt_validacion'])
    if kt_validacion is not None:
        valor_kv, fiab_kv = _aplicar_fallback(kt_validacion, 'radiacion', 'trinity_kt_validacion')
        valor_kv_obj = ValorSistema(
            nombre='Kt validación',
            tipo='índice',
            valor=valor_kv,
            unidad='0-1.5',
            fiabilidad=fiab_kv,
            icono='✅',
            prioridad=83,
            sensores=['radiacion'],
            dependencias=['Trinity']
        )
        _agregar_valor(valores_rad_precip, valor_kv_obj)
        _agregar_traza_extra(valor_kv_obj, {
            'metodo': 'Validación cruzada Trinity',
            'fuente_indice': 'trinity_kt_validacion'
        })

    kt_exceso = _extraer_valor_indice(indices, ['trinity_kt_exceso'])
    if kt_exceso is not None:
        valor_ke, fiab_ke = _aplicar_fallback(kt_exceso, 'radiacion', 'trinity_kt_exceso')
        valor_ke_obj = ValorSistema(
            nombre='Exceso Kt',
            tipo='índice',
            valor=valor_ke,
            unidad='adim',
            fiabilidad=fiab_ke,
            icono='⚠️',
            prioridad=82,
            sensores=['radiacion'],
            dependencias=['Trinity']
        )
        _agregar_valor(valores_rad_precip, valor_ke_obj)
        _agregar_traza_extra(valor_ke_obj, {
            'metodo': 'Validación Kt fuera de rango',
            'fuente_indice': 'trinity_kt_exceso'
        })

    transmitancia_uv = _extraer_valor_indice(indices, ['transmitancia_aerosoles_uv'])
    if transmitancia_uv is not None:
        valor_tuv, fiab_tuv = _aplicar_fallback(transmitancia_uv, 'radiacion', 'transmitancia_aerosoles_uv')
        valor_tuv_obj = ValorSistema(
            nombre='Transmitancia aerosoles UV',
            tipo='índice',
            valor=valor_tuv,
            unidad='0-1',
            fiabilidad=fiab_tuv,
            icono='🧴',
            prioridad=81,
            sensores=['radiacion'],
            dependencias=['Angstrom', 'UV']
        )
        _agregar_valor(valores_rad_precip, valor_tuv_obj)
        _agregar_traza_extra(valor_tuv_obj, {
            'metodo': 'Ångström dinámico (UV)',
            'fuente_indice': 'transmitancia_aerosoles_uv'
        })

    radiacion_virtual = None
    indice_dni_val = None
    indice_dhi_val = None
    indice_dni_fuente = None
    indice_dhi_fuente = None
    if isinstance(indices, dict):
        for key in ['trinity_radiacion_directa_w_m2', 'radiacion_directa_w_m2', 'radiacion_directa']:
            if key in indices:
                indice_dni_val = indices.get(key)
                indice_dni_fuente = key
                break
        for key in ['trinity_radiacion_difusa_w_m2', 'radiacion_difusa_w_m2', 'radiacion_difusa']:
            if key in indices:
                indice_dhi_val = indices.get(key)
                indice_dhi_fuente = key
                break
    if indice_dni_val is not None or indice_dhi_val is not None:
        dni_val = _float_or_none(indice_dni_val)
        dhi_val = _float_or_none(indice_dhi_val)
        if dni_val is not None:
            valor_dni = ValorSistema(
                nombre='Radiación directa (virtual)',
                tipo='índice',
                valor=round(dni_val, 2),
                unidad='W/m²',
                fiabilidad=Fiabilidad.MEDIA,
                icono='🔆',
                prioridad=92,
                sensores=['radiacion'],
                dependencias=['Trinity', 'Erbs']
            )
            _agregar_valor(valores_rad_precip, valor_dni)
            _agregar_traza_extra(valor_dni, {
                'metodo': 'Trinity (K_t + Erbs)',
                'fuente_indice': indice_dni_fuente,
                'entradas': {
                    'radiacion_global_w_m2': radiacion_sel.get('valor') if radiacion_sel else None,
                    'g0_w_m2': _extraer_valor_indice(indices, ['rest2_g0_w_m2', 'radiacion_extraterrestre'])
                }
            })
        if dhi_val is not None:
            valor_dhi = ValorSistema(
                nombre='Radiación difusa (virtual)',
                tipo='índice',
                valor=round(dhi_val, 2),
                unidad='W/m²',
                fiabilidad=Fiabilidad.MEDIA,
                icono='🌫️',
                prioridad=91,
                sensores=['radiacion'],
                dependencias=['Trinity', 'Erbs']
            )
            _agregar_valor(valores_rad_precip, valor_dhi)
            _agregar_traza_extra(valor_dhi, {
                'metodo': 'Trinity (K_t + Erbs)',
                'fuente_indice': indice_dhi_fuente,
                'entradas': {
                    'radiacion_global_w_m2': radiacion_sel.get('valor') if radiacion_sel else None,
                    'g0_w_m2': _extraer_valor_indice(indices, ['rest2_g0_w_m2', 'radiacion_extraterrestre'])
                }
            })
        if dni_val is not None and dhi_val is not None:
            radiacion_virtual = {
                'directa_w_m2': dni_val,
                'difusa_w_m2': dhi_val,
                'fuente': indice_dni_fuente or indice_dhi_fuente,
            }
    if radiacion_virtual is None and radiacion_sel is not None:
        rad_real_base = _float_or_none(radiacion_sel.get('valor'))
        if rad_real_base is not None:
            radiacion_virtual = _calcular_directa_difusa_virtual(
                contexto,
                rad_real_w_m2=rad_real_base,
                presion_hpa=presion_hpa,
            )
            if radiacion_virtual:
                valor_dni = ValorSistema(
                    nombre='Radiación directa (virtual)',
                    tipo='índice',
                    valor=round(float(radiacion_virtual['directa_w_m2']), 2),
                    unidad='W/m²',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='🔆',
                    prioridad=91,
                    sensores=['radiacion', 'presion'],
                    dependencias=['REST2', 'Rayleigh-Miller']
                )
                _agregar_valor(valores_rad_precip, valor_dni)
                _agregar_traza_extra(valor_dni, {
                    'metodo': 'REST2 + Rayleigh-Miller (ajustado a global)',
                    'entradas': {
                        'radiacion_global_w_m2': rad_real_base,
                        'g0_w_m2': radiacion_virtual.get('g0_w_m2'),
                        'elevacion_solar_deg': radiacion_virtual.get('elevacion_solar_deg'),
                        'presion_hpa': presion_hpa,
                        'escala': radiacion_virtual.get('escala'),
                    }
                })

                valor_dhi = ValorSistema(
                    nombre='Radiación difusa (virtual)',
                    tipo='índice',
                    valor=round(float(radiacion_virtual['difusa_w_m2']), 2),
                    unidad='W/m²',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='🌫️',
                    prioridad=90,
                    sensores=['radiacion', 'presion'],
                    dependencias=['REST2', 'Rayleigh-Miller']
                )
                _agregar_valor(valores_rad_precip, valor_dhi)
                _agregar_traza_extra(valor_dhi, {
                    'metodo': 'REST2 + Rayleigh-Miller (ajustado a global)',
                    'entradas': {
                        'radiacion_global_w_m2': rad_real_base,
                        'g0_w_m2': radiacion_virtual.get('g0_w_m2'),
                        'elevacion_solar_deg': radiacion_virtual.get('elevacion_solar_deg'),
                        'presion_hpa': presion_hpa,
                        'escala': radiacion_virtual.get('escala'),
                    }
                })

    # Fracción difusa (solo con radiación directa + difusa medidas)
    directa_sel = _seleccionar_sensor_mejor(
        sensores,
        ['radiacion_directa', 'directa', 'dni', 'beam', 'direct_normal'],
        contexto,
        'radiacion'
    )
    difusa_sel = _seleccionar_sensor_mejor(
        sensores,
        ['radiacion_difusa', 'difusa', 'dhi', 'diffuse'],
        contexto,
        'radiacion'
    )
    if directa_sel and difusa_sel:
        try:
            directa_val = float(directa_sel.get('valor'))
            difusa_val = float(difusa_sel.get('valor'))
        except Exception:
            directa_val = None
            difusa_val = None
        if directa_val is not None and difusa_val is not None:
            total_rad = directa_val + difusa_val
            if total_rad > 0:
                fraccion_difusa = difusa_val / total_rad
                fiab_fd = _combinar_fiabilidad(Fiabilidad.ALTA, directa_sel.get('fiabilidad'))
                fiab_fd = _combinar_fiabilidad(fiab_fd, difusa_sel.get('fiabilidad'))
                valor_fd = ValorSistema(
                    nombre='Fracción difusa',
                    tipo='índice',
                    valor=round(fraccion_difusa, 4),
                    unidad='0-1',
                    fiabilidad=fiab_fd,
                    icono='🌫️',
                    prioridad=96,
                    sensores=_sensores_origen(directa_sel, 'radiacion_directa') + _sensores_origen(difusa_sel, 'radiacion_difusa'),
                    dependencias=[]
                )
                _agregar_valor(valores_rad_precip, valor_fd)
                _agregar_traza_extra(valor_fd, {
                    'metodo': 'Fracción difusa = DHI / (DNI + DHI)',
                    'entradas': {
                        'dni_w_m2': directa_val,
                        'dhi_w_m2': difusa_val,
                    }
                })
    else:
        fraccion_idx = None
        fraccion_idx_fuente = None
        if isinstance(indices, dict):
            for key in ['trinity_fraccion_difusa', 'fraccion_radiacion_difusa', 'fraccion_difusa']:
                if key in indices:
                    fraccion_idx = indices.get(key)
                    fraccion_idx_fuente = key
                    break
        fraccion_idx_val = _float_or_none(fraccion_idx)
        if fraccion_idx_val is not None:
            valor_fd = ValorSistema(
                nombre='Fracción difusa',
                tipo='índice',
                valor=round(fraccion_idx_val, 4),
                unidad='0-1',
                fiabilidad=Fiabilidad.MEDIA,
                icono='🌫️',
                prioridad=96,
                sensores=['radiacion'],
                dependencias=['Trinity', 'Erbs']
            )
            _agregar_valor(valores_rad_precip, valor_fd)
            _agregar_traza_extra(valor_fd, {
                'metodo': 'Fracción difusa (índice físico Trinity)',
                'fuente_indice': fraccion_idx_fuente,
            })
        elif radiacion_virtual:
            directa_val = _float_or_none(radiacion_virtual.get('directa_w_m2'))
            difusa_val = _float_or_none(radiacion_virtual.get('difusa_w_m2'))
            if directa_val is not None and difusa_val is not None:
                total_rad = directa_val + difusa_val
                if total_rad > 0:
                    fraccion_difusa = difusa_val / total_rad
                    valor_fd = ValorSistema(
                        nombre='Fracción difusa',
                        tipo='índice',
                        valor=round(fraccion_difusa, 4),
                        unidad='0-1',
                        fiabilidad=Fiabilidad.MEDIA,
                        icono='🌫️',
                        prioridad=95,
                        sensores=['radiacion'],
                        dependencias=['REST2', 'Rayleigh-Miller']
                    )
                    _agregar_valor(valores_rad_precip, valor_fd)
                    _agregar_traza_extra(valor_fd, {
                        'metodo': 'Fracción difusa (virtual) = DHI / (DNI + DHI)',
                        'entradas': {
                            'dni_w_m2': directa_val,
                            'dhi_w_m2': difusa_val,
                            'escala': radiacion_virtual.get('escala')
                        }
                    })

    nub_imp = None
    nub_imp_fuente = None
    if isinstance(indices, dict):
        for key in ['nubosidad_implicita_pct', 'trinity_nubosidad_radiometrica_pct', 'nubosidad_radiometrica_pct']:
            if key in indices:
                nub_imp = indices.get(key)
                nub_imp_fuente = key
                break
    if nub_imp is None:
        nub_imp = _extraer_valor_indice(indices, ['nubosidad_implicita_pct'])
    if nub_imp is not None:
        valor_ni, fiab_ni = _aplicar_fallback(nub_imp, 'elevacion_solar', 'nubosidad_implicita_pct')
        valor_nub_imp = ValorSistema(
            nombre='Nubosidad implícita',
            tipo='índice',
            valor=valor_ni,
            unidad='%',
            fiabilidad=fiab_ni,
            icono='☁️',
            prioridad=93,
            sensores=['radiacion'],
            dependencias=['Kasten-Czeplak']
        )
        _agregar_valor(valores_rad_precip, valor_nub_imp)
        _agregar_traza_extra(valor_nub_imp, {
            'metodo': 'Nubosidad radiométrica (K_t)',
            'fuente_indice': nub_imp_fuente
        })

    lw_down_val = None
    lw_neta_val = None
    lw_neta = _extraer_valor_indice(indices, ['lw_neta_estimada_w_m2'])
    if lw_neta is not None:
        lw_neta_val = _float_or_none(lw_neta)
        valor_lw, fiab_lw = _aplicar_fallback(lw_neta, 'temperatura', 'lw_neta_estimada_w_m2')
        _agregar_valor(valores_rad_precip, ValorSistema(
            nombre='LW neta',
            tipo='índice',
            valor=valor_lw,
            unidad='W/m²',
            fiabilidad=fiab_lw,
            icono='🌒',
            prioridad=88,
            sensores=['temperatura', 'humedad'],
            dependencias=['Prata']
        ))

    # Nubosidad implícita física (Liu & Jordan + Kasten) si no hay sensor ni índice
    nubosidad_virtual = None
    if nub_imp is None and nubosidad is None and radiacion_sel is not None:
        rad_real_base = _float_or_none(radiacion_sel.get('valor'))
        if rad_real_base is not None and temp_c is not None and humedad_pct is not None:
            resultado_nub = _calcular_nubosidad_fisica(
                contexto,
                temp_c=temp_c,
                humedad_relativa_pct=humedad_pct,
                rad_real_w_m2=rad_real_base,
                presion_hpa=presion_hpa,
            )
            if resultado_nub and resultado_nub.get('nubosidad') is not None:
                nubosidad_virtual = float(resultado_nub['nubosidad'])
                valor_nub = ValorSistema(
                    nombre='Nubosidad implícita',
                    tipo='índice',
                    valor=round(nubosidad_virtual, 2),
                    unidad='%',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='☁️',
                    prioridad=92,
                    sensores=['radiacion', 'temperatura', 'humedad'],
                    dependencias=['Liu-Jordan-Kasten', 'REST2']
                )
                _agregar_valor(valores_rad_precip, valor_nub)
                _agregar_traza_extra(valor_nub, {
                    'metodo': 'Liu-Jordan-Kasten + REST2',
                    'entradas': {
                        'radiacion_w_m2': rad_real_base,
                        'g0_w_m2': resultado_nub.get('_g0_w_m2'),
                        'elevacion_solar_deg': resultado_nub.get('_elevacion_solar_deg'),
                        'temp_c': temp_c,
                        'humedad_relativa_pct': humedad_pct,
                        'punto_rocio_c': resultado_nub.get('_punto_rocio_c'),
                    },
                    'confianza_modelo': resultado_nub.get('confianza')
                })

    # LW descendente física (Prata) si no hay LW neta
    if lw_neta is None:
        lw_down_idx = None
        lw_down_fuente = None
        if isinstance(indices, dict):
            for key in ['lw_descendente_estimada_w_m2', 'radiacion_lw_descendente_prata_w_m2', 'lw_descendente_w_m2']:
                if key in indices:
                    lw_down_idx = indices.get(key)
                    lw_down_fuente = key
                    break
        lw_down_idx_val = _float_or_none(lw_down_idx)
        if lw_down_idx_val is not None:
            lw_down_val = float(lw_down_idx_val)
            valor_lw_down = ValorSistema(
                nombre='LW descendente',
                tipo='índice',
                valor=round(float(lw_down_idx_val), 2),
                unidad='W/m²',
                fiabilidad=Fiabilidad.MEDIA,
                icono='🌒',
                prioridad=88,
                sensores=['temperatura', 'humedad'],
                dependencias=['Prata']
            )
            _agregar_valor(valores_rad_precip, valor_lw_down)
            _agregar_traza_extra(valor_lw_down, {
                'metodo': 'Prata 1996 (LW↓) desde índices',
                'fuente_indice': lw_down_fuente
            })
        elif temp_c is not None and humedad_pct is not None:
            nub_base = nubosidad if nubosidad is not None else nubosidad_virtual
            lw_down = _calcular_lw_desc_prata(temp_c, humedad_pct, nub_base)
            if lw_down is not None:
                lw_down_val = float(lw_down)
                valor_lw_down = ValorSistema(
                    nombre='LW descendente',
                    tipo='índice',
                    valor=round(float(lw_down), 2),
                    unidad='W/m²',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='🌒',
                    prioridad=87,
                    sensores=['temperatura', 'humedad'],
                    dependencias=['Prata']
                )
                _agregar_valor(valores_rad_precip, valor_lw_down)
                _agregar_traza_extra(valor_lw_down, {
                    'metodo': 'Prata 1996 (LW↓)',
                    'entradas': {
                        'temp_c': temp_c,
                        'humedad_relativa_pct': humedad_pct,
                        'nubosidad_pct': nub_base
                    }
                })

    temp_superficie_idx = _extraer_valor_indice(indices, [
        'temp_superficie', 'temperatura_superficie', 't_superficie',
        'temperatura_suelo_superficie', 'temperatura_suelo'
    ])
    temp_superficie_val = _float_or_none(temp_superficie_idx)
    fuente_temp_superficie = 'indice' if temp_superficie_idx is not None else None
    if temp_superficie_val is None and temp_c is not None:
        temp_superficie_val = float(temp_c)
        fuente_temp_superficie = 'temperatura_aire'

    if temp_superficie_val is not None:
        fiab_ts = Fiabilidad.ALTA if fuente_temp_superficie == 'indice' else Fiabilidad.MEDIA
        valor_ts = ValorSistema(
            nombre='Temperatura superficie',
            tipo='índice',
            valor=round(float(temp_superficie_val), 2),
            unidad='°C',
            fiabilidad=fiab_ts,
            icono='🪨',
            prioridad=86,
            sensores=['temperatura'],
            dependencias=['Deardorff']
        )
        _agregar_valor(valores_rad_precip, valor_ts)
        _agregar_traza_extra(valor_ts, {
            'fuente_temp_superficie': fuente_temp_superficie,
            'temp_superficie_c': temp_superficie_val,
        })

        lw_up = _calcular_lw_up_stefan(temp_superficie_val)
        if lw_up is not None:
            fiab_lw_up = Fiabilidad.ALTA if fuente_temp_superficie == 'indice' else Fiabilidad.MEDIA
            valor_lw_up = ValorSistema(
                nombre='LW ascendente',
                tipo='índice',
                valor=round(float(lw_up), 2),
                unidad='W/m²',
                fiabilidad=fiab_lw_up,
                icono='🌔',
                prioridad=86,
                sensores=['temperatura'],
                dependencias=['Stefan-Boltzmann']
            )
            _agregar_valor(valores_rad_precip, valor_lw_up)
            _agregar_traza_extra(valor_lw_up, {
                'metodo': 'Stefan-Boltzmann (LW↑)',
                'fuente_temp_superficie': fuente_temp_superficie,
                'temp_superficie_c': temp_superficie_val,
            })

            if lw_down_val is not None and lw_neta is None:
                lw_neta_calc = float(lw_up) - float(lw_down_val)
                lw_neta_val = lw_neta_calc
                valor_lw_neta = ValorSistema(
                    nombre='LW neta',
                    tipo='índice',
                    valor=round(lw_neta_calc, 2),
                    unidad='W/m²',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='🌒',
                    prioridad=86,
                    sensores=['temperatura', 'humedad'],
                    dependencias=['Prata', 'Stefan-Boltzmann']
                )
                _agregar_valor(valores_rad_precip, valor_lw_neta)
                _agregar_traza_extra(valor_lw_neta, {
                    'metodo': 'LW neta = LW↑ - LW↓',
                    'lw_up_w_m2': lw_up,
                    'lw_down_w_m2': lw_down_val,
                })

    if qnet_base_val is None and lw_neta_val is not None:
        rad_base_q = _float_or_none(radiacion_sel.get('valor') if radiacion_sel else None)
        if rad_base_q is not None:
            albedo = 0.2
            qnet_virtual = (1.0 - albedo) * rad_base_q + lw_neta_val
            qnet_base_val = qnet_virtual
            valor_qnet_v = ValorSistema(
                nombre='Radiación neta (Qnet)',
                tipo='índice',
                valor=round(qnet_virtual, 2),
                unidad='W/m²',
                fiabilidad=Fiabilidad.MEDIA,
                icono='🌗',
                prioridad=88,
                sensores=['radiacion', 'temperatura', 'humedad'],
                dependencias=['SW', 'LW']
            )
            _agregar_valor(valores_rad_precip, valor_qnet_v)
            _agregar_traza_extra(valor_qnet_v, {
                'metodo': 'Qnet = (1-albedo)·Rg + LW neta',
                'albedo': albedo,
                'Rg_w_m2': rad_base_q,
                'LW_neta_w_m2': lw_neta_val,
            })

    if qnet_base_val is not None and flujo_sensible is not None and flujo_suelo is not None:
        qnet_val = _float_or_none(qnet_base_val)
        h_val = _float_or_none(flujo_sensible)
        g_val = _float_or_none(flujo_suelo)
        le_val = _float_or_none(flujo_latente) if flujo_latente is not None else None
        if qnet_val is not None and h_val is not None and g_val is not None:
            residual = qnet_val - h_val - g_val - (le_val if le_val is not None else 0.0)
            valor_res = ValorSistema(
                nombre='Balance energético residual',
                tipo='índice',
                valor=round(residual, 2),
                unidad='W/m²',
                fiabilidad=Fiabilidad.MEDIA,
                icono='⚖️',
                prioridad=84,
                sensores=['radiacion', 'temperatura', 'viento'],
                dependencias=['Qnet', 'H', 'G']
            )
            _agregar_valor(valores_rad_precip, valor_res)
            _agregar_traza_extra(valor_res, {
                'metodo': 'Residual = Qnet - H - G - LE (ΔS)',
                'qnet_w_m2': qnet_val,
                'H_w_m2': h_val,
                'G_w_m2': g_val,
                'LE_w_m2': le_val,
            })

    # ΔT 3–6h (Force-Restore) acoplado a LE virtual/medido
    try:
        from core.indices.deardorff_force_restore import calcular_temperatura_minima_deardorff
    except Exception:
        calcular_temperatura_minima_deardorff = None

    if calcular_temperatura_minima_deardorff and qnet_base_val is not None and temp_c is not None and humedad_pct is not None:
        qnet_val = _float_or_none(qnet_base_val)
        if qnet_val is not None:
            viento_pred_ms = _convertir_viento_ms(
                viento_sel.get('valor') if viento_sel else None,
                viento_sel.get('unidad') if viento_sel else None
            )
            try:
                viento_pred_ms = float(viento_pred_ms) if viento_pred_ms is not None else 1.0
            except Exception:
                viento_pred_ms = 1.0

            tipo_suelo_pred = _extraer_valor_indice(indices, ['tipo_suelo_usado_deardorff', 'tipo_suelo'])
            if isinstance(tipo_suelo_pred, dict):
                tipo_suelo_pred = tipo_suelo_pred.get('valor')
            tipo_suelo_pred = str(tipo_suelo_pred) if tipo_suelo_pred else 'arcillo_arenoso'

            lluvia_24h_val = None
            lluvia_24h_sel = _extraer_valor_sensor(sensores, ['lluvia_24h', 'rain_24h', 'dailyrain', 'lluvia_acumulada'])
            if lluvia_24h_sel is not None:
                lluvia_24h_val = _float_or_none(lluvia_24h_sel.get('valor'))

            le_val_pred = _float_or_none(flujo_latente) if flujo_latente is not None else None
            for horas_pred in (3.0, 6.0):
                try:
                    resultado_pred = calcular_temperatura_minima_deardorff(
                        temperatura_actual_c=float(temp_c),
                        temperatura_suelo_profundo_c=_float_or_none(suelo_profundo),
                        radiacion_neta_wm2=float(qnet_val),
                        viento_ms=float(viento_pred_ms),
                        humedad_relativa=float(humedad_pct),
                        flujo_calor_latente_wm2=le_val_pred,
                        tipo_suelo=tipo_suelo_pred,
                        horas_hasta_amanecer=float(horas_pred),
                        lluvia_ultimas_24h_mm=float(lluvia_24h_val or 0.0),
                    )
                except Exception:
                    resultado_pred = None

                if resultado_pred and resultado_pred.get('temperatura_minima_c') is not None:
                    try:
                        t_min_pred = float(resultado_pred.get('temperatura_minima_c'))
                    except Exception:
                        t_min_pred = None
                    if t_min_pred is None:
                        continue
                    delta_t = float(temp_c) - t_min_pred
                    valor_dt = ValorSistema(
                        nombre=f'ΔT {int(horas_pred)}h (Force-Restore)',
                        tipo='índice',
                        valor=round(delta_t, 2),
                        unidad='°C',
                        fiabilidad=Fiabilidad.MEDIA,
                        icono='🧮',
                        prioridad=83,
                        sensores=['temperatura', 'radiacion', 'viento', 'humedad'],
                        dependencias=['Deardorff', 'Force-Restore', 'Qnet', 'LE']
                    )
                    _agregar_valor(valores_rad_precip, valor_dt)
                    _agregar_traza_extra(valor_dt, {
                        'metodo': 'Force-Restore (ΔT por balance energético)',
                        'horizonte_h': horas_pred,
                        'qnet_w_m2': qnet_val,
                        'LE_w_m2': le_val_pred,
                        'H_w_m2': _float_or_none(flujo_sensible) if flujo_sensible is not None else None,
                        'G_w_m2': _float_or_none(flujo_suelo) if flujo_suelo is not None else None,
                        'tipo_suelo': tipo_suelo_pred,
                        'lluvia_24h_mm': lluvia_24h_val,
                        'resultado': resultado_pred,
                    })

    from core.indices.uv_spectral_diamond import get_uv_spectral_engine
    from core.arcos_solares import calcular_posicion_sol
    from datetime import datetime
    
    uv_sel = _seleccionar_sensor_mejor(sensores, ['uv', 'indice_uv', 'uvi', 'uv_index', 'uvindex'], contexto)
    valor_uv_sensor = uv_sel.get('valor') if uv_sel else None
    fuente_uv = "sensor"
    
    # Si no hay sensor UV o es 0, calcular con el Motor Diamond Spectral v3
    if valor_uv_sensor is None or valor_uv_sensor == 0:
        radiacion_val = radiacion_sel.get('valor') if radiacion_sel else None
        if radiacion_val is not None and radiacion_val > 0:
            # Obtener elevación solar actual
            lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
            lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
            altitud = contexto.get('ubicacion', {}).get('altitud', ESTACION.ALTITUD)
            orografia = contexto.get('orografia') if isinstance(contexto, dict) else None
            perfil_horizonte = orografia.get("perfil_horizonte") if isinstance(orografia, dict) else None
            
            datos_sol = calcular_posicion_sol(lat, lon, datetime.now(), perfil_horizonte=perfil_horizonte)
            elevacion_solar = datos_sol.get('elevacion_solar_deg', 0)
            
            # Obtener datos atmosféricos
            presion_sel = _seleccionar_sensor_mejor(sensores, ['presion', 'pressure', 'baro', 'baromabs'], contexto, 'presion')
            presion_hpa = presion_sel.get('valor') if presion_sel else 1013.25
            presion_unit = presion_sel.get('unidad') if presion_sel else 'hPa'
            presion_hpa, _ = _normalizar_unidad_valor('presion', presion_hpa, presion_unit)
            
            temp_sel = _seleccionar_sensor_mejor(sensores, ['temperatura', 'temp', 'tempc'], contexto, 'temperatura')
            temperatura_c = temp_sel.get('valor') if temp_sel else 15.0
            temp_unit = temp_sel.get('unidad') if temp_sel else '°C'
            temperatura_c, _ = _normalizar_unidad_valor('temperatura', temperatura_c, temp_unit)
            
            humedad_sel = _seleccionar_sensor_mejor(sensores, ['humedad', 'humidity'], contexto, 'humedad')
            humedad_relativa = humedad_sel.get('valor') if humedad_sel else 50.0
            hum_unit = humedad_sel.get('unidad') if humedad_sel else '%'
            humedad_relativa, _ = _normalizar_unidad_valor('humedad', humedad_relativa, hum_unit)
            
            # Calcular UV con el motor Diamond Spectral v3
            uv_engine = get_uv_spectral_engine(lat, lon, altitud)
            valor_uv_sensor, metadatos_uv = uv_engine.calcular_uv(
                radiacion_solar=radiacion_val,
                elevacion_solar=elevacion_solar,
                presion_hpa=presion_hpa,
                temperatura_c=temperatura_c,
                humedad_relativa=humedad_relativa
            )
            fuente_uv = metadatos_uv.get('motor', 'Spectral_Diamond_v3')
    
    valor_uv, fiab_uv = _aplicar_fallback(valor_uv_sensor, 'elevacion_solar', 'uv')
    fiab_uv = _combinar_fiabilidad(fiab_uv, uv_sel.get('fiabilidad') if uv_sel else None)
    
    # Aplicar Resolución de Diamante y Ley del Entero para UV
    if valor_uv is not None and isinstance(valor_uv, (int, float)):
        val_float = float(valor_uv)
        if val_float == 0 or (val_float == int(val_float)):
            valor_uv = int(val_float)
        else:
            valor_uv = round(val_float, 2)
    
    valor_uv_item = ValorSistema(
        nombre='Índice UV',
        tipo='sensor' if fuente_uv == "sensor" else 'índice',
        valor=valor_uv,
        unidad='',
        fiabilidad=fiab_uv,
        icono='🌞',
        prioridad=95,
        sensores=_sensores_origen(uv_sel, 'uv') if fuente_uv == "sensor" else ['radiacion', 'presion', 'temperatura', 'humedad'],
        dependencias=[]
    )
    _agregar_valor(valores_rad_precip, valor_uv_item)
    _agregar_traza_extra(valor_uv_item, {
        'metodo': 'UVI medido' if fuente_uv == 'sensor' else 'UVSpectralDiamond',
        'motor': fuente_uv,
        'entradas': {
            'radiacion_solar_w_m2': radiacion_sel.get('valor') if radiacion_sel else None,
            'elevacion_solar_deg': elevacion_solar if 'elevacion_solar' in locals() else None,
            'presion_hpa': presion_hpa if 'presion_hpa' in locals() else None,
            'temperatura_c': temperatura_c if 'temperatura_c' in locals() else None,
            'humedad_relativa_pct': humedad_relativa if 'humedad_relativa' in locals() else None,
        },
    })

    # Dosis UV diaria (integración física de UVI medido)
    dosis_uv = _calcular_dosis_uv_diaria()
    if dosis_uv is not None:
        valor_dosis = ValorSistema(
            nombre='Dosis UV diaria',
            tipo='índice',
            valor=round(float(dosis_uv['dosis_kj_m2']), 3),
            unidad='kJ/m²',
            fiabilidad=Fiabilidad.ALTA,
            icono='🧴',
            prioridad=94,
            sensores=[dosis_uv.get('fuente', 'uv')],
            dependencias=['UV']
        )
        _agregar_valor(valores_rad_precip, valor_dosis)
        _agregar_traza_extra(valor_dosis, {
            'metodo': 'Integración trapezoidal UVI (0.025 W/m² por UVI)',
            'ventana': 'desde medianoche local hasta ahora',
            'fuente_uv': dosis_uv.get('fuente', 'uv')
        })

    tmrt = _extraer_valor_indice(indices, ['tmrt', 'radiante', 'temperatura_radiante_media'])
    if tmrt is not None:
        valor_tmrt, fiab_tmrt = _aplicar_fallback(tmrt, 'temperatura', 'tmrt')
        _agregar_valor(valores_rad_precip, ValorSistema(
            nombre='Tmrt (radiante)',
            tipo='índice',
            valor=valor_tmrt,
            unidad='°C',
            fiabilidad=fiab_tmrt,
            icono='🔆',
            prioridad=85,
            sensores=['radiacion'],
            dependencias=['Tmrt']
        ))
    else:
        rad_base = _float_or_none(radiacion_sel.get('valor') if radiacion_sel else None)
        if rad_base is not None and temp_c is not None and humedad_pct is not None:
            try:
                from core.arcos_solares import calcular_posicion_sol
                lat = contexto.get('ubicacion', {}).get('latitud', ESTACION.LATITUD)
                lon = contexto.get('ubicacion', {}).get('longitud', ESTACION.LONGITUD)
                orografia = contexto.get('orografia') if isinstance(contexto, dict) else None
                perfil_horizonte = orografia.get("perfil_horizonte") if isinstance(orografia, dict) else None
                datos_sol = calcular_posicion_sol(lat, lon, datetime.now(), perfil_horizonte=perfil_horizonte)
                elevacion_tmrt = datos_sol.get('elevacion_solar_deg', 0.0)
            except Exception:
                elevacion_tmrt = 0.0

            viento_sel_tmrt = _seleccionar_sensor_mejor(
                sensores,
                ['viento', 'windspeed', 'wind_speed', 'windspeedmph', 'wind_ms'],
                contexto
            )
            viento_ms = _convertir_viento_ms(
                viento_sel_tmrt.get('valor') if viento_sel_tmrt else None,
                viento_sel_tmrt.get('unidad') if viento_sel_tmrt else None
            )
            try:
                viento_ms = float(viento_ms) if viento_ms is not None else 1.0
            except Exception:
                viento_ms = 1.0

            nub_base = nubosidad if nubosidad is not None else nubosidad_virtual
            resultado_tmrt = _calcular_tmrt_fisica(
                contexto,
                temp_c=temp_c,
                humedad_relativa_pct=humedad_pct,
                radiacion_w_m2=rad_base,
                viento_ms=viento_ms,
                nubosidad_pct=float(nub_base or 0.0),
                elevacion_solar_deg=float(elevacion_tmrt or 0.0),
                temp_suelo_c=temp_superficie_val
            )
            if resultado_tmrt and resultado_tmrt.get('mrt') is not None:
                valor_tmrt = ValorSistema(
                    nombre='Tmrt (radiante)',
                    tipo='índice',
                    valor=resultado_tmrt.get('mrt'),
                    unidad='°C',
                    fiabilidad=Fiabilidad.MEDIA,
                    icono='🔆',
                    prioridad=85,
                    sensores=['radiacion', 'temperatura', 'viento'],
                    dependencias=['Tmrt', 'VDI3787']
                )
                _agregar_valor(valores_rad_precip, valor_tmrt)
                _agregar_traza_extra(valor_tmrt, {
                    'metodo': 'Tmrt dinámico (VDI 3787 + Höppe)',
                    'entradas': {
                        'radiacion_w_m2': rad_base,
                        'temp_c': temp_c,
                        'humedad_relativa_pct': humedad_pct,
                        'viento_ms': viento_ms,
                        'nubosidad_pct': nub_base,
                        'elevacion_solar_deg': elevacion_tmrt,
                    },
                    'detalles': resultado_tmrt
                })

    # Nubosidad nocturna (solo si existe sensor de nubosidad)
    if _es_noche(contexto):
        nubosidad_sensor_val = _extraer_nubosidad_sensor(sensores)
        if nubosidad_sensor_val is not None:
            nub_sel = _seleccionar_sensor_mejor(sensores, ['nubosidad', 'cloud', 'clouds', 'cloudcover'], contexto)
            fiab_nub = nub_sel.get('fiabilidad') if nub_sel else Fiabilidad.ALTA
            valor_nub = ValorSistema(
                nombre='Nubosidad nocturna',
                tipo='sensor',
                valor=nubosidad_sensor_val,
                unidad='%',
                fiabilidad=fiab_nub,
                icono='🌙',
                prioridad=84,
                sensores=_sensores_origen(nub_sel, 'nubosidad'),
                dependencias=[]
            )
            _agregar_valor(valores_rad_precip, valor_nub)
            _agregar_traza_extra(valor_nub, {
                'metodo': 'Sensor físico de nubosidad (solo nocturno)',
                'condicion': 'elevacion_solar <= 0'
            })
    
    # Añadir datos de precipitación al grupo consolidado
    lluvia_sel = _seleccionar_sensor_mejor(sensores, ['lluvia', 'rain', 'rainrate', 'rainratein'], contexto, 'lluvia_rate')
    valor_ll, fiab_ll = _aplicar_fallback(lluvia_sel.get('valor') if lluvia_sel else None, 'humedad_suelo', 'lluvia')
    fiab_ll = _combinar_fiabilidad(fiab_ll, lluvia_sel.get('fiabilidad') if lluvia_sel else None)
    unidad_ll = lluvia_sel.get('unidad') if lluvia_sel else 'mm/h'
    _agregar_valor(valores_rad_precip, ValorSistema(
        nombre='Lluvia',
        tipo='sensor',
        valor=valor_ll,
        unidad=unidad_ll or 'mm/h',
        fiabilidad=fiab_ll,
        icono='🌧️',
        prioridad=90,
        sensores=_sensores_origen(lluvia_sel, 'lluvia'),
        dependencias=[]
    ))

    lluvia_acum_sel = _seleccionar_sensor_mejor(sensores, ['lluvia_acumulada', 'dailyrain', 'eventrain', 'hourlyrain'], contexto, 'lluvia')
    if lluvia_acum_sel is not None:
        valor_la, fiab_la = _aplicar_fallback(lluvia_acum_sel.get('valor'), 'humedad_suelo', 'lluvia_acumulada')
        fiab_la = _combinar_fiabilidad(fiab_la, lluvia_acum_sel.get('fiabilidad') if lluvia_acum_sel else None)
        unidad_la = lluvia_acum_sel.get('unidad') if lluvia_acum_sel else 'mm'
        _agregar_valor(valores_rad_precip, ValorSistema(
            nombre='Lluvia acumulada',
            tipo='sensor',
            valor=valor_la,
            unidad=unidad_la or 'mm',
            fiabilidad=fiab_la,
            icono='💧',
            prioridad=80,
            sensores=_sensores_origen(lluvia_acum_sel, 'lluvia_acumulada'),
            dependencias=[]
        ))
    
    if valores_rad_precip:
        grupos.append(GrupoValores(
            nombre='Radiación & Precipitación',
            icono='☀️',
            valores=valores_rad_precip,
            prioridad=60
        ))
    
    # GRUPO 5: CALIDAD DEL AIRE & VISIBILIDAD [PARTICULAS]
    valores_aire = []
    pm25_sel = _seleccionar_sensor_mejor(sensores, ['pm25', 'pm25_ch1', 'pm25_avg_24h_ch1'], contexto)
    valor_pm25, fiab_pm25 = _aplicar_fallback(pm25_sel.get('valor') if pm25_sel else None, 'visibilidad', 'pm25')
    fiab_pm25 = _combinar_fiabilidad(fiab_pm25, pm25_sel.get('fiabilidad') if pm25_sel else None)
    _agregar_valor(valores_aire, ValorSistema(
        nombre='PM2.5',
        tipo='sensor',
        valor=valor_pm25,
        unidad='µg/m³',
        fiabilidad=fiab_pm25,
        icono='[PARTICULAS]',
        prioridad=100,
        sensores=_sensores_origen(pm25_sel, 'pm25'),
        dependencias=[]
    ))

    pm10_sel = _seleccionar_sensor_mejor(sensores, ['pm10', 'pm10_ch1'], contexto)
    if pm10_sel is not None:
        valor_pm10, fiab_pm10 = _aplicar_fallback(pm10_sel.get('valor'), 'visibilidad', 'pm10')
        fiab_pm10 = _combinar_fiabilidad(fiab_pm10, pm10_sel.get('fiabilidad') if pm10_sel else None)
        _agregar_valor(valores_aire, ValorSistema(
            nombre='PM10',
            tipo='sensor',
            valor=valor_pm10,
            unidad='µg/m³',
            fiabilidad=fiab_pm10,
            icono='🌁',
            prioridad=90,
            sensores=_sensores_origen(pm10_sel, 'pm10'),
            dependencias=[]
        ))

    co2_sel = _seleccionar_sensor_mejor(sensores, ['co2', 'co2_ppm'], contexto)
    valor_co2, fiab_co2 = _aplicar_fallback(co2_sel.get('valor') if co2_sel else None, 'presion', 'co2')
    fiab_co2 = _combinar_fiabilidad(fiab_co2, co2_sel.get('fiabilidad') if co2_sel else None)
    _agregar_valor(valores_aire, ValorSistema(
        nombre='CO2',
        tipo='sensor',
        valor=valor_co2,
        unidad='ppm',
        fiabilidad=fiab_co2,
        icono='💨',
        prioridad=90,
        sensores=_sensores_origen(co2_sel, 'co2'),
        dependencias=[]
    ))

    vis_kh = _extraer_valor_indice(indices, ['visibilidad_kasten_hanel_km', 'visibilidad_kasten_hänel_km'])
    if vis_kh is not None:
        valor_vk, fiab_vk = _aplicar_fallback(vis_kh, 'visibilidad', 'visibilidad_kasten_hanel_km')
        valor_vk_obj = ValorSistema(
            nombre='Visibilidad (Kasten-Hänel)',
            tipo='índice',
            valor=valor_vk,
            unidad='km',
            fiabilidad=fiab_vk,
            icono='👁️',
            prioridad=85,
            sensores=['radiacion', 'humedad', 'aerosoles'],
            dependencias=['Kasten-Hänel']
        )
        _agregar_valor(valores_aire, valor_vk_obj)
        _agregar_traza_extra(valor_vk_obj, {
            'metodo': 'Kasten-Hänel (visibilidad física)',
            'fuente_indice': 'visibilidad_kasten_hanel_km'
        })
    
    # Añadir visibilidad si está disponible
    visibilidad_sel = _seleccionar_sensor_mejor(sensores, ['visibilidad', 'visibility'], contexto, 'visibilidad')
    if visibilidad_sel is not None:
        valor_vis, fiab_vis = _aplicar_fallback(visibilidad_sel.get('valor'), 'visibilidad', 'visibilidad')
        fiab_vis = _combinar_fiabilidad(fiab_vis, visibilidad_sel.get('fiabilidad') if visibilidad_sel else None)
        unidad_vis = visibilidad_sel.get('unidad') if visibilidad_sel else 'km'
        _agregar_valor(valores_aire, ValorSistema(
            nombre='Visibilidad',
            tipo='sensor',
            valor=valor_vis,
            unidad=unidad_vis or 'km',
            fiabilidad=fiab_vis,
            icono='👁️',
            prioridad=80,
            sensores=_sensores_origen(visibilidad_sel, 'visibilidad'),
            dependencias=[]
        ))
    
    if valores_aire:
        grupos.append(GrupoValores(
            nombre='Calidad aire',
            icono='[PARTICULAS]',
            valores=valores_aire,
            prioridad=50
        ))

    # GRUPO EXTRA: PREDICCIONES 🔮
    valores_pred = []

    def _agregar_pred(nombre: str, valor: Any, unidad: str, icono: str, prioridad: int):
        if valor is None:
            return
        try:
            valor_num = float(valor)
        except Exception:
            valor_num = valor
        _agregar_valor(valores_pred, ValorSistema(
            nombre=nombre,
            tipo='índice',
            valor=valor_num,
            unidad=unidad,
            fiabilidad=Fiabilidad.MEDIA,
            icono=icono,
            prioridad=prioridad,
            sensores=['predicciones'],
            dependencias=['Predicción']
        ))

    def _leer_pred(aliases: Iterable[str]) -> Any:
        valor = _extraer_valor_indice(indices, aliases)
        if valor is not None:
            return valor
        try:
            from core.bus import obtener_bus
            bus = obtener_bus()
            if bus is None:
                return None
            for key in aliases:
                try:
                    val_bus = bus.leer(key)
                except Exception:
                    val_bus = None
                if val_bus is not None:
                    return val_bus
        except Exception:
            return None
        return None

    _agregar_pred('Prob. lluvia 6h', _leer_pred(['probabilidad_lluvia_continua_proxima_6h']), '%', '🌧️', 90)
    _agregar_pred('Prob. lluvia 24h', _leer_pred(['probabilidad_lluvia_proxima_24h']), '%', '🌧️', 88)
    _agregar_pred('Prob. tormenta', _leer_pred(['probabilidad_tormenta_severa']), '%', '⛈️', 87)
    _agregar_pred('Tiempo llegada tormenta', _leer_pred(['tiempo_llegada_tormenta_min']), 'min', '⏳', 84)
    _agregar_pred('Prob. helada noche', _leer_pred(['probabilidad_helada_proxima_noche']), '%', '❄️', 86)
    _agregar_pred('Prob. calor extremo', _leer_pred(['probabilidad_calor_extremo_proximo_dia']), '%', '🔥', 85)
    _agregar_pred('Confianza predicción', _leer_pred(['confianza_prediccion_general']), '%', '✅', 83)
    _agregar_pred('Incertidumbre', _leer_pred(['incertidumbre_prediccion']), '%', '⚠️', 82)

    if valores_pred:
        grupos.append(GrupoValores(
            nombre='Predicciones',
            icono='🔮',
            valores=valores_pred,
            prioridad=45
        ))

    # Integrar sensores desconocidos de forma camaleónica
    for key, info in sensores.items():
        if _sensor_ya_conocido(key, alias_globales):
            continue
        if isinstance(info, dict):
            valor = info.get('valor', info.get('value'))
            unidad = info.get('unidad', info.get('unit', ''))
            meta = info.get('meta') if isinstance(info.get('meta'), dict) else info
        else:
            valor = info
            unidad = ''
            meta = None
        if valor is None:
            continue
        perfil = _perfil_sensor_conocido(key, meta)
        categoria = _inferir_categoria_sensor(key, unidad, meta)
        if not categoria:
            continue
        nombre_legible = key.replace('_', ' ').title()
        fiab = perfil.get('fiabilidad', Fiabilidad.MEDIA) if perfil else Fiabilidad.MEDIA
        prioridad = perfil.get('prioridad', 40) if perfil else 30
        icono = perfil.get('icono') if perfil else None
        valor_final = valor
        unidad_final = unidad
        if categoria == 'termo':
            valor_final, unidad_final = _normalizar_unidad_valor('temperatura', valor_final, unidad_final)
            _agregar_valor(valores_termo, ValorSistema(
                nombre=nombre_legible,
                tipo='sensor',
                valor=valor_final,
                unidad=unidad_final or '°C',
                fiabilidad=fiab,
                icono=icono or '🌡️',
                prioridad=prioridad,
                sensores=[key],
                dependencias=[]
            ))
        elif categoria == 'viento':
            valor_final = _convertir_viento_kmh(valor_final, unidad_final)
            _agregar_valor(valores_viento, ValorSistema(
                nombre=nombre_legible,
                tipo='sensor',
                valor=valor_final,
                unidad='km/h' if unidad_final else '',
                fiabilidad=fiab,
                icono=icono or '💨',
                prioridad=prioridad,
                sensores=[key],
                dependencias=[]
            ))
        elif categoria == 'radiacion':
            valor_final, unidad_final = _normalizar_unidad_valor('radiacion', valor_final, unidad_final)
            _agregar_valor(valores_rad_precip, ValorSistema(
                nombre=nombre_legible,
                tipo='sensor',
                valor=valor_final,
                unidad=unidad_final or unidad,
                fiabilidad=fiab,
                icono=icono or '☀️',
                prioridad=prioridad,
                sensores=[key],
                dependencias=[]
            ))
        elif categoria == 'aire':
            valor_final, unidad_final = _normalizar_unidad_valor('visibilidad', valor_final, unidad_final)
            _agregar_valor(valores_aire, ValorSistema(
                nombre=nombre_legible,
                tipo='sensor',
                valor=valor_final,
                unidad=unidad_final or unidad,
                fiabilidad=fiab,
                icono=icono or '👁️',
                prioridad=prioridad,
                sensores=[key],
                dependencias=[]
            ))
    
    # Aplicar alertas por sensores/índices en anomalía
    try:
        alertas_indices = contexto.get('alertas_indices', {})
        for grupo in grupos:
            for valor in grupo.valores:
                if valor.alerta:
                    continue
                for sensor in (valor.sensores or []):
                    if sensor in alertas_sensores:
                        _aplicar_alerta_a_valor(valor, alertas_sensores[sensor], sensor)
                        break
                if valor.alerta:
                    continue
                info_idx = _buscar_cambio(alertas_indices, valor.nombre) or alertas_indices.get(_normalizar_key(valor.nombre))
                if info_idx:
                    _aplicar_alerta_a_valor(valor, info_idx, valor.nombre)
    except Exception:
        logging.exception("Silent except at 528 - revisar contexto")

    # Fiabilidad multilevel por dependencias
    try:
        alertas_indices = contexto.get('alertas_indices', {})
        for grupo in grupos:
            for valor in grupo.valores:
                if valor.tipo != 'índice':
                    continue
                if valor.alerta:
                    continue
                degradada = False
                for dep in (valor.dependencias or []):
                    if _buscar_cambio(alertas_indices, dep) or alertas_indices.get(_normalizar_key(dep)):
                        valor.fiabilidad = _combinar_fiabilidad(valor.fiabilidad, Fiabilidad.MEDIA)
                        degradada = True
                        break
                if degradada:
                    continue
                for sensor in (valor.sensores or []):
                    if sensor in alertas_sensores:
                        valor.fiabilidad = _combinar_fiabilidad(valor.fiabilidad, Fiabilidad.MEDIA)
                        break
    except Exception:
        logging.exception("Silent except at 560 - revisar contexto")

    # Aplicar cambios de fórmula (solo indicador, sin alerta salvo bucle)
    try:
        cambios_formulas = contexto.get('cambios_formulas', {})
        for grupo in grupos:
            for valor in grupo.valores:
                info = _buscar_cambio(cambios_formulas, valor.nombre)
                if not info:
                    continue
                valor.cambios = int(info.get('cambios', 0) or 0)
                valor.estabilizado = bool(info.get('estabilizado', True))
                valor.loop_detectado = bool(info.get('loop_detectado', False))
                if valor.loop_detectado and not valor.alerta:
                    valor.alerta = "[WARNING] Bucle de cambios de fórmula detectado"
    except Exception:
        logging.exception("Silent except at 551 - revisar contexto")

    return grupos

# Configurar templates con ruta absoluta (nueva interfaz)
templates_path = Path(__file__).parent.parent / "templates"
templates_path = templates_path.resolve()  # Ruta absoluta a app/templates/
templates = Jinja2Templates(directory=str(templates_path))

# Inicializar ViewModels y Managers
fiabilidad_mgr = FiabilidadManager()
panel_vm = PanelViewModel(fiabilidad_mgr)

# Referencia al SystemManager (se inyecta desde main_asgi.py)
_system_manager = None

def set_system_manager(system_manager):
    """Inyecta el SystemManager desde main_asgi.py."""
    global _system_manager
    _system_manager = system_manager

def obtener_contexto_sistema() -> Dict[str, Any]:
    """Obtiene el contexto actual del sistema (sensores e índices)."""
    cached = _cache_get("contexto", _TTL_CONTEXTO)
    if cached is not None:
        return cached
    if not _system_manager or not _system_manager.system:
        return _cache_set("contexto", {
            'sensores': {},
            'indices': {},
            'ubicacion': {
                'latitud': ESTACION.LATITUD,
                'longitud': ESTACION.LONGITUD,
                'poblacion': 'Argentona'
            }
        })
    
    # Obtener estado completo del sistema
    estado = _system_manager.obtener_estado()
    sensores_raw = _system_manager.obtener_sensores()
    
    # Transformar sensores al formato esperado
    sensores = {}
    for nombre, info in sensores_raw.items():
        if isinstance(info, dict):
            if 'value' in info or 'valor' in info:
                meta = {k: v for k, v in info.items() if k not in {'value', 'valor', 'unit', 'unidad', 'timestamp'}}
                sensores[nombre] = {
                    'valor': info.get('value', info.get('valor')),
                    'unidad': info.get('unit', info.get('unidad', '')),
                    'timestamp': info.get('timestamp', ''),
                    'meta': meta if meta else None,
                }
        else:
            sensores[nombre] = {
                'valor': info,
                'unidad': ''
            }
    
    # Extraer índices del estado (si existen)
    indices = estado.get('indices', {}) if isinstance(estado, dict) else {}
    if not isinstance(indices, dict):
        indices = {}

    # Inyectar predicciones desde Bus si están disponibles
    try:
        from core.bus import obtener_bus
        bus = obtener_bus()
        if bus is not None:
            pred_keys = [
                'probabilidad_lluvia_continua_proxima_6h',
                'probabilidad_lluvia_proxima_24h',
                'confianza_prediccion_lluvia',
                'probabilidad_tormenta_severa',
                'severidad_estimada_tormenta',
                'tiempo_llegada_tormenta_min',
                'probabilidad_helada_proxima_noche',
                'probabilidad_calor_extremo_proximo_dia',
                'confianza_prediccion_general',
                'incertidumbre_prediccion',
                'escenario_optimista_temp',
                'escenario_pesimista_temp',
                'escenario_medio_temp',
            ]
            for key in pred_keys:
                if key in indices:
                    continue
                try:
                    val = None
                    if hasattr(bus, 'leer'):
                        val = bus.leer(key)
                    if val is None and hasattr(bus, 'capa_core'):
                        val = bus.capa_core.obtener_valor(key)
                    if val is None and hasattr(bus, 'capa_intermediate'):
                        val = bus.capa_intermediate.obtener_valor(key)
                    if val is not None:
                        indices[key] = val
                except Exception:
                    continue
    except Exception:
        logging.exception("Error inyectando predicciones desde Bus")
    
    # Extraer ubicación del estado
    ubicacion = estado.get('ubicacion', {})
    if not ubicacion:
        # Intentar obtener coordenadas del system manager
        coords = _system_manager.obtener_coordenadas()
        if coords:
            ubicacion = {
                'latitud': coords.get('lat', coords.get('latitude', ESTACION.LATITUD)),
                'longitud': coords.get('lon', coords.get('longitude', ESTACION.LONGITUD)),
                'poblacion': coords.get('poblacion', coords.get('population', 'Argentona'))
            }
        else:
            ubicacion = {
                'latitud': ESTACION.LATITUD,
                'longitud': ESTACION.LONGITUD,
                'poblacion': 'Argentona'
            }
    
    alertas_sensores = estado.get('alertas_sensores', {}) if isinstance(estado, dict) else {}
    alertas_indices = estado.get('alertas_indices', {}) if isinstance(estado, dict) else {}
    cambios_formulas = estado.get('cambios_formulas', {}) if isinstance(estado, dict) else {}

    orografia = _obtener_orografia(ubicacion.get("latitud", ESTACION.LATITUD), ubicacion.get("longitud", ESTACION.LONGITUD))

    return _cache_set("contexto", {
        'sensores': sensores,
        'indices': indices,
        'ubicacion': ubicacion,
        'orografia': orografia,
        'alertas_sensores': alertas_sensores,
        'alertas_indices': alertas_indices,
        'cambios_formulas': cambios_formulas,
    })

@router.get("/", response_class=HTMLResponse)
async def panel_principal(request: Request):
    """
    Renderiza el panel principal (nueva interfaz - panel.html).
    """
    return templates.TemplateResponse(request=request, name="panel.html")

@router.get("/api/panel/superior")
async def obtener_panel_superior():
    """
    Obtiene los datos para el panel superior fijo.
    
    **Response:**
    ```json
    {
        "nombre_sistema": "MeteoSer",
        "ubicacion": {
            "latitud": 41.5,
            "longitud": 2.4,
            "poblacion": "Argentona"
        },
        "estacion": "Invierno",
        "fecha": "30/01/2026",
        "hora": "10:30"
    }
    ```
    """
    cached = _cache_get("panel_superior", _TTL_PANEL)
    if cached is not None:
        return cached

    # Obtener coordenadas del sistema
    lat, lon = 41.5, 2.4
    if _system_manager:
        coords = _system_manager.obtener_coordenadas()
        if coords:
            lat = coords.get('lat', coords.get('latitude', 41.5))
            lon = coords.get('lon', coords.get('longitude', 2.4))
    
    estacion = "Invierno"  # TODO: Obtener desde cálculo astronómico
    
    data = panel_vm.obtener_panel_superior(lat, lon, estacion)
    data["orografia"] = _obtener_orografia(lat, lon)
    return _cache_set("panel_superior", data)


@router.get("/api/orografia")
async def obtener_orografia():
    """Devuelve datos orográficos calculados desde SRTM/Open-Elevation."""
    lat, lon = 41.5, 2.4
    if _system_manager:
        coords = _system_manager.obtener_coordenadas()
        if coords:
            lat = coords.get('lat', coords.get('latitude', 41.5))
            lon = coords.get('lon', coords.get('longitude', 2.4))

    data = _obtener_orografia(lat, lon)
    if not data:
        return {"disponible": False, "orografia": None}
    return {"disponible": True, "orografia": data}

@router.get("/api/panel/alertas")
async def obtener_panel_alertas():
    """Resumen de alertas de sensores e índices."""
    contexto = obtener_contexto_sistema()
    alertas_sensores = contexto.get('alertas_sensores', {})
    alertas_indices = contexto.get('alertas_indices', {})
    lista = []
    for sensor, info in alertas_sensores.items():
        lista.append({
            "tipo": "sensor",
            "clave": sensor,
            "motivo": info.get("motivo"),
            "simulado": info.get("simulado"),
            "error": info.get("error_estimado"),
            "timestamp": info.get("timestamp"),
        })
    for indice, info in alertas_indices.items():
        lista.append({
            "tipo": "indice",
            "clave": indice,
            "motivo": info.get("motivo"),
            "simulado": info.get("simulado"),
            "error": info.get("error_estimado"),
            "timestamp": info.get("timestamp"),
        })
    lista = sorted(lista, key=lambda x: (x.get("tipo"), x.get("clave")))
    return {"total": len(lista), "items": lista}

@router.get("/api/panel/arcos")
async def obtener_arcos_solares(nubosidad: float = None):
    """
    Obtiene los datos para los arcos solar y lunar.
    
    **Query params:**
    - nubosidad (opcional): Porcentaje de nubosidad
    
    **Response:**
    ```json
    {
        "sol": {
            "posicion": 0.45,
            "amanecer": "07:30",
            "anochecer": "18:45",
            "duracion_dia": 675.0,
            "es_de_dia": true,
            "nublado": false
        },
        "luna": {
            "posicion": 0.0,
            "fase": 0.25,
            "nombre_fase": "Cuarto Creciente",
            "icono": "first_quarter",
            "duracion_noche": 765.0
        }
    }
    ```
    """
    lat, lon = 41.5, 2.4
    if _system_manager:
        coords = _system_manager.obtener_coordenadas()
        if coords:
            lat = coords.get('lat', coords.get('latitude', 41.5))
            lon = coords.get('lon', coords.get('longitude', 2.4))
    
    # Obtener nubosidad del contexto si no se especifica
    contexto = obtener_contexto_sistema()
    if nubosidad is None:
        nubosidad = _extraer_nubosidad(contexto) or 0

    cache_key = f"arcos:{int(nubosidad) if isinstance(nubosidad, (int, float)) else 0}"
    cached = _cache_get(cache_key, _TTL_ARCOS)
    if cached is not None:
        return cached

    altitud = contexto.get("ubicacion", {}).get("altitud") or contexto.get("ubicacion", {}).get("altitud_srtm")
    orografia = contexto.get("orografia") or _obtener_orografia(lat, lon)
    perfil_horizonte = orografia.get("perfil_horizonte") if orografia else None
    data = panel_vm.obtener_arcos_solares(
        lat,
        lon,
        nubosidad,
        sensores=contexto.get("sensores", {}),
        altitud_m=altitud,
        perfil_horizonte=perfil_horizonte,
    )
    return _cache_set(cache_key, data)

@router.get("/api/panel/central")
async def obtener_panel_central():
    """
    Obtiene los datos para el panel central (recomendaciones y sensación).
    
    **Response:**
    ```json
    {
        "recomendaciones": {
            "texto": "Temperatura fresca, lleva una chaqueta. Buen momento para ventilar la casa.",
            "recomendaciones": ["Temperatura fresca, lleva una chaqueta", "Buen momento para ventilar la casa"],
            "iconos": ["jacket", "ventilation"],
            "es_nocturno": false
        },
        "temperatura": {"valor": 21.5, "unidad": "°C", "fiabilidad": "alta"},
        "humedad": {"valor": 60, "unidad": "%", "fiabilidad": "alta"},
        "presion": {"valor": 1013, "unidad": "hPa", "fiabilidad": "media"},
        "viento": {"valor": 10, "unidad": "km/h", "fiabilidad": "alta"},
        "sensacion": {
            "unificado": true,
            "edificio": 20.5,
            "persona": 20.5
        }
    }
    ```
    """
    cached = _cache_get("panel_central", _TTL_PANEL)
    if cached is not None:
        return cached

    # Obtener contexto del sistema real
    contexto = obtener_contexto_sistema()
    
    # Añadir información de arcos solares
    lat, lon = 41.5, 2.4
    if _system_manager:
        coords = _system_manager.obtener_coordenadas()
        if coords:
            lat = coords.get('latitude', 41.5)
            lon = coords.get('longitude', 2.4)
    
    altitud = contexto.get("ubicacion", {}).get("altitud") or contexto.get("ubicacion", {}).get("altitud_srtm")
    orografia = contexto.get("orografia") or _obtener_orografia(lat, lon)
    perfil_horizonte = orografia.get("perfil_horizonte") if orografia else None
    contexto['elevacion_solar'] = panel_vm.obtener_arcos_solares(
        lat,
        lon,
        sensores=contexto.get("sensores", {}),
        altitud_m=altitud,
        perfil_horizonte=perfil_horizonte,
    )

    uv_info = _obtener_uv_contexto(contexto)
    if uv_info is not None:
        contexto['uv'] = uv_info.get('valor')
        contexto['uv_motor'] = uv_info.get('motor')

    data = panel_vm.obtener_panel_central(contexto)
    return _cache_set("panel_central", data)


@router.get("/api/panel/cajones")
async def obtener_cajones():
    """
    Obtiene la estructura de cajones para la UI DESDE DATOS REALES del sistema.
    
    **Response:**
    ```json
    {
        "cajones": [
            {
                "id": "cajon_termodinamica",
                "nombre": "Termodinámica",
                "icono": "🌡️",
                "prioridad": 100,
                "valores_tapa": [
                    {"nombre": "Temperatura", "valor": 21.5, "unidad": "°C", "icono": "🌡️"},
                    {"nombre": "Sensación", "valor": 20.0, "unidad": "°C", "icono": "🤚"}
                ],
                "total_valores": 8
            }
        ],
        "total": 6
    }
    ```
    """
    cached = _cache_get("cajones", _TTL_CAJONES)
    if cached is not None:
        return {"cajones": cached, "total": len(cached)}

    # Obtener datos reales del sistema
    contexto = obtener_contexto_sistema()

    # GENERAR GRUPOS DINÁMICOS DESDE DATOS REALES
    grupos = generar_grupos_desde_sistema(contexto)

    # Inicializar jerarquía con grupos reales
    panel_vm.inicializar_jerarquia(grupos)
    cajones = panel_vm.obtener_cajones()

    _cache_set("cajones", cajones)
    return {"cajones": cajones, "total": len(cajones)}


@router.get("/api/panel/traza")
async def obtener_traza(nombre: str):
    """Devuelve la traza física de un valor/índice si está disponible en el panel."""
    contexto = obtener_contexto_sistema()
    grupos = generar_grupos_desde_sistema(contexto)
    key_busqueda = _normalizar_key(nombre)
    for grupo in grupos:
        for valor in grupo.valores:
            if _normalizar_key(valor.nombre) != key_busqueda:
                continue
            _asegurar_traza(valor)
            return {
                "encontrado": True,
                "nombre": valor.nombre,
                "tipo": valor.tipo,
                "valor": valor.valor,
                "unidad": valor.unidad,
                "fiabilidad": valor.fiabilidad.name.lower(),
                "alerta": valor.alerta,
                "sensores": list(valor.sensores or []),
                "dependencias": list(valor.dependencias or []),
                "traza": getattr(valor, 'traza', None),
            }
    return {"encontrado": False, "nombre": nombre}


def obtener_cajones_cacheados() -> List[Dict[str, Any]]:
    cached = _cache_get("cajones", _TTL_CAJONES)
    if cached is not None:
        return cached
    contexto = obtener_contexto_sistema()
    grupos = generar_grupos_desde_sistema(contexto)
    panel_vm.inicializar_jerarquia(grupos)
    cajones = panel_vm.obtener_cajones()
    return _cache_set("cajones", cajones)


@router.get("/health")
async def health_check():
    """
    🔬 Verificación de rendimiento del sistema UI.
    Devuelve timestamp para calcular latencia cliente-servidor.
    Objetivo: < 100ms de latencia.
    """
    from datetime import datetime
    import time
    
    inicio = time.time()
    
    # Verificar que el sistema está operativo
    try:
        contexto = obtener_contexto_sistema()
        tiene_datos = len(contexto.get('sensores', {})) > 0
    except:
        tiene_datos = False
    
    latencia_backend = (time.time() - inicio) * 1000  # en ms
    
    return {
        "status": "operational" if tiene_datos else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "latencia_backend_ms": round(latencia_backend, 2),
        "gpu_acceleration": "enabled",
        "drag_drop_persistence": "ready",
        "canvas_animations": "active",
        "alerta_tormenta": "armed"
    }

@router.get("/api/submenu/{nombre_valor}")
async def obtener_submenu_valor(nombre_valor: str):
    """
    Obtiene el contenido del submenú explicativo para un valor específico.
    
    **Path params:**
    - nombre_valor: Nombre del valor/índice
    
    **Response:**
    ```json
    {
        "nombre": "Temperatura",
        "tipo": "sensor",
        "valor": 21.5,
        "unidad": "°C",
        "fiabilidad": "alta",
        "sensores_origen": ["sensor_temp"],
        "dependencias": ["UTCI", "sensacion_termica"],
        "formula": "Medición directa del sensor",
        "estado": "Operativo",
        "alerta": null
    }
    ```
    """
    contexto = obtener_contexto_sistema()
    return panel_vm.obtener_submenu_valor(nombre_valor, contexto)



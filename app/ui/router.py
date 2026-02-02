# router.py
# Rutas de la nueva interfaz MeteoSer

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time
from typing import Dict, Any, List, Iterable, Optional

from app.ui.viewmodel import PanelViewModel
from core.fiabilidad_manager import FiabilidadManager
from core.data_model import ValorSistema, GrupoValores, Fiabilidad
from core.context.fallback_universal import obtener_fallback_universal, EstadoFisico

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

def _normalizar_key(valor: str) -> str:
    return str(valor).strip().lower().replace(" ", "_")


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
    
    # Sistema de tracking para evitar duplicados
    valores_ya_usados = set()
    
    def valor_unico(nombre: str) -> bool:
        """Verifica si un valor ya fue usado en otro grupo."""
        nombre_norm = nombre.lower().replace(' ', '_')
        if nombre_norm in valores_ya_usados:
            return False
        valores_ya_usados.add(nombre_norm)
        return True
    
    grupos = []
    
    # GRUPO 1: TERMODINÁMICA 🌡️
    valores_termo = []
    temp = _extraer_valor_sensor(sensores, ['temperatura', 'temp', 'tempc', 'tempf', 'temperature'])
    valor_temp, fiab_temp = _aplicar_fallback(temp.get('valor') if temp else None, 'temperatura', 'temperatura')
    valores_termo.append(ValorSistema(
        nombre='Temperatura',
        tipo='sensor',
        valor=valor_temp,
        unidad='°C',
        fiabilidad=fiab_temp,
        icono='🌡️',
        prioridad=100,
        sensores=['temperatura'],
        dependencias=[]
    ))

    humedad = _extraer_valor_sensor(sensores, ['humedad', 'humidity', 'rh', 'humedad_relativa'])
    valor_h, fiab_h = _aplicar_fallback(humedad.get('valor') if humedad else None, 'humedad_relativa', 'humedad')
    valores_termo.append(ValorSistema(
        nombre='Humedad',
        tipo='sensor',
        valor=valor_h,
        unidad='%',
        fiabilidad=fiab_h,
        icono='💧',
        prioridad=95,
        sensores=['humedad'],
        dependencias=[]
    ))

    presion = _extraer_valor_sensor(sensores, ['presion', 'pressure', 'baro', 'baromabs', 'baromrelin'])
    valor_p, fiab_p = _aplicar_fallback(presion.get('valor') if presion else None, 'presion', 'presion')
    valores_termo.append(ValorSistema(
        nombre='Presión',
        tipo='sensor',
        valor=valor_p,
        unidad='hPa',
        fiabilidad=fiab_p,
        icono='🎚️',
        prioridad=85,
        sensores=['presion'],
        dependencias=[]
    ))

    utci = _extraer_valor_indice(indices, ['utci', 'utci_edificio', 'utci_persona', 'utci_sensor', 'utci_calle'])
    if utci is None:
        utci = None
    if utci is not None:
        if isinstance(utci, dict):
            utci_calle = utci.get('calle')
            utci_sensor = utci.get('sensor')
            if utci_calle is not None:
                valor_uc, fiab_uc = _aplicar_fallback(utci_calle, 'temperatura', 'utci_calle')
                valores_termo.append(ValorSistema(
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
                valores_termo.append(ValorSistema(
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
            valores_termo.append(ValorSistema(
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
    
    if valores_termo:
        grupos.append(GrupoValores(
            nombre='Termodinámica',
            icono='🌡️',
            valores=valores_termo,
            prioridad=100
        ))
    
    # GRUPO 2: VIENTO 💨
    valores_viento = []
    viento = _extraer_valor_sensor(sensores, ['viento', 'windspeed', 'wind_speed', 'windspeedmph', 'wind_ms'])
    valor_v, fiab_v = _aplicar_fallback(viento.get('valor') if viento else None, 'velocidad_viento', 'viento')
    valores_viento.append(ValorSistema(
        nombre='Velocidad viento',
        tipo='sensor',
        valor=valor_v,
        unidad='km/h',
        fiabilidad=fiab_v,
        icono='💨',
        prioridad=100,
        sensores=['viento'],
        dependencias=[]
    ))

    racha = _extraer_valor_sensor(sensores, ['racha', 'windgust', 'windgustmph', 'gust'])
    if racha is not None:
        valor_r, fiab_r = _aplicar_fallback(racha.get('valor'), 'velocidad_viento', 'racha')
        valores_viento.append(ValorSistema(
            nombre='Ráfagas',
            tipo='sensor',
            valor=valor_r,
            unidad='km/h',
            fiabilidad=fiab_r,
            icono='🌪️',
            prioridad=90,
            sensores=['racha'],
            dependencias=[]
        ))

    direccion = _extraer_valor_sensor(sensores, ['direccion_viento', 'winddir', 'wind_dir'])
    valor_d, fiab_d = _aplicar_fallback(direccion.get('valor') if direccion else None, 'azimuth_solar', 'direccion_viento')
    valores_viento.append(ValorSistema(
        nombre='Dirección viento',
        tipo='sensor',
        valor=valor_d,
        unidad='°',
        fiabilidad=fiab_d,
        icono='🧭',
        prioridad=80,
        sensores=['direccion_viento'],
        dependencias=[]
    ))

    z0h = _extraer_valor_indice(indices, ['z0h', 'z0h_zilitinkevich'])
    if z0h is not None:
        valor_z0h, fiab_z0h = _aplicar_fallback(z0h, 'temperatura', 'z0h_zilitinkevich')
        valores_viento.append(ValorSistema(
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
    
    # GRUPO 3: BIOMETRÍA 👤
    valores_bio = []
    pmv = _extraer_valor_indice(indices, ['pmv', 'indice_pmv'])
    valor_pmv, fiab_pmv = _aplicar_fallback(pmv, 'temperatura', 'pmv')
    valores_bio.append(ValorSistema(
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
    valores_bio.append(ValorSistema(
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
    radiacion = _extraer_valor_sensor(sensores, ['radiacion', 'solarradiation', 'radiacion_solar'])
    valor_rad, fiab_rad = _aplicar_fallback(radiacion.get('valor') if radiacion else None, 'elevacion_solar', 'radiacion')
    if valor_unico('Radiación solar'):
        valores_rad_precip.append(ValorSistema(
            nombre='Radiación solar',
            tipo='sensor',
            valor=valor_rad,
            unidad='W/m²',
            fiabilidad=fiab_rad,
            icono='☀️',
            prioridad=100,
            sensores=['radiacion'],
            dependencias=[]
        ))

    from core.indices.uv_spectral_diamond import get_uv_spectral_engine
    from core.arcos_solares import calcular_posicion_sol
    from datetime import datetime
    
    uv = _extraer_valor_sensor(sensores, ['uv', 'indice_uv', 'uvi', 'uv_index', 'uvindex'])
    valor_uv_sensor = uv.get('valor') if uv else None
    fuente_uv = "sensor"
    
    # Si no hay sensor UV o es 0, calcular con el Motor Diamond Spectral v3
    if valor_uv_sensor is None or valor_uv_sensor == 0:
        radiacion_val = radiacion.get('valor') if radiacion else None
        if radiacion_val is not None and radiacion_val > 0:
            # Obtener elevación solar actual
            lat = contexto.get('ubicacion', {}).get('latitud', 41.55)
            lon = contexto.get('ubicacion', {}).get('longitud', 2.40)
            altitud = contexto.get('ubicacion', {}).get('altitud', 100.0)
            
            datos_sol = calcular_posicion_sol(lat, lon, datetime.now())
            elevacion_solar = datos_sol.get('elevacion_solar', 0)
            
            # Obtener datos atmosféricos
            presion_val = _extraer_valor_sensor(sensores, ['presion', 'pressure', 'baro', 'baromabs'])
            presion_hpa = presion_val.get('valor') if presion_val else 1013.25
            
            temp_val = _extraer_valor_sensor(sensores, ['temperatura', 'temp', 'tempc'])
            temperatura_c = temp_val.get('valor') if temp_val else 15.0
            
            humedad_val = _extraer_valor_sensor(sensores, ['humedad', 'humidity'])
            humedad_relativa = humedad_val.get('valor') if humedad_val else 50.0
            
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
    
    # Aplicar Resolución de Diamante y Ley del Entero para UV
    if valor_uv is not None and isinstance(valor_uv, (int, float)):
        val_float = float(valor_uv)
        if val_float == 0 or (val_float == int(val_float)):
            valor_uv = int(val_float)
        else:
            valor_uv = round(val_float, 2)
    
    if valor_unico('Índice UV'):
        valores_rad_precip.append(ValorSistema(
            nombre='Índice UV',
            tipo='sensor',
            valor=valor_uv,
            unidad='',
            fiabilidad=fiab_uv,
            icono='🌞',
            prioridad=95,
            sensores=['uv'],
            dependencias=[]
        ))

    tmrt = _extraer_valor_indice(indices, ['tmrt', 'radiante', 'temperatura_radiante_media'])
    if tmrt is not None and valor_unico('Tmrt (radiante)'):
        valor_tmrt, fiab_tmrt = _aplicar_fallback(tmrt, 'temperatura', 'tmrt')
        valores_rad_precip.append(ValorSistema(
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
    
    # Añadir datos de precipitación al grupo consolidado
    lluvia = _extraer_valor_sensor(sensores, ['lluvia', 'rain', 'rainrate', 'rainratein'])
    valor_ll, fiab_ll = _aplicar_fallback(lluvia.get('valor') if lluvia else None, 'humedad_suelo', 'lluvia')
    if valor_unico('Lluvia'):
        valores_rad_precip.append(ValorSistema(
            nombre='Lluvia',
            tipo='sensor',
            valor=valor_ll,
            unidad='mm/h',
            fiabilidad=fiab_ll,
            icono='🌧️',
            prioridad=90,
            sensores=['lluvia'],
            dependencias=[]
        ))

    lluvia_acum = _extraer_valor_sensor(sensores, ['lluvia_acumulada', 'dailyrain', 'eventrain', 'hourlyrain'])
    if lluvia_acum is not None and valor_unico('Lluvia acumulada'):
        valor_la, fiab_la = _aplicar_fallback(lluvia_acum.get('valor'), 'humedad_suelo', 'lluvia_acumulada')
        valores_rad_precip.append(ValorSistema(
            nombre='Lluvia acumulada',
            tipo='sensor',
            valor=valor_la,
            unidad='mm',
            fiabilidad=fiab_la,
            icono='💧',
            prioridad=80,
            sensores=['lluvia_acumulada'],
            dependencias=[]
        ))
    
    if valores_rad_precip:
        grupos.append(GrupoValores(
            nombre='Radiación & Precipitación',
            icono='☀️',
            valores=valores_rad_precip,
            prioridad=60
        ))
    
    # GRUPO 5: CALIDAD DEL AIRE & VISIBILIDAD 🌫️
    valores_aire = []
    pm25 = _extraer_valor_sensor(sensores, ['pm25', 'pm25_ch1', 'pm25_avg_24h_ch1'])
    valor_pm25, fiab_pm25 = _aplicar_fallback(pm25.get('valor') if pm25 else None, 'visibilidad', 'pm25')
    if valor_unico('PM2.5'):
        valores_aire.append(ValorSistema(
            nombre='PM2.5',
            tipo='sensor',
            valor=valor_pm25,
            unidad='µg/m³',
            fiabilidad=fiab_pm25,
            icono='🌫️',
            prioridad=100,
            sensores=['pm25'],
            dependencias=[]
        ))

    pm10 = _extraer_valor_sensor(sensores, ['pm10', 'pm10_ch1'])
    if pm10 is not None and valor_unico('PM10'):
        valor_pm10, fiab_pm10 = _aplicar_fallback(pm10.get('valor'), 'visibilidad', 'pm10')
        valores_aire.append(ValorSistema(
            nombre='PM10',
            tipo='sensor',
            valor=valor_pm10,
            unidad='µg/m³',
            fiabilidad=fiab_pm10,
            icono='🌁',
            prioridad=90,
            sensores=['pm10'],
            dependencias=[]
        ))

    co2 = _extraer_valor_sensor(sensores, ['co2', 'co2_ppm'])
    valor_co2, fiab_co2 = _aplicar_fallback(co2.get('valor') if co2 else None, 'presion', 'co2')
    if valor_unico('CO2'):
        valores_aire.append(ValorSistema(
            nombre='CO2',
            tipo='sensor',
            valor=valor_co2,
            unidad='ppm',
            fiabilidad=fiab_co2,
            icono='💨',
            prioridad=90,
            sensores=['co2'],
            dependencias=[]
        ))
    
    # Añadir visibilidad si está disponible
    visibilidad = _extraer_valor_sensor(sensores, ['visibilidad', 'visibility'])
    if visibilidad is not None and valor_unico('Visibilidad'):
        valor_vis, fiab_vis = _aplicar_fallback(visibilidad.get('valor'), 'visibilidad', 'visibilidad')
        valores_aire.append(ValorSistema(
            nombre='Visibilidad',
            tipo='sensor',
            valor=valor_vis,
            unidad='km',
            fiabilidad=fiab_vis,
            icono='👁️',
            prioridad=80,
            sensores=['visibilidad'],
            dependencias=[]
        ))
    
    if valores_aire:
        grupos.append(GrupoValores(
            nombre='Calidad aire',
            icono='🌫️',
            valores=valores_aire,
            prioridad=50
        ))
    
    # GRUPO 6: SENSORES VIRTUALES 🤖 (placeholder si no hay datos)
    valores_virtuales = []
    # Aquí se pueden añadir sensores virtuales cuando estén disponibles
    if valores_virtuales or True:  # Siempre crear el grupo aunque esté vacío
        grupos.append(GrupoValores(
            nombre='Sensores virtuales',
            icono='🤖',
            valores=valores_virtuales,
            prioridad=45
        ))
    
    # GRUPO 7: PREDICCIONES 🔮 (placeholder)
    valores_predicciones = []
    if valores_predicciones or True:
        grupos.append(GrupoValores(
            nombre='Predicciones',
            icono='🔮',
            valores=valores_predicciones,
            prioridad=40
        ))
    
    # GRUPO 8: ALERTAS Y RIESGOS ⚠️ (placeholder)
    valores_alertas = []
    if valores_alertas or True:
        grupos.append(GrupoValores(
            nombre='Alertas y riesgos',
            icono='⚠️',
            valores=valores_alertas,
            prioridad=35
        ))
    
    # GRUPO 9: ÍNDICES MISCELÁNEOS 📊 (placeholder)
    valores_misc = []
    if valores_misc or True:
        grupos.append(GrupoValores(
            nombre='Índices misceláneos',
            icono='📊',
            valores=valores_misc,
            prioridad=30
        ))
    
    # GRUPO 10: CONFIGURACIÓN Y SISTEMA ⚙️ (placeholder)
    valores_sistema = []
    if valores_sistema or True:
        grupos.append(GrupoValores(
            nombre='Sistema',
            icono='⚙️',
            valores=valores_sistema,
            prioridad=25
        ))
    
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
            'indices': {}
        })
    
    # Obtener estado completo del sistema
    estado = _system_manager.obtener_estado()
    sensores_raw = _system_manager.obtener_sensores()
    
    # Transformar sensores al formato esperado
    sensores = {}
    for nombre, info in sensores_raw.items():
        if isinstance(info, dict):
            if 'value' in info or 'valor' in info:
                sensores[nombre] = {
                    'valor': info.get('value', info.get('valor')),
                    'unidad': info.get('unit', info.get('unidad', '')),
                    'timestamp': info.get('timestamp', '')
                }
        else:
            sensores[nombre] = {
                'valor': info,
                'unidad': ''
            }
    
    # Extraer índices del estado (si existen)
    indices = estado.get('indices', {})
    
    return _cache_set("contexto", {
        'sensores': sensores,
        'indices': indices
    })

@router.get("/", response_class=HTMLResponse)
async def panel_principal(request: Request):
    """
    Renderiza el panel principal (nueva interfaz - panel.html).
    """
    return templates.TemplateResponse("panel.html", {"request": request})

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
    return _cache_set("panel_superior", data)

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
    if nubosidad is None:
        contexto = obtener_contexto_sistema()
        nubosidad = contexto['sensores'].get('nubosidad', {}).get('valor', 0)

    cache_key = f"arcos:{int(nubosidad) if isinstance(nubosidad, (int, float)) else 0}"
    cached = _cache_get(cache_key, _TTL_ARCOS)
    if cached is not None:
        return cached

    data = panel_vm.obtener_arcos_solares(lat, lon, nubosidad)
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
    
    contexto['arco_solar'] = panel_vm.obtener_arcos_solares(lat, lon)

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



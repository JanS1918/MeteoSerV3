# GUÍA DE INTEGRACIÓN GFS/NOAA
==================================

## ESTADO ACTUAL: FASE 3 (NO IMPLEMENTADO)

### ¿Qué es GFS?
Global Forecast System - Modelo numérico de predicción meteorológica de NOAA.
- Actualización: cada 6 horas
- Resolución: 0.25° (~25km)
- Horizonte: hasta 384 horas (16 días)

### ¿Por qué NO está implementado?
1. **Requiere credenciales NOAA** (registro en api.weather.gov)
2. **Latencia alta** (10-30 segundos por consulta)
3. **Cuota limitada** (1000 requests/día en plan free)
4. **Complejidad parsing** (datos en GRIB2, requiere xarray/cfgrib)
5. **NO CRÍTICO** para uso personal (MeteoSerV3 ya tiene predicción local)

### ¿Cuándo implementar?
- **SI** necesitas predicción a 7+ días (solo GFS puede)
- **SI** tienes cuenta NOAA aprobada
- **SI** puedes tolerar latencia 10-30s
- **NO** si solo necesitas precisión local (usa LSTM local)

---

## IMPLEMENTACIÓN (Cuando sea necesario)

### PASO 1: Obtener credenciales NOAA

```bash
# 1. Registrarse en https://www.weather.gov/developers
# 2. Solicitar API key
# 3. Guardar en archivo .env
echo "NOAA_API_KEY=tu_clave_aqui" >> .env
echo "NOAA_USER_AGENT=MeteoSerV3/1.0 (contacto@example.com)" >> .env
```

### PASO 2: Instalar dependencias

```bash
# Instalación completa para GFS
pip install xarray cfgrib requests python-dotenv

# Verificar instalación
python -c "import xarray, cfgrib; print('OK')"
```

### PASO 3: Crear módulo de integración

```python
# core/apis/gfs_integration.py
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GFSIntegration:
    """Integración con GFS/NOAA"""
    
    BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
    
    def __init__(self):
        self.api_key = os.getenv("NOAA_API_KEY")
        self.user_agent = os.getenv("NOAA_USER_AGENT")
        
        if not self.api_key:
            raise ValueError("NOAA_API_KEY no configurada")
    
    def fetch_forecast(self, 
                      lat: float, 
                      lon: float, 
                      hours_ahead: int = 48) -> Optional[Dict]:
        """
        Obtiene pronóstico GFS para ubicación.
        
        Args:
            lat: Latitud (41.55 para Argentona)
            lon: Longitud (2.39 para Argentona)
            hours_ahead: Horas de pronóstico (max 384)
        
        Returns:
            Dict con temperatura, presión, humedad, viento
        """
        # WARNING: Esto puede tardar 10-30 segundos
        # Usar ExecutionSandbox con timeout 30s
        
        params = {
            'file': self._get_latest_run(),
            'lev_surface': 'on',
            'var_TMP': 'on',  # Temperatura
            'var_PRES': 'on',  # Presión
            'var_RH': 'on',  # Humedad relativa
            'var_UGRD': 'on',  # Viento U
            'var_VGRD': 'on',  # Viento V
            'subregion': '',
            'leftlon': lon - 0.5,
            'rightlon': lon + 0.5,
            'toplat': lat + 0.5,
            'bottomlat': lat - 0.5,
            'dir': f'/gfs.{self._get_run_date()}'
        }
        
        headers = {
            'User-Agent': self.user_agent
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parsear GRIB2 con cfgrib
            import xarray as xr
            ds = xr.open_dataset(response.content, engine='cfgrib')
            
            # Extraer valores para Argentona
            temp_k = ds['t2m'].sel(latitude=lat, longitude=lon, method='nearest').values
            pres_pa = ds['sp'].sel(latitude=lat, longitude=lon, method='nearest').values
            rh_pct = ds['r2'].sel(latitude=lat, longitude=lon, method='nearest').values
            
            return {
                'temperatura_c': float(temp_k - 273.15),
                'presion_hpa': float(pres_pa / 100),
                'humedad_rel_pct': float(rh_pct),
                'timestamp': datetime.now().isoformat(),
                'source': 'GFS/NOAA',
                'forecast_hours': hours_ahead
            }
            
        except requests.Timeout:
            raise TimeoutError("GFS timeout después de 30s")
        except Exception as e:
            raise RuntimeError(f"Error GFS: {e}")
    
    def _get_latest_run(self) -> str:
        """Obtiene run más reciente (00, 06, 12, 18 UTC)"""
        now = datetime.utcnow()
        hour = now.hour
        
        # GFS runs: 00z, 06z, 12z, 18z
        run_hour = (hour // 6) * 6
        return f"gfs.t{run_hour:02d}z.pgrb2.0p25.f000"
    
    def _get_run_date(self) -> str:
        """Fecha del run (YYYYMMDD)"""
        return datetime.utcnow().strftime("%Y%m%d")
```

### PASO 4: Integrar con Execution Sandbox

```python
# En main_asgi.py
from core.apis.gfs_integration import GFSIntegration
from core.monitoring.execution_sandbox import get_sandbox

@app.get("/api/gfs/forecast")
def get_gfs_forecast(hours: int = 48):
    """Obtiene pronóstico GFS (SANDBOX: timeout 30s)"""
    
    sandbox = get_sandbox()
    gfs = GFSIntegration()
    
    # Ejecutar en sandbox (protección contra timeout)
    result = sandbox.execute_with_limits(
        "gfs_fetch",
        gfs.fetch_forecast,
        lat=41.55326700,  # Argentona
        lon=2.39684500,
        hours_ahead=hours
    )
    
    if not result.executed:
        return JSONResponse({
            "error": "GFS timeout o error",
            "violation": result.violation,
            "message": "Intenta de nuevo o reduce horizonte"
        }, status_code=504)
    
    return result.result
```

### PASO 5: Validación con ExecutionSandbox

```python
# Verificar que URL sea HTTPS y dominio confiable
sandbox = get_sandbox()
allowed, reason = sandbox.validate_url("https://nomads.ncep.noaa.gov/...")

if not allowed:
    raise SecurityError(f"URL bloqueada: {reason}")
```

---

## ALTERNATIVA: API Weather.gov (Más simple)

Si GFS es demasiado complejo, usar API REST de Weather.gov:

```python
# Mucho más simple, sin GRIB2
import requests

def get_simple_forecast(lat: float, lon: float):
    """API simple de Weather.gov (solo USA)"""
    
    # WARNING: Solo funciona en territorio USA
    # Para España, usar AEMET API (requiere clave AEMET)
    
    url = f"https://api.weather.gov/points/{lat},{lon}"
    headers = {'User-Agent': 'MeteoSerV3/1.0'}
    
    response = requests.get(url, headers=headers, timeout=10)
    data = response.json()
    
    forecast_url = data['properties']['forecast']
    forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
    
    return forecast_response.json()
```

---

## PARA ESPAÑA: Usar AEMET

AEMET (Agencia Estatal de Meteorología) tiene API oficial:

```bash
# 1. Solicitar clave en https://opendata.aemet.es/centrodedescargas/inicio
# 2. Guardar clave
echo "AEMET_API_KEY=tu_clave" >> .env
```

```python
# core/apis/aemet_integration.py
import requests
from typing import Dict

class AEMETIntegration:
    """Integración con AEMET (España)"""
    
    BASE_URL = "https://opendata.aemet.es/opendata/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_forecast_barcelona(self) -> Dict:
        """Pronóstico para Barcelona (código 08019)"""
        
        # Endpoint de predicción municipal
        url = f"{self.BASE_URL}/prediccion/especifica/municipio/diaria/08019"
        params = {'api_key': self.api_key}
        
        # Primera llamada: obtener URL de datos
        response = requests.get(url, params=params, timeout=10)
        data_url = response.json()['datos']
        
        # Segunda llamada: obtener datos reales
        forecast = requests.get(data_url, timeout=10)
        return forecast.json()
```

---

## PRIORIDADES

### FASE 1 (COMPLETADO ✅):
- ✅ ISA Bug
- ✅ Watchdog
- ✅ Auto-calibrator
- ✅ Drift Gate
- ✅ Monitor Bus
- ✅ Bias Detector

### FASE 2 (COMPLETADO ✅):
- ✅ Execution Sandbox
- ✅ LSTM Training Setup

### FASE 3 (OPCIONAL - SOLO SI NECESARIO):
- ⏳ GUI Duelos (ya existe GUI en /templates/index.html, puerto 8080)
- ⏳ GFS Integration (solo si necesitas predicción 7+ días)
- ⏳ AEMET Integration (mejor opción para España)

---

## DECISIÓN RECOMENDADA

**NO implementar GFS/NOAA ahora** porque:

1. **Complejidad alta** (GRIB2, xarray, cfgrib)
2. **Latencia alta** (10-30s por request)
3. **Requiere credenciales** (proceso de aprobación lento)
4. **MeteoSerV3 ya tiene predicción local** (LSTM)
5. **Uso personal** (no necesitas GFS profesional)

**SI necesitas pronóstico externo:**
- Usar AEMET (España, más simple)
- O OpenWeatherMap API (plan free: 1000 calls/día)

**FOCO ACTUAL:**
- Sistema autónomo está completo ✅
- Mantenimiento Zero operativo ✅
- Precisión absoluta (ISA corregido) ✅
- Todo listo para abandono 6 meses ✅

---

## EJEMPLO: OpenWeatherMap (Alternativa simple)

```python
# Mucho más simple que GFS
import requests

def get_openweather_forecast(lat, lon, api_key):
    """OpenWeatherMap API (plan free)"""
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric'  # Celsius
    }
    
    response = requests.get(url, params=params, timeout=5)
    return response.json()

# USO:
# 1. Registrar en https://openweathermap.org/api
# 2. Obtener API key (gratis, 1000 calls/día)
# 3. forecast = get_openweather_forecast(41.55, 2.39, "tu_clave")
```

---

## CONCLUSIÓN

**Sistema autónomo COMPLETADO para abandono remoto:**

✅ Watchdog → auto-recovery
✅ Auto-calibrator → compensa degradación
✅ Drift Gate → detecta anomalías <1min
✅ Bias Detector → sesgo 90 días
✅ Monitor Bus → vigilancia 33+ valores
✅ Execution Sandbox → aislamiento APIs
✅ LSTM Setup → predicción local
✅ GUI → ya existe en puerto 8080
✅ ISA Bug → presión corregida (1011.3 hPa)

**GFS/NOAA: FASE 3 (solo si necesitas predicción profesional 7+ días)**

Para uso personal: **NO necesitas GFS**. El sistema local es suficiente.

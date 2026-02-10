#!/usr/bin/env python3
"""
RECUPERACIÓN DE DATOS HISTÓRICOS - ECOWITT HP2550A
====================================================

Script para:
1. Recuperar datos del MQTT broker si el sensor está online
2. Intentar recuperar datos del cloud de Ecowitt (si hay credenciales)
3. Persistir todos los datos recuperados en el sistema

Datos cegados: Últimas 48 horas (sistema sin recibir datos)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from core.system.constants import ESTACION
from core.integration.ecowitt_receiver import app as ecowitt_app
from core.system.system_manager import SystemManager


# ═══════════════════════════════════════════════════════════════════════════════
# RECUPERACIÓN DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

class RecuperadorDatosEcowitt:
    """Recupera datos históricos de Ecowitt HP2550A"""
    
    def __init__(self):
        self.manager = SystemManager()
        self.system = self.manager.iniciar()
        self.datos_recuperados = {
            "timestamp_inicio": datetime.now().isoformat(),
            "ubicacion": {
                "latitud": ESTACION.LATITUD,
                "longitud": ESTACION.LONGITUD,
                "altitud_m": ESTACION.ALTITUD,
                "nombre": ESTACION.NOMBRE,
            },
            "datos_mqtt": [],
            "datos_cloud": [],
            "metadatos": {},
        }
        
    def obtener_datos_mqtt_local(self):
        """
        Intenta obtener datos del broker MQTT local
        (si la HP2550A ha enviado durante el tiempo ciego)
        """
        logger.info("[BUSCAR] Verificando MQTT broker local...")
        
        try:
            # MQTT suele estar en 1883
            import paho.mqtt.client as mqtt
            
            client = mqtt.Client()
            client.connect("127.0.0.1", 1883, keepalive=10)
            
            mensaje_recibido = {"data": None}
            
            def on_message(client, userdata, msg):
                """Callback cuando llega un mensaje MQTT"""
                try:
                    payload = json.loads(msg.payload.decode())
                    mensaje_recibido["data"] = payload
                    logger.info(f"[OK] MQTT recibido: {msg.topic}")
                except Exception as e:
                    logger.error(f"[ERROR] Error decodificando MQTT: {e}")
            
            client.on_message = on_message
            client.subscribe("ecowitt/#")  # Suscribirse a tópicos ecowitt
            
            # Esperar 5 segundos a que llegue data
            logger.info("  Esperando datos MQTT (5 segundos)...")
            client.loop_start()
            
            import time
            time.sleep(5)
            
            client.loop_stop()
            client.disconnect()
            
            if mensaje_recibido["data"]:
                self.datos_recuperados["datos_mqtt"].append({
                    "timestamp": datetime.now().isoformat(),
                    "datos": mensaje_recibido["data"]
                })
                logger.info(f"[OK] Datos MQTT recuperados: {mensaje_recibido['data']}")
            else:
                logger.warning("[WARNING]  No hay datos MQTT en este momento")
                
        except ImportError:
            logger.warning("[WARNING]  paho-mqtt no instalado (MQTT no disponible)")
        except Exception as e:
            logger.warning(f"[WARNING]  No se pudo conectar a MQTT: {e}")
    
    def obtener_datos_cloud_ecowitt(self):
        """
        Intenta obtener datos del cloud de Ecowitt
        Requiere: API_KEY y API_SECRET
        """
        logger.info("☁️  Intentando conectar a Ecowitt Cloud...")
        
        # Buscar credenciales
        api_key = os.getenv("ECOWITT_API_KEY")
        api_secret = os.getenv("ECOWITT_API_SECRET")
        device_id = os.getenv("ECOWITT_DEVICE_ID")
        
        if not (api_key and api_secret and device_id):
            logger.warning("[WARNING]  Credenciales Ecowitt Cloud no encontradas")
            logger.warning("   Variables esperadas: ECOWITT_API_KEY, ECOWITT_API_SECRET, ECOWITT_DEVICE_ID")
            logger.info("   Para obtenerlas: https://console.ecowitt.net/login")
            return
        
        try:
            import requests
            import hmac
            import hashlib
            
            # Endpoint de Ecowitt Cloud
            url = "https://api.ecowitt.net/api/v1/device/real_time"
            
            # Parámetros
            params = {
                "device_id": device_id,
                "application_type": "ws2500"
            }
            
            # Generar signature (HMAC-SHA256)
            timestamp = str(int(datetime.now().timestamp()))
            method = "GET"
            canonical_request = f"{method}\n{url}\n{json.dumps(params)}\n{timestamp}"
            signature = hmac.new(
                api_secret.encode(),
                canonical_request.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "Content-Type": "application/json"
            }
            
            # Realizar request
            logger.info(f"  Solicitud: GET {url}")
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.datos_recuperados["datos_cloud"].append({
                    "timestamp": datetime.now().isoformat(),
                    "datos": data
                })
                logger.info(f"[OK] Datos Cloud recuperados: {len(data)} registros")
            else:
                logger.warning(f"[WARNING]  Cloud API retornó {response.status_code}: {response.text}")
                
        except ImportError:
            logger.warning("[WARNING]  requests no instalado (Cloud API no disponible)")
        except Exception as e:
            logger.warning(f"[WARNING]  No se pudo conectar a Cloud: {e}")
    
    def obtener_historial_local_guardado(self):
        """
        Busca datos guardados localmente que puedan haber sido almacenados
        durante el tiempo "ciego"
        """
        logger.info("📁 Buscando datos guardados localmente...")
        
        data_dir = Path("data")
        
        # Buscar archivos de histórico
        historial_files = list(data_dir.glob("**/histórico*.json")) + \
                         list(data_dir.glob("**/history*.json")) + \
                         list(data_dir.glob("**/archive*.json"))
        
        if historial_files:
            logger.info(f"  Encontrados {len(historial_files)} archivos de histórico")
            for f in historial_files:
                try:
                    with open(f, 'r') as fp:
                        contenido = json.load(fp)
                        self.datos_recuperados["datos_mqtt"].append({
                            "timestamp": f.stat().st_mtime,
                            "fuente": str(f),
                            "datos": contenido
                        })
                        logger.info(f"  [OK] Cargado: {f.name}")
                except Exception as e:
                    logger.error(f"  [ERROR] Error leyendo {f}: {e}")
        else:
            logger.warning("[WARNING]  No hay archivos de histórico guardados")
    
    def persistir_datos_recuperados(self):
        """
        Guarda TODOS los datos recuperados en el sistema de forma durable
        """
        logger.info("[GUARDAR] Persistiendo datos recuperados...")
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Archivo de histórico
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_historico = data_dir / f"historico_recuperado_{timestamp_str}.json"
        
        # Agregar metadatos
        self.datos_recuperados["metadatos"] = {
            "recuperado_en": datetime.now().isoformat(),
            "periodo_ciego_dias": 2,
            "periodo_ciego_inicio": (datetime.now() - timedelta(days=2)).isoformat(),
            "periodo_ciego_fin": datetime.now().isoformat(),
            "total_mqtt_registros": len(self.datos_recuperados["datos_mqtt"]),
            "total_cloud_registros": len(self.datos_recuperados["datos_cloud"]),
        }
        
        try:
            with open(archivo_historico, 'w') as f:
                json.dump(self.datos_recuperados, f, indent=2, default=str)
            
            logger.info(f"[OK] Datos guardados en: {archivo_historico}")
            
            # También guardar en bus del sistema
            try:
                self.system.bus.publicar(
                    "datos.recuperados.historico",
                    self.datos_recuperados,
                    nivel="CRITICO",
                    origen="recuperador"
                )
                logger.info("[OK] Datos publicados en bus del sistema")
            except Exception as e:
                logger.warning(f"[WARNING]  No se pudo publicar en bus: {e}")
            
            return archivo_historico
            
        except Exception as e:
            logger.error(f"[ERROR] Error guardando datos: {e}")
            return None
    
    def generar_reporte(self):
        """Genera reporte de recuperación"""
        logger.info("\n" + "="*80)
        logger.info("[STATS] REPORTE DE RECUPERACIÓN DE DATOS")
        logger.info("="*80)
        logger.info(f"Ubicación: {ESTACION.NOMBRE}")
        logger.info(f"Coordenadas: {ESTACION.LATITUD}°N, {ESTACION.LONGITUD}°E")
        logger.info(f"Altitud: {ESTACION.ALTITUD}m")
        logger.info(f"\nPeriodo ciego: Últimas 48 horas")
        logger.info(f"Datos MQTT recuperados: {len(self.datos_recuperados['datos_mqtt'])}")
        logger.info(f"Datos Cloud recuperados: {len(self.datos_recuperados['datos_cloud'])}")
        logger.info("="*80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("[LAUNCH] RECUPERADOR DE DATOS HISTÓRICOS - ECOWITT HP2550A")
    print("="*80 + "\n")
    
    recuperador = RecuperadorDatosEcowitt()
    
    # Paso 1: Historial local guardado
    recuperador.obtener_historial_local_guardado()
    
    # Paso 2: MQTT (si hay broker)
    recuperador.obtener_datos_mqtt_local()
    
    # Paso 3: Cloud de Ecowitt (si hay credenciales)
    recuperador.obtener_datos_cloud_ecowitt()
    
    # Paso 4: Persistir en el sistema
    archivo = recuperador.persistir_datos_recuperados()
    
    # Paso 5: Reporte
    recuperador.generar_reporte()
    
    if archivo:
        print(f"[OK] ÉXITO: Datos guardados en {archivo}")
        print("\nPróximo paso: Integrar datos en índices usando:")
        print("  from core.integration.data_recovery import cargar_datos_recuperados")
    else:
        print("[ERROR] No se pudo persistir los datos")

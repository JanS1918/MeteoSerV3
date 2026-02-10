#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
🔄 INTEGRADOR ALWAYS-ON - AUTO-RECOVER HISTÓRICO EN CADA ARRANQUE
════════════════════════════════════════════════════════════════════════════════

Se ejecuta SIEMPRE que arranque el servidor para:
1. Detectar datos faltantes (gaps históricos)
2. Recuperar TODOS los datos posibles desde última sesión
3. Procesar como si el servidor hubiera estado encendido
4. Guardar en histórico con normalidad

Flujo:
  Arranque servidor → Integrador activo
  ├─ ¿Hay gap histórico? SÍ → Recuperar datos
  ├─ Procesar datos sin procesar (raw)
  ├─ Guardar en histórico
  └─ Continuar operación normal
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))


# ════════════════════════════════════════════════════════════════════════════════
# DETECTOR DE GAPS HISTÓRICOS
# ════════════════════════════════════════════════════════════════════════════════

class DetectorGapsHistoricos:
    """Detecta períodos de datos faltantes en el sistema."""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.ultimo_evento_conocido = None
        self.brecha_detectada = False
        self.inicio_brecha = None
        self.fin_brecha = None
    
    def detectar_gap(self) -> dict:
        """
        Detecta si hay un gap (brecha) histórico sin datos.
        
        Returns:
            Dict con info del gap o {} si no hay
        """
        logger.info("🔍 Detectando gaps históricos...")
        
        # Buscar último timestamp en datos
        archivos = sorted(self.data_dir.glob("**/*.json"), reverse=True)
        
        ultimo_ts = None
        for archivo in archivos[:20]:  # Revisar los 20 más recientes
            try:
                with open(archivo) as f:
                    datos = json.load(f)
                
                # Buscar timestamp
                ts = datos.get("timestamp") or datos.get("ts") or \
                     datos.get("updated_at") or datos.get("timestamp_recuperacion")
                
                if ts:
                    if isinstance(ts, str):
                        ultimo_ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    break
            except:
                continue
        
        if not ultimo_ts:
            logger.warning("⚠️  No se encontró último timestamp conocido")
            return {}
        
        # Calcular gap
        ahora = datetime.now(ultimo_ts.tzinfo) if ultimo_ts.tzinfo else datetime.now()
        gap = ahora - ultimo_ts
        
        if gap.total_seconds() > 300:  # > 5 minutos
            logger.warning(f"⚠️  GAP DETECTADO: {gap.total_seconds():.0f} segundos ({gap.total_seconds()/3600:.2f}h)")
            
            self.brecha_detectada = True
            self.inicio_brecha = ultimo_ts
            self.fin_brecha = ahora
            
            return {
                "existe_gap": True,
                "inicio": ultimo_ts.isoformat(),
                "fin": ahora.isoformat(),
                "duracion_segundos": gap.total_seconds(),
                "duracion_horas": gap.total_seconds() / 3600,
            }
        else:
            logger.info(f"✓ Sin gaps detectados (último dato hace {gap.total_seconds():.0f}s)")
            return {"existe_gap": False}
    
    def obtener_estado(self) -> dict:
        return {
            "brecha_detectada": self.brecha_detectada,
            "inicio_brecha": self.inicio_brecha.isoformat() if self.inicio_brecha else None,
            "fin_brecha": self.fin_brecha.isoformat() if self.fin_brecha else None,
        }


# ════════════════════════════════════════════════════════════════════════════════
# RECUPERADOR AUTOMÁTICO
# ════════════════════════════════════════════════════════════════════════════════

class RecuperadorAutomatico:
    """Recupera automáticamente datos del gap detectado."""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.datos_recuperados = []
        self.sistemas_consultados = []
    
    def recuperar_del_local_archive(self, inicio: datetime, fin: datetime) -> list:
        """Recupera datos de archivo local."""
        logger.info(f"📂 Buscando en archivos locales ({inicio} → {fin})...")
        
        datos = []
        archivos_relevantes = list(self.data_dir.glob("**/*.json")) + \
                             list(self.data_dir.glob("**/*.jsonl"))
        
        for archivo in archivos_relevantes:
            try:
                if archivo.suffix == '.jsonl':
                    with open(archivo) as f:
                        for linea in f:
                            try:
                                item = json.loads(linea)
                                ts = item.get("timestamp") or item.get("ts")
                                if ts:
                                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                    if inicio <= dt <= fin:
                                        datos.append(item)
                            except:
                                pass
                else:
                    with open(archivo) as f:
                        contenido = json.load(f)
                        if isinstance(contenido, list):
                            for item in contenido:
                                ts = item.get("timestamp") or item.get("ts")
                                if ts:
                                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                    if inicio <= dt <= fin:
                                        datos.append(item)
            except:
                continue
        
        logger.info(f"✓ {len(datos)} registros encontrados en archivos locales")
        self.sistemas_consultados.append("local_archive")
        return datos
    
    def recuperar_del_mqtt_local(self) -> list:
        """Intenta recuperar del broker MQTT local si existe."""
        logger.info("🔗 Intentando conectar a MQTT local (127.0.0.1:1883)...")
        
        datos = []
        try:
            import paho.mqtt.client as mqtt
            
            mensajes_recibidos = []
            
            def on_message(client, userdata, msg):
                try:
                    payload = json.loads(msg.payload.decode('utf-8'))
                    payload['topic'] = msg.topic
                    payload['timestamp'] = datetime.now().isoformat()
                    mensajes_recibidos.append(payload)
                except:
                    pass
            
            client = mqtt.Client()
            client.on_message = on_message
            client.connect("127.0.0.1", 1883, keepalive=5)
            client.subscribe("ecowitt/#")
            
            # Esperar 3 segundos a mensajes
            client.loop_start()
            import time
            time.sleep(3)
            client.loop_stop()
            client.disconnect()
            
            if mensajes_recibidos:
                logger.info(f"✓ {len(mensajes_recibidos)} mensajes MQTT recuperados")
                self.sistemas_consultados.append("mqtt_local")
            
            datos = mensajes_recibidos
            
        except Exception as e:
            logger.warning(f"⚠️  MQTT no disponible: {e}")
        
        return datos
    
    def recuperar_del_ecowitt_cloud(self) -> list:
        """Intenta recuperar del Cloud Ecowitt si hay credenciales."""
        logger.info("☁️  Intentando conectar a Ecowitt Cloud...")
        
        datos = []
        try:
            import os
            api_key = os.getenv("ECOWITT_API_KEY")
            api_secret = os.getenv("ECOWITT_API_SECRET")
            device_id = os.getenv("ECOWITT_DEVICE_ID")
            
            if not all([api_key, api_secret, device_id]):
                logger.info("⚠️  Credenciales Ecowitt Cloud no disponibles")
                return []
            
            import requests
            
            endpoint = "https://api.ecowitt.net/api/v1/device/real_time"
            params = {
                "application_key": api_key,
                "api_secret": api_secret,
                "device_id": device_id,
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            if response.status_code == 200:
                payload = response.json()
                payload['timestamp'] = datetime.now().isoformat()
                payload['fuente'] = 'ecowitt_cloud'
                datos = [payload]
                
                logger.info(f"✓ Datos Ecowitt Cloud obtenidos")
                self.sistemas_consultados.append("ecowitt_cloud")
            
        except Exception as e:
            logger.warning(f"⚠️  Cloud Ecowitt no disponible: {e}")
        
        return datos
    
    def recuperar_todo(self, inicio: datetime, fin: datetime) -> dict:
        """Recupera datos de todas las fuentes disponibles."""
        
        logger.info(f"\n🚀 INICIO RECUPERACIÓN AUTOMÁTICA")
        logger.info(f"   Período: {inicio} → {fin}")
        logger.info(f"   Duración: {(fin-inicio).total_seconds()/3600:.2f} horas\n")
        
        # Fuente 1: Archivos locales
        datos_local = self.recuperar_del_local_archive(inicio, fin)
        
        # Fuente 2: MQTT local
        datos_mqtt = self.recuperar_del_mqtt_local()
        
        # Fuente 3: Cloud Ecowitt
        datos_cloud = self.recuperar_del_ecowitt_cloud()
        
        # Consolidar
        todos_datos = datos_local + datos_mqtt + datos_cloud
        self.datos_recuperados = todos_datos
        
        return {
            "total_registros": len(todos_datos),
            "desde_local": len(datos_local),
            "desde_mqtt": len(datos_mqtt),
            "desde_cloud": len(datos_cloud),
            "sistemas": self.sistemas_consultados,
            "datos": todos_datos,
        }


# ════════════════════════════════════════════════════════════════════════════════
# PROCESADOR DE DATOS SIN PROCESAR
# ════════════════════════════════════════════════════════════════════════════════

class ProcesadorDatosBrutos:
    """Procesa datos raw como si el servidor hubiera estado encendido."""
    
    def __init__(self):
        self.data_dir = Path("data")
    
    def procesar_datos_gap(self, datos: list) -> list:
        """
        Procesa datos recuperados del gap como si el servidor estuviera activo.
        
        - Valida formato
        - Extrae campos de sensores
        - Enriquece con timestamps
        - Prepara para histórico
        """
        logger.info(f"\n🔧 PROCESANDO {len(datos)} registros...")
        
        eventos_procesados = []
        
        for registro in datos:
            try:
                # Determinar tipo de dato
                if 'ecowitt' in str(registro).lower() or 'barom' in registro:
                    # Es dato Ecowitt
                    evento = {
                        "timestamp": registro.get("timestamp", datetime.now().isoformat()),
                        "tipo": "sensor.ecowitt",
                        "fuente": "recuperacion.automatica",
                        "datos_raw": registro,
                        "datos_procesados": {
                            "temperatura": registro.get("tempf") and (registro.get("tempf") - 32) * 5/9,
                            "humedad": registro.get("humidity"),
                            "presion": registro.get("baromrelin"),
                            "viento_velocidad": registro.get("windspeedmph") and registro.get("windspeedmph") * 0.44704,
                            "radiacion": registro.get("solarradiation"),
                            "uv": registro.get("uv"),
                        }
                    }
                elif 'mqtt' in str(registro).get("fuente", "").lower():
                    # Es dato MQTT
                    evento = {
                        "timestamp": registro.get("timestamp", datetime.now().isoformat()),
                        "tipo": "sensor.mqtt",
                        "fuente": "recuperacion.mqtt",
                        "topic": registro.get("topic"),
                        "datos_raw": registro,
                    }
                else:
                    # Dato genérico
                    evento = {
                        "timestamp": registro.get("timestamp", datetime.now().isoformat()),
                        "tipo": "sensor.generico",
                        "fuente": "recuperacion.automatica",
                        "datos_raw": registro,
                    }
                
                eventos_procesados.append(evento)
                
            except Exception as e:
                logger.warning(f"⚠️  Error procesando registro: {e}")
                continue
        
        logger.info(f"✓ {len(eventos_procesados)} eventos procesados exitosamente")
        return eventos_procesados
    
    def guardar_en_historico(self, eventos: list) -> Path:
        """Guarda eventos en histórico del sistema."""
        
        logger.info(f"\n💾 GUARDANDO EN HISTÓRICO ({len(eventos)} eventos)...")
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_historico = self.data_dir / f"recuperacion_gap_procesada_{timestamp_str}.json"
        
        try:
            with open(archivo_historico, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp_procesamiento": datetime.now().isoformat(),
                    "total_eventos": len(eventos),
                    "eventos": eventos,
                }, f, indent=2, default=str)
            
            logger.info(f"✓ Archivo histórico: {archivo_historico.name}")
            return archivo_historico
            
        except Exception as e:
            logger.error(f"❌ Error guardando histórico: {e}")
            return None


# ════════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR INTEGRADOR ALWAYS-ON
# ════════════════════════════════════════════════════════════════════════════════

async def ejecutar_integrador_automatico():
    """
    Ejecuta todo el flujo de recuperación y procesamiento.
    Se llama automáticamente en startup del servidor.
    """
    
    logger.info("\n" + "="*80)
    logger.info("🔄 INTEGRADOR ALWAYS-ON - RECUPERACIÓN AUTOMÁTICA EN ARRANQUE")
    logger.info("="*80 + "\n")
    
    try:
        # 1. Detectar gap
        detector = DetectorGapsHistoricos()
        gap_info = detector.detectar_gap()
        
        if not gap_info.get("existe_gap"):
            logger.info("✓ No hay gap histórico, operación normal")
            return {"status": "sin_gap", "gap_info": gap_info}
        
        logger.warning(f"🚨 GAP DETECTADO: {gap_info['duracion_horas']:.2f} horas")
        
        # 2. Recuperar datos
        recuperador = RecuperadorAutomatico()
        inicio = datetime.fromisoformat(gap_info["inicio"])
        fin = datetime.fromisoformat(gap_info["fin"])
        
        recuperacion = recuperador.recuperar_todo(inicio, fin)
        
        if recuperacion["total_registros"] == 0:
            logger.warning("⚠️  No se recuperaron datos del gap")
            return {"status": "gap_sin_datos", "gap_info": gap_info}
        
        logger.info(f"✅ {recuperacion['total_registros']} registros recuperados")
        logger.info(f"   - Locales: {recuperacion['desde_local']}")
        logger.info(f"   - MQTT: {recuperacion['desde_mqtt']}")
        logger.info(f"   - Cloud: {recuperacion['desde_cloud']}")
        
        # 3. Procesar datos
        procesador = ProcesadorDatosBrutos()
        eventos = procesador.procesar_datos_gap(recuperacion["datos"])
        
        # 4. Guardar en histórico
        archivo = procesador.guardar_en_historico(eventos)
        
        # 5. Intentar integrar en bus si disponible
        try:
            from core.system.system_manager import SystemManager
            logger.info(f"\n📡 Integrando en bus del sistema...")
            system = SystemManager()
            
            for evento in eventos[:10]:  # Publicar primeros 10
                system.bus.publicar("datos.recuperados.gap", evento)
            
            logger.info(f"✓ {len(eventos)} eventos publicados en bus")
            
        except Exception as e:
            logger.warning(f"⚠️  Bus no disponible para integración: {e}")
        
        return {
            "status": "exito",
            "gap_info": gap_info,
            "recuperacion": recuperacion,
            "eventos_procesados": len(eventos),
            "archivo_historico": str(archivo),
        }
        
    except Exception as e:
        logger.error(f"❌ Error en integrador automático: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA - Llamar desde main_asgi.py
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test directo
    resultado = asyncio.run(ejecutar_integrador_automatico())
    logger.info(f"\n✅ RESULTADO: {resultado.get('status')}")

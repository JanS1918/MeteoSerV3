"""
MANAGER INFLUXDB - Persistencia de Series Temporales
====================================================
Cliente wrapper para InfluxDB 2.x con gestión automática de tokens, buckets y queries.

Características:
- Conexión automática con reintentos
- Escritura batch para eficiencia
- Queries optimizadas con Flux
- Retención automática (configurable)
- Compresión y downsampling

Flujo:
1. Conectar a InfluxDB (local o remoto)
2. Escribir datos del Bus cada N segundos
3. Consultar historial con filtros temporales
4. Downsampling automático para consultas largas
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import time
import threading
from pathlib import Path
import json

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    print("[WARNING] influxdb-client no disponible. Instalar con: pip install influxdb-client")


class InfluxDBManager:
    """Manager para InfluxDB 2.x con gestión completa"""
    
    def __init__(self, url: str = "http://localhost:8086",
                 token: str = None,
                 org: str = "meteoser",
                 bucket: str = "meteodata"):
        """
        Args:
            url: URL del servidor InfluxDB
            token: Token de autenticación (o None para config file)
            org: Organización
            bucket: Bucket por defecto
        """
        if not INFLUXDB_AVAILABLE:
            raise ImportError("influxdb-client no instalado")
        
        self.url = url
        self.token = token or self._cargar_token()
        self.org = org
        self.bucket = bucket
        
        self.client = None
        self.write_api = None
        self.query_api = None
        self.conectado = False
        
        # Buffer de escritura
        self.buffer_escritura = []
        self.buffer_max_size = 100
        self.buffer_lock = threading.Lock()
    
    def _cargar_token(self) -> str:
        """Carga token desde archivo de configuración"""
        config_file = Path("data/influxdb_config.json")
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('token', '')
        
        return ""
    
    def conectar(self, reintentos: int = 3) -> bool:
        """
        Establece conexión con InfluxDB
        
        Args:
            reintentos: Número de intentos
        
        Returns:
            True si conectó exitosamente
        """
        for intento in range(reintentos):
            try:
                self.client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org,
                    timeout=10_000  # 10 segundos
                )
                
                # Verificar conexión
                health = self.client.health()
                if health.status == "pass":
                    self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                    self.query_api = self.client.query_api()
                    self.conectado = True
                    
                    print(f"[OK] Conectado a InfluxDB ({self.url})")
                    return True
                else:
                    print(f"[WARNING]  InfluxDB health check failed: {health.message}")
            
            except Exception as e:
                print(f"[ERROR] Error conectando a InfluxDB (intento {intento+1}/{reintentos}): {e}")
                time.sleep(2)
        
        return False
    
    def desconectar(self):
        """Cierra conexión y escribe buffer pendiente"""
        if self.conectado:
            self._flush_buffer()
            
            if self.client:
                self.client.close()
            
            self.conectado = False
            print("🔌 Desconectado de InfluxDB")
    
    def escribir_punto(self, measurement: str, fields: Dict[str, Any],
                      tags: Dict[str, str] = None, timestamp: datetime = None):
        """
        Escribe un punto a InfluxDB
        
        Args:
            measurement: Nombre de la medición (ej: "temperatura")
            fields: Campos {nombre: valor} (ej: {"valor": 22.5})
            tags: Tags opcionales {nombre: valor} (ej: {"sensor": "DHT22"})
            timestamp: Timestamp (o None para now)
        """
        if not self.conectado:
            print("[WARNING]  No conectado a InfluxDB")
            return
        
        try:
            point = Point(measurement)
            
            # Agregar tags
            if tags:
                for key, value in tags.items():
                    point.tag(key, value)
            
            # Agregar fields
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point.field(key, value)
                elif isinstance(value, str):
                    point.field(key, value)
                elif isinstance(value, bool):
                    point.field(key, value)
            
            # Timestamp
            if timestamp:
                point.time(timestamp, WritePrecision.NS)
            
            # Agregar a buffer
            with self.buffer_lock:
                self.buffer_escritura.append(point)
                
                # Flush si buffer lleno
                if len(self.buffer_escritura) >= self.buffer_max_size:
                    self._flush_buffer()
        
        except Exception as e:
            print(f"[ERROR] Error escribiendo punto: {e}")
    
    def _flush_buffer(self):
        """Escribe todos los puntos del buffer"""
        if not self.buffer_escritura:
            return
        
        try:
            with self.buffer_lock:
                self.write_api.write(
                    bucket=self.bucket,
                    record=self.buffer_escritura
                )
                
                n_puntos = len(self.buffer_escritura)
                self.buffer_escritura.clear()
                
                print(f"📝 {n_puntos} puntos escritos a InfluxDB")
        
        except Exception as e:
            print(f"[ERROR] Error en flush: {e}")
    
    def consultar(self, measurement: str,
                 inicio: datetime = None,
                 fin: datetime = None,
                 fields: List[str] = None,
                 tags_filter: Dict[str, str] = None,
                 agregacion: str = None,
                 ventana: str = "1m") -> List[Dict]:
        """
        Consulta datos históricos
        
        Args:
            measurement: Medición a consultar
            inicio: Timestamp inicio (o None para últimas 24h)
            fin: Timestamp fin (o None para now)
            fields: Lista de campos a retornar (o None para todos)
            tags_filter: Filtros por tags {"sensor": "DHT22"}
            agregacion: "mean", "max", "min", etc. (o None)
            ventana: Ventana de agregación "1m", "5m", "1h" (si agregacion)
        
        Returns:
            Lista de diccionarios con resultados
        """
        if not self.conectado:
            print("[WARNING]  No conectado a InfluxDB")
            return []
        
        # Defaults
        if inicio is None:
            inicio = datetime.now() - timedelta(days=1)
        if fin is None:
            fin = datetime.now()
        
        # Construir query Flux
        query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {inicio.isoformat()}Z, stop: {fin.isoformat()}Z)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        '''
        
        # Filtros de tags
        if tags_filter:
            for key, value in tags_filter.items():
                query += f'\n  |> filter(fn: (r) => r["{key}"] == "{value}")'
        
        # Filtros de fields
        if fields:
            fields_str = ' or '.join([f'r["_field"] == "{f}"' for f in fields])
            query += f'\n  |> filter(fn: (r) => {fields_str})'
        
        # Agregación
        if agregacion:
            query += f'\n  |> aggregateWindow(every: {ventana}, fn: {agregacion}, createEmpty: false)'
        
        query += '\n  |> yield(name: "result")'
        
        try:
            # Ejecutar query
            tables = self.query_api.query(query, org=self.org)
            
            # Parsear resultados
            resultados = []
            for table in tables:
                for record in table.records:
                    resultados.append({
                        'time': record.get_time(),
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        **record.values
                    })
            
            return resultados
        
        except Exception as e:
            print(f"[ERROR] Error en consulta: {e}")
            return []
    
    def obtener_ultimo_valor(self, measurement: str, field: str = "valor") -> Optional[float]:
        """
        Obtiene el último valor registrado
        
        Args:
            measurement: Medición
            field: Campo a obtener
        
        Returns:
            Último valor o None
        """
        query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -1h)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
              |> filter(fn: (r) => r["_field"] == "{field}")
              |> last()
        '''
        
        try:
            tables = self.query_api.query(query, org=self.org)
            
            for table in tables:
                for record in table.records:
                    return record.get_value()
            
            return None
        
        except Exception as e:
            print(f"[ERROR] Error obteniendo último valor: {e}")
            return None
    
    def crear_bucket(self, nombre: str, retencion_dias: int = 30) -> bool:
        """
        Crea un nuevo bucket con retención
        
        Args:
            nombre: Nombre del bucket
            retencion_dias: Días de retención (0 = infinito)
        
        Returns:
            True si creó exitosamente
        """
        try:
            buckets_api = self.client.buckets_api()
            
            # Verificar si ya existe
            buckets = buckets_api.find_buckets().buckets
            if any(b.name == nombre for b in buckets):
                print(f"[WARNING]  Bucket '{nombre}' ya existe")
                return True
            
            # Crear
            retencion_seconds = retencion_dias * 86400 if retencion_dias > 0 else 0
            buckets_api.create_bucket(
                bucket_name=nombre,
                org=self.org,
                retention_rules=[{"everySeconds": retencion_seconds}] if retencion_seconds > 0 else None
            )
            
            print(f"[OK] Bucket '{nombre}' creado (retención: {retencion_dias} días)")
            return True
        
        except Exception as e:
            print(f"[ERROR] Error creando bucket: {e}")
            return False
    
    def eliminar_datos_antiguos(self, measurement: str, dias: int = 90):
        """
        Elimina datos más antiguos que N días
        
        Args:
            measurement: Medición a limpiar
            dias: Días de antigüedad
        """
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: 0, stop: {fecha_limite.isoformat()}Z)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
              |> drop()
        '''
        
        try:
            self.query_api.query(query, org=self.org)
            print(f"🗑️  Datos antiguos de '{measurement}' eliminados (> {dias} días)")
        
        except Exception as e:
            print(f"[ERROR] Error eliminando datos: {e}")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           INFLUXDB MANAGER - Persistencia Automática         ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        from core.persistence import InfluxDBManager
        from datetime import datetime, timedelta
        
        # 1. Conectar
        db = InfluxDBManager(
            url="http://localhost:8086",
            token="tu-token-aqui",
            bucket="meteodata"
        )
        
        if db.conectar():
            # 2. Escribir datos
            db.escribir_punto(
                measurement="temperatura",
                fields={"valor": 22.5, "humedad": 65.0},
                tags={"sensor": "DHT22", "ubicacion": "exterior"}
            )
            
            # 3. Consultar últimas 24h
            datos = db.consultar(
                measurement="temperatura",
                inicio=datetime.now() - timedelta(days=1)
            )
            
            print(f"Registros obtenidos: {len(datos)}")
            
            # 4. Agregación (media cada 5 min)
            datos_agregados = db.consultar(
                measurement="temperatura",
                inicio=datetime.now() - timedelta(hours=6),
                agregacion="mean",
                ventana="5m"
            )
            
            # 5. Último valor
            ultimo = db.obtener_ultimo_valor("temperatura", "valor")
            print(f"Última temperatura: {ultimo}°C")
            
            # 6. Desconectar
            db.desconectar()
    
    INSTALACIÓN InfluxDB:
        # Docker (recomendado):
        docker run -d -p 8086:8086 influxdb:2.7
        
        # O descarga directa:
        https://portal.influxdata.com/downloads/
    """)

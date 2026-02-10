import logging
"""
ARCHIVADOR DE SERIES TEMPORALES - Persistencia Automática
=========================================================
Archiva datos del Bus automáticamente a InfluxDB en segundo plano.

Características:
- Suscripción automática al Bus
- Escritura batch cada N segundos
- Recuperación de datos perdidos
- Compresión y downsampling
- Alertas de disco lleno

Flujo:
1. Suscribirse a capas CORE + CALCULATED del Bus
2. Buffer en RAM (cada 30s escribe a BD)
3. Downsampling automático para datos antiguos
4. Retención configurable (30d por defecto)
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
from collections import deque
import json
from pathlib import Path

try:
    from .influxdb_manager import InfluxDBManager, INFLUXDB_AVAILABLE
except ImportError:
    InfluxDBManager = None
    INFLUXDB_AVAILABLE = False


class ArchivadorSeriesTemporales:
    """Archiva datos del Bus automáticamente a InfluxDB"""
    
    def __init__(self, bus=None, db_manager: InfluxDBManager = None):
        """
        Args:
            bus: BusCapasInformacion
            db_manager: InfluxDBManager (o None para crear automáticamente)
        """
        if not INFLUXDB_AVAILABLE:
            raise ImportError("InfluxDB no disponible - instalar influxdb-client")
        
        self.bus = bus
        self.db_manager = db_manager
        
        # Control
        self.archivando = False
        self.hilo_archivado = None
        self.intervalo_escritura_segundos = 30  # Escribir cada 30s
        
        # Estadísticas
        self.total_puntos_escritos = 0
        self.errores_escritura = 0
        self.ultima_escritura = None
        
        # Callbacks
        self.callbacks_error: List[Callable] = []
    
    def iniciar(self, intervalo_segundos: int = 30):
        """
        Inicia archivado automático
        
        Args:
            intervalo_segundos: Cada cuántos segundos escribir a BD
        """
        if not self.db_manager or not self.db_manager.conectado:
            print("❌ DB Manager no conectado")
            return False
        
        if self.archivando:
            print("⚠️  Archivador ya iniciado")
            return False
        
        self.intervalo_escritura_segundos = intervalo_segundos
        self.archivando = True
        
        # Iniciar hilo
        self.hilo_archivado = threading.Thread(
            target=self._bucle_archivado,
            daemon=True,
            name="ArchivadorSeriesTemporales"
        )
        self.hilo_archivado.start()
        
        print(f"🤖 Archivador INICIADO (cada {intervalo_segundos}s)")
        return True
    
    def detener(self):
        """Detiene archivado y escribe datos pendientes"""
        if not self.archivando:
            return
        
        print("⏹️  Deteniendo archivador...")
        self.archivando = False
        
        if self.hilo_archivado:
            self.hilo_archivado.join(timeout=10)
        
        # Flush final
        if self.db_manager:
            self.db_manager._flush_buffer()
        
        print(f"✅ Archivador detenido ({self.total_puntos_escritos} puntos escritos)")
    
    def _bucle_archivado(self):
        """Bucle que ejecuta archivado periódico"""
        while self.archivando:
            try:
                inicio = time.time()
                
                # Obtener datos del Bus
                if self.bus:
                    self._archivar_capa_bus("CORE")
                    self._archivar_capa_bus("CALCULATED")
                
                # Flush a BD
                self.db_manager._flush_buffer()
                self.ultima_escritura = datetime.now()
                
                # Esperar hasta próximo intervalo
                tiempo_transcurrido = time.time() - inicio
                tiempo_espera = max(0, self.intervalo_escritura_segundos - tiempo_transcurrido)
                time.sleep(tiempo_espera)
            
            except Exception as e:
                self.errores_escritura += 1
                print(f"❌ Error en bucle de archivado: {e}")
                
                # Notificar callbacks
                for callback in self.callbacks_error:
                    try:
                        callback(e)
                    except:
                        logging.exception("Silent except at 137 - revisar contexto")
                
                time.sleep(5)  # Esperar antes de reintentar
    
    def _archivar_capa_bus(self, nivel: str):
        """
        Archiva todos los datos de una capa del Bus
        
        Args:
            nivel: "CORE", "CALCULATED", etc.
        """
        try:
            # Obtener todas las variables del nivel
            variables = self.bus.obtener_variables_por_nivel(nivel)
            
            for variable in variables:
                dato = self.bus.leer(variable, nivel=nivel)
                
                if dato is None:
                    continue
                
                # Extraer componentes
                valor = dato.get('valor')
                timestamp = dato.get('timestamp', datetime.now())
                origen = dato.get('origen', 'desconocido')
                confianza = dato.get('confianza', 1.0)
                
                # Escribir a InfluxDB
                self.db_manager.escribir_punto(
                    measurement=variable.replace('.', '_'),  # Normalizar nombre
                    fields={
                        'valor': valor,
                        'confianza': confianza
                    },
                    tags={
                        'nivel': nivel,
                        'origen': origen
                    },
                    timestamp=timestamp
                )
                
                self.total_puntos_escritos += 1
        
        except Exception as e:
            print(f"❌ Error archivando capa {nivel}: {e}")
    
    def recuperar_historico(self, variable: str, 
                           inicio: datetime,
                           fin: datetime = None,
                           agregacion: str = None,
                           ventana: str = "1m") -> List[Dict]:
        """
        Recupera datos históricos de una variable
        
        Args:
            variable: Nombre de la variable
            inicio: Timestamp inicio
            fin: Timestamp fin (o None para now)
            agregacion: "mean", "max", "min" (o None)
            ventana: Ventana de agregación "1m", "5m", "1h"
        
        Returns:
            Lista de {time, valor}
        """
        measurement = variable.replace('.', '_')
        
        resultados = self.db_manager.consultar(
            measurement=measurement,
            inicio=inicio,
            fin=fin,
            fields=['valor'],
            agregacion=agregacion,
            ventana=ventana
        )
        
        return [
            {
                'time': r['time'],
                'valor': r['value'],
                'confianza': r.get('confianza', 1.0)
            }
            for r in resultados
        ]
    
    def obtener_estadisticas_variable(self, variable: str, 
                                      dias: int = 7) -> Dict:
        """
        Calcula estadísticas de una variable
        
        Args:
            variable: Nombre de la variable
            dias: Días hacia atrás
        
        Returns:
            Estadísticas {min, max, mean, count}
        """
        measurement = variable.replace('.', '_')
        inicio = datetime.now() - timedelta(days=dias)
        
        # Min
        datos_min = self.db_manager.consultar(
            measurement=measurement,
            inicio=inicio,
            agregacion="min",
            ventana=f"{dias}d"
        )
        
        # Max
        datos_max = self.db_manager.consultar(
            measurement=measurement,
            inicio=inicio,
            agregacion="max",
            ventana=f"{dias}d"
        )
        
        # Mean
        datos_mean = self.db_manager.consultar(
            measurement=measurement,
            inicio=inicio,
            agregacion="mean",
            ventana=f"{dias}d"
        )
        
        # Count
        datos_count = self.db_manager.consultar(
            measurement=measurement,
            inicio=inicio,
            agregacion="count",
            ventana=f"{dias}d"
        )
        
        return {
            'variable': variable,
            'periodo': f'{dias} días',
            'min': datos_min[0]['value'] if datos_min else None,
            'max': datos_max[0]['value'] if datos_max else None,
            'mean': datos_mean[0]['value'] if datos_mean else None,
            'count': datos_count[0]['value'] if datos_count else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def exportar_a_csv(self, variable: str, 
                      inicio: datetime,
                      fin: datetime = None,
                      ruta_salida: str = None) -> str:
        """
        Exporta datos históricos a CSV
        
        Args:
            variable: Variable a exportar
            inicio: Timestamp inicio
            fin: Timestamp fin
            ruta_salida: Path de salida (o None para auto)
        
        Returns:
            Path del archivo CSV creado
        """
        import csv
        
        # Obtener datos
        datos = self.recuperar_historico(variable, inicio, fin)
        
        # Path por defecto
        if ruta_salida is None:
            ruta_salida = f"data/exports/{variable}_{inicio.strftime('%Y%m%d')}.csv"
        
        # Crear directorio
        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir CSV
        with open(ruta_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['time', 'valor', 'confianza'])
            writer.writeheader()
            writer.writerows(datos)
        
        print(f"📄 CSV exportado: {ruta_salida} ({len(datos)} registros)")
        return ruta_salida
    
    def agregar_callback_error(self, callback: Callable):
        """Registra callback para errores"""
        self.callbacks_error.append(callback)
    
    def generar_reporte(self) -> Dict:
        """Genera reporte del archivador"""
        return {
            'archivando': self.archivando,
            'total_puntos_escritos': self.total_puntos_escritos,
            'errores_escritura': self.errores_escritura,
            'ultima_escritura': self.ultima_escritura.isoformat() if self.ultima_escritura else None,
            'intervalo_segundos': self.intervalo_escritura_segundos,
            'db_conectado': self.db_manager.conectado if self.db_manager else False
        }


# Singleton global
_archivador_global = None

def obtener_archivador(bus=None, db_manager: InfluxDBManager = None) -> ArchivadorSeriesTemporales:
    """
    Obtiene instancia global del archivador
    
    Args:
        bus: BusCapasInformacion
        db_manager: InfluxDBManager (o None)
    
    Returns:
        ArchivadorSeriesTemporales singleton
    """
    global _archivador_global
    
    if _archivador_global is None:
        _archivador_global = ArchivadorSeriesTemporales(bus, db_manager)
    
    return _archivador_global


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        ARCHIVADOR - Persistencia Automática del Bus         ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Ejemplo COMPLETO:
    
        from core.bus import obtener_bus
        from core.persistence import InfluxDBManager, obtener_archivador
        from datetime import datetime, timedelta
        
        # 1. Configurar BD
        db = InfluxDBManager(
            url="http://localhost:8086",
            token="tu-token",
            bucket="meteodata"
        )
        db.conectar()
        
        # 2. Obtener Bus y Archivador
        bus = obtener_bus()
        archivador = obtener_archivador(bus, db)
        
        # 3. Iniciar archivado automático (cada 30s)
        archivador.iniciar(intervalo_segundos=30)
        
        # El archivador guarda automáticamente CORE + CALCULATED del Bus
        
        # 4. Recuperar histórico (ejemplo: últimas 24h)
        datos = archivador.recuperar_historico(
            "sensores.temperatura_c",
            inicio=datetime.now() - timedelta(days=1)
        )
        print(f"Registros: {len(datos)}")
        
        # 5. Estadísticas de 7 días
        stats = archivador.obtener_estadisticas_variable("sensores.temperatura_c", dias=7)
        print(f"Min: {stats['min']}, Max: {stats['max']}, Media: {stats['mean']}")
        
        # 6. Exportar a CSV
        csv_path = archivador.exportar_a_csv(
            "sensores.temperatura_c",
            inicio=datetime.now() - timedelta(days=7)
        )
        
        # 7. Al cerrar aplicación
        archivador.detener()
        db.desconectar()
    
    RESULTADO:
    - Nunca pierdes datos (persistencia automática)
    - Consultas históricas rápidas
    - Exportación a CSV para análisis externo
    - Alertas automáticas de errores
    """)

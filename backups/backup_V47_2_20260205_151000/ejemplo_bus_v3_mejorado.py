"""
INTEGRACIÓN DEL BUS MEJORADO - Ejemplo Completo
==============================================
Cómo integrar los componentes del Bus Dual con ADN + Delta Publishing.

Este archivo muestra la arquitectura final y cómo usarla.
"""

from core.bus.bus_indexer import BusIndexer
from core.bus.bus_async_writer import BusAsyncWriter, WriterConIntento
from core.bus.dato_historico import DatoConHistorico, BufferCircular
from core.bus.bus_snapshot import BusSnapshotDinamico
import time


class BusV3Mejorado:
    """
    Bus Mejorado con todas las optimizaciones:
    ✅ ADN (Namespacing)
    ✅ Indexación (O(k) búsquedas)
    ✅ Async Writer (lock-free)
    ✅ Histórico integrado (para LSTM)
    ✅ Delta Publishing (Pulso mínimo)
    ✅ Snapshot dinámico (sin sesgo)
    """
    
    def __init__(self, tamaño_cola_escritura: int = 10000,
                 ventana_historico: int = 100):
        """
        Args:
            tamaño_cola_escritura: Max escrituras pendientes
            ventana_historico: Muestras por variable
        """
        
        # 1. INDEXER (búsquedas rápidas)
        self.indexer = BusIndexer()
        
        # 2. ASYNC WRITER (escritura sin contención)
        self.writer = BusAsyncWriter(tamaño_cola=tamaño_cola_escritura)
        self.writer_con_reintentos = WriterConIntento(self.writer, max_reintentos=3)
        
        # 3. BUFFER CIRCULAR (histórico + estadísticas)
        self.buffer_circular = BufferCircular()
        
        # 4. SNAPSHOT DINÁMICO (resumen automático)
        self.snapshot = BusSnapshotDinamico(tamaño_maximo_snapshot=100)
        
        # 5. CONFIGURACIÓN DE DELTA PUBLISHING
        self.umbrales_delta = {}  # {"adn": 0.1, "adn:intervalo": 60}
        
        # Estado
        self.iniciado = False
        
        # Estadísticas
        self.total_publicaciones = 0
        self.total_rechazadas = 0
    
    def iniciar(self):
        """Inicia el Bus (worker threads, etc.)"""
        if self.iniciado:
            return
        
        self.writer.iniciar()
        self.iniciado = True
        print("✅ Bus V3 Mejorado iniciado")
    
    def detener(self):
        """Detiene el Bus limpiamente"""
        if not self.iniciado:
            return
        
        self.writer.detener()
        self.iniciado = False
        print("✅ Bus V3 Mejorado detenido")
    
    # ═══════════════════════════════════════════════════════════════
    # API DE PUBLICACIÓN (con ADN + Delta)
    # ═══════════════════════════════════════════════════════════════
    
    def registrar_variable(self, adn: str, 
                          umbral_delta: float = 0.1,
                          intervalo_minimo_segundos: int = 60):
        """
        Registra nueva variable con configuración de Delta
        
        Args:
            adn: "Sensores.Ecowitt.Temperatura.Raw"
            umbral_delta: Publica si Δ > este valor
            intervalo_minimo_segundos: Publica al menos cada N segundos
        """
        # Registrar en buffer circular
        dato = self.buffer_circular.registrar(adn, ventana=100)
        
        # Configurar delta publishing
        self.umbrales_delta[adn] = umbral_delta
        self.umbrales_delta[f"{adn}:intervalo"] = intervalo_minimo_segundos
    
    def publicar(self, adn: str, valor: float, 
                 forzar: bool = False) -> bool:
        """
        Publica variable (con inteligencia Delta)
        
        Args:
            adn: ADN completo
            valor: Nuevo valor
            forzar: Publicar sin verificar Delta
        
        Returns:
            True si se publicó, False si se filtró por Delta
        """
        if not self.iniciado:
            return False
        
        # 1. Actualizar en buffer circular
        if adn not in self.buffer_circular.variables:
            self.registrar_variable(adn)
        
        dato = self.buffer_circular.variables[adn]
        dato.actualizar(valor)
        
        # 2. Verificar Delta Publishing
        if not forzar:
            if not dato.deberia_publicarse(
                umbral_delta=self.umbrales_delta.get(adn, 0.1),
                intervalo_minimo_segundos=self.umbrales_delta.get(f"{adn}:intervalo", 60)
            ):
                # Filtrado por Delta
                return False
        
        # 3. Marcar como publicado
        dato.marcar_como_publicado()
        
        # 4. Escribir en Bus async
        exito = self.writer_con_reintentos.publicar_con_reintentos(adn, valor)
        
        if exito:
            self.total_publicaciones += 1
        else:
            self.total_rechazadas += 1
        
        # 5. Registrar en indexer
        self.indexer.registrar_variable(adn, valor)
        
        return exito
    
    # ═══════════════════════════════════════════════════════════════
    # API DE LECTURA (búsquedas rápidas)
    # ═══════════════════════════════════════════════════════════════
    
    def obtener(self, adn: str):
        """Acceso O(1) a variable"""
        return self.indexer.obtener(adn)
    
    def obtener_familia(self, prefijo: str):
        """Acceso O(k) a familia de variables"""
        return self.indexer.obtener_familia(prefijo)
    
    def buscar(self, patron: str):
        """Búsqueda con wildcard"""
        return self.indexer.buscar(patron)
    
    # ═══════════════════════════════════════════════════════════════
    # API PARA IA (histórico completo)
    # ═══════════════════════════════════════════════════════════════
    
    def obtener_serie_para_lstm(self, adn: str, ultimas_n: int = 60):
        """Obtiene serie histórica para LSTM"""
        if adn in self.buffer_circular.variables:
            return self.buffer_circular.variables[adn].obtener_serie(ultimas_n)
        return []
    
    def obtener_todas_series_para_lstm(self, ultimas_n: int = 60):
        """Obtiene histórico de TODAS las variables"""
        return self.buffer_circular.obtener_serie_todas(ultimas_n)
    
    # ═══════════════════════════════════════════════════════════════
    # API PARA DASHBOARD/API (snapshot dinámico)
    # ═══════════════════════════════════════════════════════════════
    
    def generar_snapshot(self):
        """Genera snapshot dinámico (sin decisión humana)"""
        # Obtener estadísticas de buffer circular
        datos_historicos = {
            adn: {
                'varianza': dato.varianza_historica,
                'media': dato.media_historica
            }
            for adn, dato in self.buffer_circular.variables.items()
        }
        
        # Obtener snapshot
        bus_raw = self.writer.obtener_todas_variables()
        return self.snapshot.generar_snapshot(bus_raw, datos_historicos)
    
    def obtener_snapshot_formateado(self):
        """Snapshot para API/Dashboard (nombres simplificados)"""
        return self.snapshot.obtener_snapshot_formateado()
    
    def obtener_snapshot_completo_para_ia(self):
        """Snapshot completo para IA (sin filtro)"""
        return self.writer.obtener_todas_variables()
    
    # ═══════════════════════════════════════════════════════════════
    # MONITOREO Y ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════
    
    def obtener_estadisticas_completas(self) -> dict:
        """Estadísticas de todo el Bus"""
        stats_writer = self.writer.obtener_estadisticas()
        stats_indexer = self.indexer.obtener_estadisticas()
        stats_snapshot = self.snapshot.obtener_estadisticas()
        
        return {
            'estado': 'iniciado' if self.iniciado else 'parado',
            'publicaciones': {
                'exitosas': self.total_publicaciones,
                'rechazadas': self.total_rechazadas,
                'eficiencia': (self.total_publicaciones / 
                              (self.total_publicaciones + self.total_rechazadas)
                              if (self.total_publicaciones + self.total_rechazadas) > 0
                              else 0)
            },
            'writer': stats_writer,
            'indexer': stats_indexer,
            'snapshot': stats_snapshot,
            'buffer_circular': {
                'variables_con_historico': len(self.buffer_circular.variables),
                'umbrales_configurados': len(self.umbrales_delta) // 2  # Cada variable ocupa 2 entries
            }
        }


# ═══════════════════════════════════════════════════════════════
# EJEMPLO DE USO COMPLETO
# ═══════════════════════════════════════════════════════════════

def ejemplo_uso_completo():
    """Demuestra el Bus V3 Mejorado en funcionamiento"""
    
    print("\n" + "═" * 70)
    print("  EJEMPLO: Bus V3 Mejorado - Datos Masivos sin Caos")
    print("═" * 70 + "\n")
    
    # 1. Crear Bus
    bus = BusV3Mejorado(tamaño_cola_escritura=10000)
    bus.iniciar()
    
    # 2. Configurar variables con Delta Publishing
    bus.registrar_variable("Sensores.Ecowitt.Temperatura", umbral_delta=0.1, intervalo_minimo_segundos=60)
    bus.registrar_variable("Sensores.Ecowitt.Humedad", umbral_delta=1.0, intervalo_minimo_segundos=60)
    bus.registrar_variable("Prediccion.LSTM.UTCI", umbral_delta=0.05, intervalo_minimo_segundos=30)
    bus.registrar_variable("Calibracion.Temperatura.Bias", umbral_delta=0.2)
    
    # 3. Publicar datos (simulación)
    print("📝 Simulando 1000 publicaciones...")
    
    for i in range(1000):
        # Temperatura sube lentamente
        temp = 20.0 + (i * 0.01)
        bus.publicar("Sensores.Ecowitt.Temperatura", temp)
        
        # Humedad cambia cada 50 ciclos
        if i % 50 == 0:
            humedad = 50 + (i * 0.01)
            bus.publicar("Sensores.Ecowitt.Humedad", humedad)
        
        # Predicción
        prediccion = 21.5 + (i * 0.015)
        bus.publicar("Prediccion.LSTM.UTCI", prediccion, forzar=True)
    
    print("✅ 1000 actualizaciones procesadas\n")
    
    # 4. Búsquedas rápidas
    print("🔍 Búsquedas (indexación):")
    
    # Familia
    ecowitt = bus.obtener_familia("Sensores.Ecowitt")
    print(f"   Sensores.Ecowitt.* → {len(ecowitt)} variables")
    
    # Wildcard
    todas_predicciones = bus.buscar("Prediccion.*")
    print(f"   Prediccion.* → {len(todas_predicciones)} variables\n")
    
    # 5. Histórico para IA
    print("🤖 Histórico para IA (LSTM):")
    serie_temp = bus.obtener_serie_para_lstm("Sensores.Ecowitt.Temperatura", ultimas_n=10)
    print(f"   Últimas 10 muestras temperatura: {[round(x, 2) for x in serie_temp[-10:]]}\n")
    
    # 6. Snapshot dinámico
    print("📊 Snapshot Dinámico (sin sesgo humano):")
    snap = bus.generar_snapshot()
    print(f"   Variables incluidas: {len(snap)} (de {bus.indexer.total_variables} totales)")
    print(f"   Criterio: Solo varianza > umbral\n")
    
    # 7. Estadísticas completas
    print("📈 Estadísticas Completas:")
    stats = bus.obtener_estadisticas_completas()
    
    print(f"   Publicaciones exitosas: {stats['publicaciones']['exitosas']}")
    print(f"   Publicaciones rechazadas (Delta): {stats['publicaciones']['rechazadas']}")
    print(f"   Eficiencia: {stats['publicaciones']['eficiencia']*100:.1f}%")
    print(f"   Total variables en Bus: {stats['indexer']['total_variables']}")
    print(f"   Tipos de variables: {list(stats['indexer']['tipos'].keys())}")
    print(f"   Variables en snapshot: {stats['snapshot']['variables_en_snapshot']}\n")
    
    # 8. API para Dashboard
    print("🌐 Datos para API/Dashboard (snapshot formateado):")
    api_data = bus.obtener_snapshot_formateado()
    for clave, valor in list(api_data.items())[:5]:
        print(f"   {clave}: {round(valor, 2) if isinstance(valor, float) else valor}")
    print(f"   ... ({len(api_data)} variables más)\n")
    
    # 9. Detener
    bus.detener()
    
    print("✅ Ejemplo completado\n")


if __name__ == "__main__":
    ejemplo_uso_completo()

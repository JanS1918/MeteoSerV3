"""
MONITOR DE BUS EN TIEMPO REAL
==============================
Dashboard interactivo que muestra MB/s y flujo de datos del Bus.
Se actualiza en consola cada N segundos.
"""

import sys
import time
import threading
from datetime import datetime
from collections import deque
from typing import Optional

from core.bus.bus_capas_informacion import obtener_bus


class MonitorBusRealtime:
    """Monitor en tiempo real del flujo de datos por el Bus"""
    
    def __init__(self, intervalo_actualizacion: float = 5.0):
        """
        Args:
            intervalo_actualizacion: Segundos entre refreshes (default 5s)
        """
        self.bus = obtener_bus()
        self.intervalo = intervalo_actualizacion
        self.corriendo = False
        self.hilo = None
        self.historial_throughput = deque(maxlen=60)  # Últimos 60 samplings
        self.lock = threading.RLock()
    
    def iniciar(self):
        """Inicia el monitor en thread separado"""
        if self.corriendo:
            return
        
        self.corriendo = True
        self.hilo = threading.Thread(target=self._loop_monitor, daemon=True)
        self.hilo.start()
        print("📊 Monitor del Bus iniciado (Ctrl+C para salir)")
    
    def detener(self):
        """Detiene el monitor"""
        self.corriendo = False
        if self.hilo:
            self.hilo.join(timeout=2)
    
    def _loop_monitor(self):
        """Loop principal de monitoreo"""
        while self.corriendo:
            try:
                self._mostrar_dashboard()
                time.sleep(self.intervalo)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error en monitor: {e}")
    
    def _mostrar_dashboard(self):
        """Renderiza dashboard en consola"""
        self._limpiar_pantalla()
        
        dashboard = self.bus.obtener_dashboard()
        
        # Encabezado
        print("=" * 80)
        print(f"  🛰️  BUS DE CAPAS DE INFORMACIÓN - {dashboard['timestamp']}")
        print("=" * 80)
        
        # Modo debug
        debug_str = "🔴 ACTIVADO" if dashboard['debug_mode'] else "⚫ Desactivado"
        print(f"\n  DEBUG MODE: {debug_str}")
        
        # Throughput
        throughput = dashboard['throughput_bytes_seg']
        if throughput > 0:
            mb_seg = throughput / (1024 * 1024)
            print(f"  📈 Throughput: {mb_seg:.6f} MB/s ({throughput:.0f} bytes/s)")
        
        # Capas
        print("\n  📦 CONTENIDO POR CAPAS:")
        print("  " + "-" * 76)
        
        capas = dashboard['capas']
        
        # CORE
        core_data = capas['CORE']
        self._mostrar_capa_simple(
            "CORE",
            core_data['items'],
            "Datos validados (confianza > 0.95)"
        )
        
        # INTERMEDIATE
        inter_data = capas['INTERMEDIATE']
        self._mostrar_capa_simple(
            "INTERMEDIATE",
            inter_data['items'],
            "Cálculos pre-índices"
        )
        
        # DEBUG
        debug_data = capas['DEBUG']
        self._mostrar_capa_simple(
            "DEBUG",
            debug_data['items'],
            "Variables temporales (si DEBUG=ON)"
        )
        
        # TIMESERIES
        ts_data = capas['TIMESERIES']
        print(f"\n  ⏱️  TIMESERIES (Históricos)")
        print(f"      Variables con histórico: {ts_data['variables']}")
        
        if ts_data['principales']:
            print(f"\n      Principales (últimas 10):")
            for ts_stat in ts_data['principales']:
                if ts_stat.get('muestras', 0) > 0:
                    var = ts_stat.get('variable', '?')
                    muestras = ts_stat.get('muestras', 0)
                    print(f"        • {var}: {muestras} muestras", end="")
                    
                    if 'promedio' in ts_stat:
                        print(f" (promedio: {ts_stat['promedio']:.2f})", end="")
                    print()
        
        # Últimas queries
        print("\n  🔍 ÚLTIMAS QUERIES:")
        print("  " + "-" * 76)
        
        if dashboard['ultimas_queries']:
            for query in dashboard['ultimas_queries'][-5:]:
                print(f"      {query['filtro']:<40} → {query['resultados']} resultados")
        else:
            print("      (sin queries registradas)")
        
        # Estadísticas globales
        print("\n  📊 ESTADÍSTICAS GLOBALES:")
        print("  " + "-" * 76)
        
        total_core = core_data['inserciones'] + core_data['actualizaciones']
        total_inter = inter_data['inserciones'] + inter_data['actualizaciones']
        total_debug = debug_data['inserciones'] + debug_data['actualizaciones']
        
        print(f"      CORE:           {core_data['inserciones']} inserciones, "
              f"{core_data['actualizaciones']} actualizaciones")
        print(f"      INTERMEDIATE:   {inter_data['inserciones']} inserciones, "
              f"{inter_data['actualizaciones']} actualizaciones")
        print(f"      DEBUG:          {debug_data['inserciones']} inserciones, "
              f"{debug_data['actualizaciones']} actualizaciones")
        
        print("\n" + "=" * 80)
    
    def _mostrar_capa_simple(self, nombre: str, items: int, desc: str):
        """Muestra una capa en formato simplificado"""
        barra = "█" * min(items // 5, 30)
        print(f"\n  {nombre:<12} [{items:4d} vars] {barra}")
        print(f"  {' '*12} {desc}")
    
    def _limpiar_pantalla(self):
        """Limpia consola (cross-platform)"""
        try:
            if sys.platform == 'win32':
                import os
                os.system('cls')
            else:
                import os
                os.system('clear')
        except:
            # Si falla, al menos imprime saltos de línea
            print("\n" * 100)
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas sin mostrar"""
        with self.lock:
            dashboard = self.bus.obtener_dashboard()
            return {
                "timestamp": dashboard['timestamp'],
                "debug_mode": dashboard['debug_mode'],
                "throughput_bytes_seg": dashboard['throughput_bytes_seg'],
                "total_core": (
                    dashboard['capas']['CORE']['inserciones'] +
                    dashboard['capas']['CORE']['actualizaciones']
                ),
                "total_intermediate": (
                    dashboard['capas']['INTERMEDIATE']['inserciones'] +
                    dashboard['capas']['INTERMEDIATE']['actualizaciones']
                ),
                "total_debug": (
                    dashboard['capas']['DEBUG']['inserciones'] +
                    dashboard['capas']['DEBUG']['actualizaciones']
                ),
                "variables_timeseries": dashboard['capas']['TIMESERIES']['variables']
            }


def mostrar_monitor_una_vez(verbose: bool = True) -> dict:
    """
    Muestra el estado del Bus una sola vez (sin loop)
    Útil para scripts o debugging
    """
    bus = obtener_bus()
    dashboard = bus.obtener_dashboard()
    
    if verbose:
        print("\n🛰️  ESTADO ACTUAL DEL BUS:")
        print("=" * 60)
        
        print(f"\nTiempo: {dashboard['timestamp']}")
        print(f"Debug:  {'ACTIVADO 🔴' if dashboard['debug_mode'] else 'Desactivado'}")
        print(f"Throughput: {dashboard['throughput_bytes_seg']:.2f} bytes/seg")
        
        print("\n📦 Variables por capa:")
        print(f"  CORE:         {dashboard['capas']['CORE']['items']} variables")
        print(f"  INTERMEDIATE: {dashboard['capas']['INTERMEDIATE']['items']} variables")
        print(f"  DEBUG:        {dashboard['capas']['DEBUG']['items']} variables")
        print(f"  TIMESERIES:   {dashboard['capas']['TIMESERIES']['variables']} históricos")
        
        print("\n" + "=" * 60)
    
    return dashboard


# Uso: python -c "from core.bus.monitor_bus import MonitorBusRealtime; m = MonitorBusRealtime(); m.iniciar()"
if __name__ == "__main__":
    monitor = MonitorBusRealtime(intervalo_actualizacion=3.0)
    monitor.iniciar()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Monitor cerrado")
        monitor.detener()

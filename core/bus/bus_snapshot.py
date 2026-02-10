"""
BUS SNAPSHOT DINÁMICO - Resumen Automático sin Sesgo
====================================================
Genera vista de resumen del Bus automáticamente basada en varianza.

Arquitectura:
- Snapshot: 50-100 variables "maestras" (sin decisión humana)
- Criterio: Solo variables con varianza > umbral (son relevantes)
- Actualización: Cada N segundos, automático

Beneficio:
- Dashboard limpio (50 variables)
- IA accede completo (10.000 variables)
- Sin filtro arbitrario (decisión matemática)
"""

from typing import Dict, List, Optional, Any
import time


class BusSnapshotDinamico:
    """
    Generador de snapshots dinámicos basado en varianza
    
    Automáticamente selecciona las variables "maestras"
    sin intervención humana.
    """
    
    def __init__(self, tamaño_maximo_snapshot: int = 100,
                 umbral_varianza_minimo: float = 0.01):
        """
        Args:
            tamaño_maximo_snapshot: Máximo de variables en snapshot
            umbral_varianza_minimo: Varianza mínima para incluir variable
        """
        self.tamaño_maximo = tamaño_maximo_snapshot
        self.umbral_varianza = umbral_varianza_minimo
        
        self.snapshot_actual: Dict[str, Any] = {}
        self.variables_maestras: List[str] = []
        
        self.ultima_actualizacion = time.time()
        self.intervalo_actualizacion = 5  # Actualizar cada 5s
        
        # Estadísticas
        self.variables_candidatas_totales = 0
        self.variables_incluidas = 0
        self.variables_excluidas = 0
    
    def generar_snapshot(self, bus_raw: Dict[str, Any], 
                        datos_historicos: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera snapshot automáticamente
        
        Args:
            bus_raw: Bus completo con todas las variables
            datos_historicos: Variables con histórico (varianza disponible)
        
        Returns:
            Snapshot filtrado (solo variables relevantes)
        """
        self.variables_candidatas_totales = len(bus_raw)
        
        # Si no hay histórico, usar criterio alternativo (nombre)
        if datos_historicos is None:
            return self._generar_por_nombre(bus_raw)
        
        # Criterio principal: Varianza
        candidatos = []
        
        for adn, dato_historico in datos_historicos.items():
            # Obtener varianza
            varianza = dato_historico.get('varianza', 0.0)
            
            # Si varianza > umbral, es "interesante"
            if varianza > self.umbral_varianza:
                candidatos.append((adn, varianza))
                self.variables_incluidas += 1
            else:
                self.variables_excluidas += 1
        
        # Ordenar por varianza (descendente) y tomar top N
        candidatos.sort(key=lambda x: x[1], reverse=True)
        self.variables_maestras = [adn for adn, _ in candidatos[:self.tamaño_maximo]]
        
        # Construir snapshot
        self.snapshot_actual = {
            adn: bus_raw.get(adn) 
            for adn in self.variables_maestras 
            if adn in bus_raw
        }
        
        self.ultima_actualizacion = time.time()
        return self.snapshot_actual
    
    def _generar_por_nombre(self, bus_raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera snapshot por heurística de nombres
        
        Prioriza:
        1. Variables sin "debug", "internal", etc.
        2. Variables cortas (nombres naturales)
        3. Variables de tipos comunes (temperatura, humedad, etc.)
        """
        PALABRAS_EXCLUIDAS = ['debug', 'internal', 'test', '_tmp', 'cache']
        PALABRAS_PRIORITARIAS = ['temperatura', 'humedad', 'presion', 
                                 'viento', 'lluvia', 'utci', 'error']
        
        candidatos = []
        
        for adn, valor in bus_raw.items():
            # Excluir si tiene palabras prohibidas
            if any(exc.lower() in adn.lower() for exc in PALABRAS_EXCLUIDAS):
                self.variables_excluidas += 1
                continue
            
            # Puntuación: Si tiene palabra prioritaria, suma puntos
            puntuacion = 0
            for palabra in PALABRAS_PRIORITARIAS:
                if palabra.lower() in adn.lower():
                    puntuacion += 100
            
            # Penalizar variables profundas (muchos puntos)
            puntuacion -= len(adn.split('.')) * 2
            
            candidatos.append((adn, puntuacion))
            self.variables_incluidas += 1
        
        # Ordenar y tomar top N
        candidatos.sort(key=lambda x: x[1], reverse=True)
        self.variables_maestras = [adn for adn, _ in candidatos[:self.tamaño_maximo]]
        
        # Construir snapshot
        self.snapshot_actual = {
            adn: bus_raw.get(adn) 
            for adn in self.variables_maestras 
            if adn in bus_raw
        }
        
        return self.snapshot_actual
    
    def obtener_snapshot(self) -> Dict[str, Any]:
        """Retorna snapshot actual sin regenerar"""
        return dict(self.snapshot_actual)
    
    def obtener_snapshot_formateado(self) -> Dict[str, Any]:
        """
        Retorna snapshot con formato para API/Dashboard
        
        {
            "temperatura": 23.5,
            "humedad": 65,
            "prediccion.utci": 24.2,
            ...
        }
        """
        formateado = {}
        
        for adn, valor in self.snapshot_actual.items():
            # Simplificar nombre si es posible
            partes = adn.split('.')
            
            # Si tiene 3+ partes, usar solo últimas 2
            if len(partes) >= 3:
                clave = '.'.join(partes[-2:])
            else:
                clave = adn
            
            formateado[clave] = valor
        
        return formateado
    
    def es_en_snapshot(self, adn: str) -> bool:
        """Verifica si variable está en snapshot"""
        return adn in self.variables_maestras
    
    def agregar_forzado(self, adn: str):
        """Fuerza inclusión de variable (ej: variables críticas)"""
        if adn not in self.variables_maestras:
            self.variables_maestras.append(adn)
            
            # Si se pasa tamaño, remover la menos importante
            if len(self.variables_maestras) > self.tamaño_maximo:
                self.variables_maestras = self.variables_maestras[:self.tamaño_maximo]
    
    def remover_forzado(self, adn: str):
        """Remueve variable del snapshot"""
        if adn in self.variables_maestras:
            self.variables_maestras.remove(adn)
    
    def obtener_estadisticas(self) -> Dict:
        """Estadísticas de generación"""
        return {
            'variables_en_snapshot': len(self.snapshot_actual),
            'variables_candidatas': self.variables_candidatas_totales,
            'variables_incluidas': self.variables_incluidas,
            'variables_excluidas': self.variables_excluidas,
            'ultima_actualizacion': self.ultima_actualizacion,
            'porcentaje_inclusion': (
                (self.variables_incluidas / self.variables_candidatas_totales * 100)
                if self.variables_candidatas_totales > 0 else 0
            )
        }


class SnapshotBuilder:
    """
    Builder para construir snapshots personalizados
    """
    
    def __init__(self):
        self.variables_requeridas: List[str] = []
        self.variables_excluidas: List[str] = []
        self.prefijos_permitidos: List[str] = []
    
    def requerir(self, adn: str) -> 'SnapshotBuilder':
        """Requiere variable en snapshot"""
        self.variables_requeridas.append(adn)
        return self
    
    def excluir(self, adn: str) -> 'SnapshotBuilder':
        """Excluye variable de snapshot"""
        self.variables_excluidas.append(adn)
        return self
    
    def solo_prefijos(self, *prefijos) -> 'SnapshotBuilder':
        """Solo incluir variables con estos prefijos"""
        self.prefijos_permitidos.extend(prefijos)
        return self
    
    def construir(self, bus_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Construye snapshot según criterios"""
        resultado = {}
        
        for adn, valor in bus_raw.items():
            # Excluidas
            if adn in self.variables_excluidas:
                continue
            
            # Prefijos
            if self.prefijos_permitidos:
                if not any(adn.startswith(p) for p in self.prefijos_permitidos):
                    continue
            
            resultado[adn] = valor
        
        # Agregar requeridas
        for adn in self.variables_requeridas:
            if adn in bus_raw:
                resultado[adn] = bus_raw[adn]
        
        return resultado


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║      BUS SNAPSHOT - Resumen Dinámico sin Sesgo              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        snapshot = BusSnapshotDinamico(tamaño_maximo=100)
        
        # Generar automáticamente basado en varianza
        snap = snapshot.generar_snapshot(bus_raw, datos_historicos)
        
        # Resultado: Solo variables con varianza > umbral
        # 10.000 variables → 50-100 en snapshot
        
        # Dashboard obtiene snapshot simple
        api_data = snapshot.obtener_snapshot_formateado()
        
        # IA obtiene bus_raw completo
        
        # Variables críticas siempre incluidas
        snapshot.agregar_forzado("Sensores.Temperatura")
        
        # Stats
        print(snapshot.obtener_estadisticas())
    """)

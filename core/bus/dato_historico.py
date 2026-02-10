"""
DATO CON HISTÓRICO - Buffer Circular para Series Temporales
===========================================================
Variable con histórico integrado para LSTM y análisis temporal.

Arquitectura:
- Deque circular: O(1) inserción/eliminación
- Timestamp automático: Registro temporal preciso
- Delta tracking: Detecta cambios significativos
- Varianza calculada: Para snapshot dinámico

Beneficio:
- IA accede a últimas N muestras sin queries adicionales
- Sincronización perfecta (datos + histórico en una estructura)
"""

from collections import deque
import time
from typing import List, Optional, Any
import statistics

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round


class DatoConHistorico:
    """
    Variable del Bus con histórico integrado
    
    Mantiene:
    - Valor actual
    - Últimas N muestras (para LSTM)
    - Timestamps precisos
    - Estadísticas (media, varianza, delta)
    """
    
    def __init__(self, ventana_historico: int = 100, 
                 nombre: str = None,
                 adn: str = None):
        """
        Args:
            ventana_historico: Número de muestras a mantener
            nombre: Nombre legible
            adn: ADN completo (ej: "Sensores.Ecowitt.Temperatura")
        """
        self.valor_actual: Optional[float] = None
        self.historico: deque = deque(maxlen=ventana_historico)
        self.historico_timestamps: deque = deque(maxlen=ventana_historico)
        self.ventana_historico = ventana_historico
        
        self.nombre = nombre
        self.adn = adn
        
        # Delta (para publicación inteligente)
        self.ultimo_valor_publicado: Optional[float] = None
        self.ultimo_timestamp_publicado: float = time.time()
        
        # Estadísticas
        self.ultima_actualizacion = time.time()
        self.num_actualizaciones = 0
        self.varianza_historica = 0.0
        self.media_historica = 0.0
    
    def actualizar(self, nuevo_valor: Any) -> bool:
        """
        Actualiza el valor y mantiene histórico
        
        Args:
            nuevo_valor: Nuevo valor de la variable
        
        Returns:
            True si se actualizó, False si None/inválido
        """
        if nuevo_valor is None:
            return False
        
        # Convertir a float si es posible
        try:
            nuevo_valor = float(nuevo_valor)
        except (ValueError, TypeError):
            return False
        
        # Si es la primera actualización
        if self.valor_actual is None:
            self.valor_actual = nuevo_valor
            self.historico.append(nuevo_valor)
            self.historico_timestamps.append(time.time())
            self.ultimo_valor_publicado = nuevo_valor
            self.num_actualizaciones = 1
            self._recalcular_estadisticas()
            return True
        
        # Agregar histórico
        self.historico.append(self.valor_actual)
        self.historico_timestamps.append(self.ultima_actualizacion)
        
        # Actualizar valor
        self.valor_actual = nuevo_valor
        self.ultima_actualizacion = time.time()
        self.num_actualizaciones += 1
        
        # Recalcular estadísticas
        self._recalcular_estadisticas()
        
        return True
    
    def _recalcular_estadisticas(self):
        """Recalcula media y varianza del histórico"""
        if len(self.historico) < 2:
            self.media_historica = float(self.valor_actual) if self.valor_actual else 0
            self.varianza_historica = 0.0
            return
        
        try:
            self.media_historica = statistics.mean(self.historico)
            self.varianza_historica = statistics.variance(self.historico)
        except:
            self.varianza_historica = 0.0
    
    def obtener_serie(self, ultimas_n: int = None) -> List[float]:
        """
        Obtiene últimas N muestras del histórico
        
        Args:
            ultimas_n: Número de muestras (o None para todas)
        
        Returns:
            Lista de valores [más antiguo, ..., más nuevo]
        """
        historico_list = list(self.historico)
        
        if ultimas_n is None or ultimas_n >= len(historico_list):
            return historico_list
        
        return historico_list[-ultimas_n:]
    
    def obtener_serie_con_timestamps(self, ultimas_n: int = None) -> List[tuple]:
        """
        Obtiene serie completa con timestamps
        
        Returns:
            Lista de (timestamp, valor) tuples
        """
        historico_list = list(self.historico)
        timestamps_list = list(self.historico_timestamps)
        
        if ultimas_n:
            historico_list = historico_list[-ultimas_n:]
            timestamps_list = timestamps_list[-ultimas_n:]
        
        return list(zip(timestamps_list, historico_list))
    
    def calcular_delta(self) -> float:
        """Retorna cambio desde último valor publicado"""
        if self.ultimo_valor_publicado is None:
            return 0.0
        
        return abs(self.valor_actual - self.ultimo_valor_publicado)
    
    def calcular_velocidad_cambio(self) -> float:
        """
        Velocidad de cambio (unidades/segundo)
        
        Basado en últimas 2 muestras
        """
        if len(self.historico) < 1:
            return 0.0
        
        valor_anterior = self.historico[-1] if self.historico else self.valor_actual
        tiempo_transcurrido = self.ultima_actualizacion - self.historico_timestamps[-1]
        
        if tiempo_transcurrido <= 0:
            return 0.0
        
        delta = self.valor_actual - valor_anterior
        return delta / tiempo_transcurrido
    
    def deberia_publicarse(self, umbral_delta: float = 0.1, 
                          intervalo_minimo_segundos: float = 60) -> bool:
        """
        Determina si variable debe publicarse (Delta + Pulso mínimo)
        
        Args:
            umbral_delta: Cambio mínimo para publicar
            intervalo_minimo_segundos: Publica al menos cada N segundos
        
        Returns:
            True si debe publicarse
        """
        # Primera publicación: siempre publicar
        if self.num_actualizaciones <= 1:
            return True
        # Pulso mínimo (publica aunque no cambie)
        tiempo_desde_pub = time.time() - self.ultimo_timestamp_publicado
        if tiempo_desde_pub > intervalo_minimo_segundos:
            return True
        
        # Delta significativo
        if self.calcular_delta() > umbral_delta:
            return True
        
        return False
    
    def marcar_como_publicado(self):
        """Marca que variable fue publicada"""
        self.ultimo_valor_publicado = self.valor_actual
        self.ultimo_timestamp_publicado = time.time()
    
    def obtener_resumen(self) -> dict:
        """Resumen para debug/monitoring"""
        return {
            'adn': self.adn,
            'nombre': self.nombre,
            'valor_actual': self.valor_actual,
            'media': round(self.media_historica, 4),
            'varianza': round(self.varianza_historica, 4),
            'muestras': len(self.historico),
            'delta_desde_pub': round(self.calcular_delta(), 4),
            'velocidad_cambio': round(self.calcular_velocidad_cambio(), 6),
            'actualizaciones': self.num_actualizaciones
        }
    
    def limpiar_historico(self):
        """Limpia histórico (reinicia buffer)"""
        self.historico.clear()
        self.historico_timestamps.clear()


class BufferCircular:
    """
    Wrapper para facilitar operaciones en lote
    """
    
    def __init__(self):
        self.variables: dict = {}
    
    def registrar(self, adn: str, ventana: int = 100) -> DatoConHistorico:
        """Registra nueva variable"""
        dato = DatoConHistorico(ventana_historico=ventana, adn=adn)
        self.variables[adn] = dato
        return dato
    
    def actualizar_todas(self, actualizaciones: dict) -> int:
        """
        Actualiza múltiples variables
        
        Args:
            actualizaciones: {"adn": valor, ...}
        
        Returns:
            Número de actualizaciones exitosas
        """
        exitos = 0
        for adn, valor in actualizaciones.items():
            if adn in self.variables:
                if self.variables[adn].actualizar(valor):
                    exitos += 1
        
        return exitos
    
    def obtener_serie_todas(self, ultimas_n: int = 60) -> dict:
        """Obtiene series de TODAS las variables"""
        return {adn: dato.obtener_serie(ultimas_n) 
                for adn, dato in self.variables.items()}
    
    def obtener_variables_para_publicar(self, umbrales: dict) -> List[str]:
        """Obtiene variables que deben publicarse según Delta"""
        a_publicar = []
        
        for adn, dato in self.variables.items():
            umbral = umbrales.get(adn, 0.1)
            intervalo = umbrales.get(f"{adn}:intervalo", 60)
            
            if dato.deberia_publicarse(umbral, intervalo):
                a_publicar.append(adn)
        
        return a_publicar


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║      DATO CON HISTÓRICO - Series Temporales Integradas      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        dato = DatoConHistorico(ventana_historico=100, 
                                adn="Sensores.Ecowitt.Temperatura")
        
        # Actualizar múltiples veces
        for t in [20.0, 20.1, 20.3, 20.7, 21.2]:
            dato.actualizar(t)
        
        # Obtener serie (para LSTM)
        serie = dato.obtener_serie(ultimas_n=60)
        # [20.0, 20.1, 20.3, 20.7, 21.2]
        
        # Decidir si publicar
        if dato.deberia_publicarse(umbral_delta=0.1, intervalo_minimo=60):
            print("Publicar en Bus")
            dato.marcar_como_publicado()
        
        # Estadísticas
        print(dato.obtener_resumen())
    """)

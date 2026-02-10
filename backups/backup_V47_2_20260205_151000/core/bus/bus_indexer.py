"""
BUS INDEXER - Búsqueda Inteligente por ADN (O(k) en lugar de O(n))
==================================================================
Sistema de indexación mediante Trie + flat_map para acceso rápido a variables.

Arquitectura:
- Trie: Estructura jerárquica para navegación por prefijo
- Flat Map: Acceso O(1) a variable específica
- Índice Invertido: Búsquedas por familia

Ejemplo:
    Sensores.Ecowitt.Temperatura → acceso O(1)
    Sensores.Ecowitt.*  → búsqueda O(k) donde k=número Ecowitt
"""

from typing import Dict, List, Optional, Any
import fnmatch
from collections import defaultdict


class NodoTrie:
    """Nodo del Trie para estructura jerárquica"""
    
    def __init__(self):
        self.hijos: Dict[str, 'NodoTrie'] = {}
        self.es_hoja = False
        self.referencia_plana: Optional[str] = None


class BusIndexer:
    """
    Indexador inteligente de variables con ADN (Linaje Automático Dinámico)
    
    Mantiene:
    1. Trie jerárquico para navegación
    2. Flat map para acceso O(1)
    3. Índices invertidos para búsquedas complejas
    """
    
    def __init__(self):
        self.raiz_trie = NodoTrie()
        self.flat_map: Dict[str, Any] = {}  # "Sensores.Ecowitt.Temp" → {...}
        
        # Índices invertidos (para búsquedas rápidas)
        self.indice_por_familia: Dict[str, List[str]] = defaultdict(list)
        self.indice_por_tipo: Dict[str, List[str]] = defaultdict(list)
        
        # Estadísticas
        self.total_variables = 0
        self.cache_busquedas = {}
    
    def registrar_variable(self, adn: str, dato: Any):
        """
        Registra variable con su ADN completo
        
        Args:
            adn: "Sensores.Ecowitt.Temperatura.Raw" (con puntos)
            dato: Objeto o valor a almacenar
        """
        # Agregar a flat_map
        self.flat_map[adn] = dato
        
        # Agregar a Trie
        partes = adn.split('.')
        nodo = self.raiz_trie
        
        for parte in partes:
            if parte not in nodo.hijos:
                nodo.hijos[parte] = NodoTrie()
            nodo = nodo.hijos[parte]
        
        nodo.es_hoja = True
        nodo.referencia_plana = adn
        
        # Índices invertidos
        if len(partes) >= 2:
            familia = '.'.join(partes[:-1])  # "Sensores.Ecowitt"
            self.indice_por_familia[familia].append(adn)
        
        if len(partes) >= 1:
            tipo = partes[0]  # "Sensores"
            self.indice_por_tipo[tipo].append(adn)
        
        self.total_variables = len(self.flat_map)
        self.cache_busquedas.clear()  # Invalidar cache
    
    def obtener(self, adn: str) -> Optional[Any]:
        """Acceso O(1) a variable específica"""
        return self.flat_map.get(adn)
    
    def obtener_familia(self, prefijo: str) -> List[str]:
        """
        Obtiene todas las variables de una familia
        
        Args:
            prefijo: "Sensores.Ecowitt" (sin wildcard)
        
        Returns:
            Lista de ADNs que empiezan con prefijo (O(k))
        """
        return self.indice_por_familia.get(prefijo, [])
    
    def buscar(self, patron: str) -> List[str]:
        """
        Búsqueda por patrón con wildcard
        
        Args:
            patron: "Sensores.Ecowitt.*" o "*.Temperatura"
        
        Returns:
            Lista de ADNs que coinciden (cached)
        """
        # Verificar cache
        if patron in self.cache_busquedas:
            return self.cache_busquedas[patron]
        
        # Si es búsqueda simple (sin wildcards internos)
        if patron.endswith('.*'):
            prefijo = patron[:-2]
            resultados = self.indice_por_familia.get(prefijo, [])
        else:
            # Búsqueda con wildcard complejo
            resultados = [adn for adn in self.flat_map.keys() 
                         if fnmatch.fnmatch(adn, patron)]
        
        # Cachear resultado
        self.cache_busquedas[patron] = resultados
        return resultados
    
    def obtener_rama_completa(self, prefijo: str, incluir_valores=False) -> Dict:
        """
        Obtiene rama completa del Trie
        
        Args:
            prefijo: "Sensores" → retorna Sensores.*
            incluir_valores: Si True, incluye valores además de keys
        
        Returns:
            Estructura jerárquica
        """
        partes = prefijo.split('.')
        nodo = self.raiz_trie
        
        # Navegar hasta el nodo
        for parte in partes:
            if parte not in nodo.hijos:
                return {}
            nodo = nodo.hijos[parte]
        
        # Extraer rama
        resultado = {}
        
        def _extraer_rama(nodo_actual, prefijo_actual):
            for nombre_hijo, nodo_hijo in nodo_actual.hijos.items():
                clave_completa = f"{prefijo_actual}.{nombre_hijo}" if prefijo_actual else nombre_hijo
                
                if nodo_hijo.es_hoja and incluir_valores:
                    resultado[clave_completa] = self.flat_map.get(clave_completa)
                elif nodo_hijo.es_hoja:
                    resultado[clave_completa] = None
                
                _extraer_rama(nodo_hijo, clave_completa)
        
        _extraer_rama(nodo, prefijo)
        return resultado
    
    def listar_familias(self, tipo: str = None) -> Dict[str, int]:
        """
        Lista todas las familias disponibles
        
        Args:
            tipo: Filtrar por tipo (ej: "Sensores")
        
        Returns:
            {"Sensores.Ecowitt": 45, "Sensores.DHT22": 12, ...}
        """
        resultado = {}
        
        for familia, adns in self.indice_por_familia.items():
            if tipo is None or familia.startswith(tipo + '.'):
                resultado[familia] = len(adns)
        
        return resultado
    
    def listar_tipos(self) -> Dict[str, int]:
        """
        Lista todos los tipos de variables
        
        Returns:
            {"Sensores": 100, "Prediccion": 50, ...}
        """
        return {tipo: len(adns) for tipo, adns in self.indice_por_tipo.items()}
    
    def eliminar(self, adn: str):
        """Elimina variable del índice"""
        if adn in self.flat_map:
            del self.flat_map[adn]
            self.total_variables = len(self.flat_map)
            self.cache_busquedas.clear()
    
    def existe(self, adn: str) -> bool:
        """Verifica si variable existe (O(1))"""
        return adn in self.flat_map
    
    def obtener_estadisticas(self) -> Dict:
        """Estadísticas del indexador"""
        return {
            'total_variables': self.total_variables,
            'total_familias': len(self.indice_por_familia),
            'total_tipos': len(self.indice_por_tipo),
            'tamaño_cache_busquedas': len(self.cache_busquedas),
            'tipos': self.listar_tipos(),
            'familias_por_tipo': {
                tipo: len([f for f in self.indice_por_familia.keys() 
                          if f.startswith(tipo + '.')])
                for tipo in self.indice_por_tipo.keys()
            }
        }


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          BUS INDEXER - Búsqueda Inteligente por ADN        ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        indexer = BusIndexer()
        
        # Registrar variables
        indexer.registrar_variable("Sensores.Ecowitt.Temperatura.Raw", 23.5)
        indexer.registrar_variable("Sensores.Ecowitt.Humedad.Raw", 65)
        indexer.registrar_variable("Prediccion.LSTM.UTCI.Proximos5Min", 24.2)
        
        # Acceso O(1)
        temp = indexer.obtener("Sensores.Ecowitt.Temperatura.Raw")
        
        # Búsqueda por familia O(k)
        ecowitt_all = indexer.obtener_familia("Sensores.Ecowitt")
        
        # Búsqueda con wildcard
        todas_predicciones = indexer.buscar("Prediccion.*")
        
        # Estadísticas
        stats = indexer.obtener_estadisticas()
        # {
        #   'total_variables': 3,
        #   'total_familias': 2,
        #   'tipos': {'Sensores': 2, 'Prediccion': 1}
        # }
    """)

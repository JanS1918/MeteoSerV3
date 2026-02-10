"""
Validación en Cascada de Sensores - Detección de fallas de dependencias.

Si presión falla → UTCI, Monin-Obukhov, ET0 no deben ejecutarse
Si temperatura falla → muchos índices no pueden ejecutarse
Sistema marca cascada como "rota" para evitar garbage data.
"""
import logging
from typing import Dict, Optional, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoSensor(Enum):
    """Estados posibles de un sensor."""
    OK = "OK"
    FUERA_RANGO = "FUERA_RANGO"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    INCONSISTENTE = "INCONSISTENTE"
    OUTLIER = "OUTLIER"


class DependenciaSensor:
    """Define dependencias entre sensores."""
    
    # Mapa de qué índices requieren qué sensores
    DEPENDENCIAS = {
        "temperatura": [],  # No depende de nada
        "humedad": [],  # No depende de nada
        "presion": [],  # No depende de nada
        "viento": [],  # No depende de nada
        
        # Dependencias de segundo nivel
        "utci": ["temperatura", "humedad", "presion", "viento"],
        "monin_obukhov": ["temperatura", "presion", "viento"],
        "et0": ["temperatura", "humedad", "presion", "viento", "radiacion"],
        "indice_calor": ["temperatura", "humedad"],
        "sensacion_termica": ["temperatura", "viento"],
        "radiacion_neta": ["radiacion", "temperatura"],
        "evapotrans": ["temperatura", "humedad", "presion", "radiacion"],
    }
    
    @classmethod
    def obtener_dependencias(cls, indice: str) -> List[str]:
        """Retorna lista de sensores requeridos para un índice."""
        return cls.DEPENDENCIAS.get(indice, [])
    
    @classmethod
    def indice_puede_ejecutarse(cls, indice: str, sensores_validos: Dict) -> Tuple[bool, List[str]]:
        """
        Verifica si un índice puede ejecutarse con sensores disponibles.
        
        Returns:
            Tupla (puede_ejecutarse, lista_sensores_faltantes)
        """
        dependencias = cls.obtener_dependencias(indice)
        faltantes = []
        
        for sensor in dependencias:
            # Sensor no existe o no es válido
            if sensor not in sensores_validos or not sensores_validos.get(sensor):
                faltantes.append(sensor)
        
        return (len(faltantes) == 0, faltantes)


class ValidadorCascada:
    """Valida sensores y marca dependencias rotas."""
    
    # Rangos de validación
    RANGOS_FISICOS = {
        "temperatura_c": (-99, 99),  # Rango meteorológico
        "humedad_pct": (0, 100),
        "humedad_fraccion": (0, 1),
        "presion_hpa": (800, 1100),  # Rango terrestre
        "viento_ms": (0, 50),  # Hasta huracanes
        "radiacion_w_m2": (0, 2000),  # Máximo solar
        "elevacion_solar_grados": (0, 90),  # Sobre horizonte
    }
    
    def __init__(self):
        """Inicializa validador."""
        self.ultimos_valores = {}
        self.historial_validez = {}  # Mantiene historial de validez
    
    def validar_sensores(self, sensores: Dict[str, float], 
                        outlier_detector=None) -> Dict[str, any]:
        """
        Valida todos los sensores e identifica cascadas rotas.
        
        Args:
            sensores: Dict con valores de sensores
            outlier_detector: Detector de outliers (opcional)
        
        Returns:
            Dict con estado validación y cascada rota
        
        Estructura de retorno:
        {
            "sensores_validos": {"temp": True, "presion": False, ...},
            "razones": {"presion": "FUERA_RANGO (950 hPa < 800)"},
            "cascada_valida": False,
            "indices_disponibles": ["indice_calor", "sensacion_termica"],
            "indices_bloqueados": ["utci", "et0"],
            "recomendaciones": ["Revisar barómetro", "Usar ET0 de fallback"]
        }
        """
        validez = {}
        razones = {}
        recomendaciones = []
        
        # 1. VALIDACIÓN DE RANGO FÍSICO
        for sensor, valor in sensores.items():
            if valor is None:
                validez[sensor] = False
                razones[sensor] = "NO_DISPONIBLE"
                continue
            
            # Obtener rango para este sensor
            rango = None
            for nombre_rango, (minv, maxv) in self.RANGOS_FISICOS.items():
                if nombre_rango.split('_')[0] in sensor.lower():
                    rango = (minv, maxv)
                    break
            
            if rango:
                minv, maxv = rango
                if valor < minv or valor > maxv:
                    validez[sensor] = False
                    razones[sensor] = f"FUERA_RANGO ({valor} ∉ [{minv}, {maxv}])"
                    continue
            
            # Pasar validación de rango
            validez[sensor] = True
            razones[sensor] = "OK"
        
        # 2. DETECCIÓN DE OUTLIERS (si disponible)
        if outlier_detector:
            for sensor, valor in sensores.items():
                if validez.get(sensor, False) and sensor not in ["elevacion_solar_grados"]:
                    es_outlier, msg = outlier_detector.detectar(sensor, valor)
                    if es_outlier:
                        validez[sensor] = False
                        razones[sensor] = f"OUTLIER ({msg})"
        
        # 3. VALIDACIÓN CRUZADA (coherencia entre sensores)
        # Ejemplo: Si T < -50°C, humedad debe ser muy baja
        temp = sensores.get("temperatura_c")
        humedad = sensores.get("humedad_pct")
        if temp is not None and humedad is not None and validez.get("temperatura_c"):
            if temp < -40 and humedad > 30:
                # Poco probable físicamente
                validez["humedad_pct"] = False
                razones["humedad_pct"] = "INCONSISTENTE (T muy baja pero HR alta)"
                recomendaciones.append("Revisar sensor humedad en temperaturas extremas")
        
        # 4. DETERMINAR CASCADA
        sensores_validos = {k: v for k, v in validez.items() if v}
        indices_disponibles = []
        indices_bloqueados = []
        
        for indice in list(DependenciaSensor.DEPENDENCIAS.keys()):
            puede_ejecutarse, faltantes = DependenciaSensor.indice_puede_ejecutarse(
                indice, sensores_validos
            )
            if puede_ejecutarse:
                indices_disponibles.append(indice)
            else:
                indices_bloqueados.append({
                    "indice": indice,
                    "requiere": DependenciaSensor.obtener_dependencias(indice),
                    "faltantes": faltantes
                })
        
        # 5. RECOMENDACIONES
        sensores_rotos = [s for s, v in validez.items() if not v]
        if sensores_rotos:
            recomendaciones.extend([
                f"Revisar sensor {s} ({razones.get(s, 'desconocido')})" 
                for s in sensores_rotos[:3]  # Max 3 recomendaciones
            ])
        
        if not indices_disponibles:
            recomendaciones.append("[WARNING] NINGÚN ÍNDICE DISPONIBLE - Revisar sensores principales")
        
        # Retornar resultado
        return {
            "sensores_validos": validez,
            "razones": razones,
            "cascada_valida": len(indices_disponibles) > 0,
            "indices_disponibles": indices_disponibles,
            "indices_bloqueados": indices_bloqueados,
            "recomendaciones": recomendaciones,
            "timestamp": __import__('time').time(),
        }
    
    def resumen_cascada(self, resultado_validacion: Dict) -> str:
        """Genera resumen humanizado de validación."""
        disponibles = resultado_validacion.get("indices_disponibles", [])
        bloqueados = resultado_validacion.get("indices_bloqueados", [])
        recomendaciones = resultado_validacion.get("recomendaciones", [])
        
        lineas = []
        lineas.append("═" * 60)
        
        if resultado_validacion.get("cascada_valida"):
            lineas.append("[OK] CASCADA VÁLIDA - Todos los índices disponibles pueden calcularse")
        else:
            lineas.append("[ERROR] CASCADA ROTA - Algunos índices no pueden calcularse")
        
        lineas.append("")
        lineas.append(f"  Disponibles ({len(disponibles)}): {', '.join(disponibles[:5])}")
        if len(disponibles) > 5:
            lineas.append(f"                     ... +{len(disponibles)-5} más")
        
        if bloqueados:
            lineas.append(f"  Bloqueados ({len(bloqueados)}):")
            for item in bloqueados[:3]:
                faltantes = ", ".join(item["faltantes"])
                lineas.append(f"    - {item['indice']}: requiere {faltantes}")
            if len(bloqueados) > 3:
                lineas.append(f"    ... +{len(bloqueados)-3} más")
        
        if recomendaciones:
            lineas.append("")
            lineas.append("  Recomendaciones:")
            for rec in recomendaciones[:3]:
                lineas.append(f"    • {rec}")
        
        lineas.append("═" * 60)
        
        return "\n".join(lineas)


if __name__ == "__main__":
    # Test
    print("╔════════════════════════════════════════════╗")
    print("║   Test ValidadorCascada                    ║")
    print("╚════════════════════════════════════════════╝\n")
    
    validador = ValidadorCascada()
    
    # Test 1: Todos los sensores válidos
    print("1️⃣  Caso: Todos los sensores OK")
    sensores_ok = {
        "temperatura_c": 20.0,
        "humedad_pct": 65.0,
        "presion_hpa": 1010.0,
        "viento_ms": 3.5,
    }
    resultado = validador.validar_sensores(sensores_ok)
    print(validador.resumen_cascada(resultado))
    
    # Test 2: Presión fuera de rango
    print("\n2️⃣  Caso: Presión fuera de rango")
    sensores_bad = sensores_ok.copy()
    sensores_bad["presion_hpa"] = 50.0  # Inválido
    resultado = validador.validar_sensores(sensores_bad)
    print(validador.resumen_cascada(resultado))
    
    # Test 3: Múltiples sensores rotos
    print("\n3️⃣  Caso: Múltiples sensores rotos")
    sensores_muy_bad = {
        "temperatura_c": None,  # No disponible
        "humedad_pct": 150,  # Fuera de rango
        "presion_hpa": 1010.0,  # OK
        "viento_ms": 2.0,  # OK
    }
    resultado = validador.validar_sensores(sensores_muy_bad)
    print(validador.resumen_cascada(resultado))

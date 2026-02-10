import logging
"""
Sistema de Testigo de Fallo y Auditoría Selectiva.
Detecta anomalías físicas y romps en los cálculos.
Genera flags de fiabilidad para JSON.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("testigo_fallo")


class FallbackWitness:
    """Monitor de fallos físicos y auditoría de consistencia."""
    
    def __init__(self):
        self.anomalias = []
        self.flags_fiabilidad = {}
    
    def validar_indice(self, nombre: str, valor: float, min_val: float = -float('inf'), 
                       max_val: float = float('inf')) -> Dict[str, Any]:
        """
        Valida un índice calculado contra límites físicos.
        Devuelve dict con valor, flag de fiabilidad, y anotación.
        """
        resultado = {
            "valor": valor,
            "fiabilidad": "Alta",
            "valido": True,
            "anotaciones": []
        }
        
        # Verificación de NaN/Inf
        try:
            if valor is None or (isinstance(valor, float) and (float('nan') == valor or float('inf') == abs(valor))):
                resultado["fiabilidad"] = "Nula"
                resultado["valido"] = False
                resultado["anotaciones"].append("[TESTIGO] Valor NaN/Inf detectado")
                return resultado
        except:
            logging.exception("Silent except at 40 - revisar contexto")
        
        # Verificación de rango
        try:
            v = float(valor)
            if v < min_val or v > max_val:
                resultado["fiabilidad"] = "Baja"
                resultado["valido"] = False
                resultado["anotaciones"].append(f"[TESTIGO] Fuera de rango físico [{min_val}, {max_val}]")
                return resultado
        except:
            resultado["fiabilidad"] = "Nula"
            resultado["valido"] = False
            resultado["anotaciones"].append("[TESTIGO] No convertible a float")
            return resultado
        
        return resultado
    
    def auditar_coherencia(self, indices: Dict[str, Any]) -> List[str]:
        """
        Auditoría selectiva de coherencia física.
        Devuelve lista de anomalías detectadas.
        """
        anomalias = []
        
        # Coherencia Temperatura - Punto de Rocío
        temp = indices.get("temperatura", {}).get("valor")
        td = indices.get("punto_rocio", {}).get("valor")
        if temp is not None and td is not None:
            if td > temp:
                anomalias.append("[AUDITORIA] Punto de rocío > Temperatura (físicamente imposible)")
        
        # Coherencia Radiación - UV
        rad = indices.get("radiacion", {}).get("valor")
        uv = indices.get("uv", {}).get("valor")
        if rad is not None and uv is not None:
            if rad > 1000 and uv < 1:
                anomalias.append("[AUDITORIA] Radiación alta pero UV bajo (inconsistente)")
        
        # Coherencia Presión - Altitud
        pres = indices.get("presion", {}).get("valor")
        if pres is not None:
            if pres < 700 or pres > 1050:
                anomalias.append(f"[AUDITORIA] Presión {pres} kPa en rango anómalo")
        
        # Coherencia HR - VPD
        hr = indices.get("humedad", {}).get("valor")
        vpd = indices.get("vpd", {}).get("valor")
        if hr is not None and vpd is not None:
            if hr > 95 and vpd > 0.5:
                anomalias.append("[AUDITORIA] HR muy alta pero VPD alto (inconsistente)")
        
        # Coherencia UTCI - Temperatura
        utci = indices.get("utci", {}).get("valor")
        if temp is not None and utci is not None:
            diff = abs(float(utci) - float(temp))
            if diff > 30:
                anomalias.append(f"[AUDITORIA] UTCI diferencia > 30°C ({diff:.1f}°C)")
        
        self.anomalias = anomalias
        return anomalias
    
    def generar_flags(self, indices: Dict[str, Any]) -> Dict[str, str]:
        """
        Genera flags de fiabilidad para cada índice basados en:
        - Fuente (real vs estimado)
        - Validación física
        - Coherencia con otros índices
        """
        flags = {}
        
        for nombre, entrada in indices.items():
            if not isinstance(entrada, dict):
                continue
            
            fiabilidad = "Alta"
            
            # Regla 1: Si es estimado, reducir
            if entrada.get("estimado", False):
                fiabilidad = "Media"
            
            # Regla 2: Si hay anotación de auditoría, reducir
            explicacion = str(entrada.get("explicacion", "")).lower()
            if "error" in explicacion or "falla" in explicacion:
                fiabilidad = "Baja"
            
            # Regla 3: Información de fiabilidad explícita
            if "fiabilidad" in entrada:
                fiabilidad = entrada["fiabilidad"]
            
            flags[nombre] = fiabilidad
        
        self.flags_fiabilidad = flags
        return flags
    
    def reporte_auditoria(self) -> Dict[str, Any]:
        """Genera reporte de auditoría completo."""
        return {
            "anomalias_detectadas": len(self.anomalias),
            "anomalias": self.anomalias,
            "indices_con_baja_fiabilidad": {
                k: v for k, v in self.flags_fiabilidad.items() if v != "Alta"
            }
        }


# Instancia global
_witness = FallbackWitness()


def validar_indice(nombre: str, valor: float, min_val: float = -float('inf'), 
                   max_val: float = float('inf')) -> Dict[str, Any]:
    """Función pública para validación de índices."""
    return _witness.validar_indice(nombre, valor, min_val, max_val)


def auditar_coherencia(indices: Dict[str, Any]) -> List[str]:
    """Función pública para auditoría de coherencia."""
    return _witness.auditar_coherencia(indices)


def generar_flags_fiabilidad(indices: Dict[str, Any]) -> Dict[str, str]:
    """Función pública para generación de flags."""
    return _witness.generar_flags(indices)


def reporte_auditoria() -> Dict[str, Any]:
    """Función pública para reporte de auditoría."""
    return _witness.reporte_auditoria()

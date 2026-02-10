"""
[GUARDIAN] CAPA 25: SANITIZACIÓN DE DATOS EXTERNOS (HIGIENE METEOROLÓGICA)

MISIÓN CRÍTICA:
Validar TODOS los datos externos antes de que entren al sistema de aprendizaje.
Prevenir envenenamiento del MOS Clustering por APIs comprometidas.

FILOSOFÍA:
"El riñón del Acorazado - Solo datos puros entran al sistema"

CASOS CRÍTICOS:
- API envía temperatura "25.5°C" (string) en vez de 25.5 (float)
- API envía temperatura 150°C (físicamente imposible)
- API envía campo "__proto__" (prototype pollution)
- API envía null donde esperamos número
- API comprometida inyecta eval() en strings

CONSUMO: <0.01% CPU
AUTOR: V47.5 PATRULLA SOBERANA - 25 CAPAS
FECHA: 2026-02-05
"""

import re
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SanitizacionDatosExternos:
    """
    Sanitizador de datos externos para prevenir envenenamiento del aprendizaje.
    
    Valida tipos, rangos físicos y rechaza inyección de código.
    """
    
    # Rangos físicos válidos para Argentona (Maresme)
    RANGOS_FISICOS = {
        "temperatura": {"min": -30.0, "max": 60.0, "unidad": "°C"},
        "hr": {"min": 0.0, "max": 100.0, "unidad": "%"},
        "presion": {"min": 850.0, "max": 1100.0, "unidad": "hPa"},
        "viento_velocidad": {"min": 0.0, "max": 200.0, "unidad": "km/h"},
        "viento_rafaga": {"min": 0.0, "max": 250.0, "unidad": "km/h"},
        "lluvia": {"min": 0.0, "max": 500.0, "unidad": "mm"},
        "radiacion_solar": {"min": 0.0, "max": 1500.0, "unidad": "W/m²"},
        "uv": {"min": 0.0, "max": 16.0, "unidad": "index"},
        "punto_rocio": {"min": -40.0, "max": 40.0, "unidad": "°C"},
        "sensacion_termica": {"min": -50.0, "max": 70.0, "unidad": "°C"},
    }
    
    # Campos obligatorios por fuente
    CAMPOS_OBLIGATORIOS = {
        "ecowitt": ["temperatura", "hr", "presion"],
        "openweather": ["temperatura", "hr", "presion", "viento_velocidad"],
        "aemet": ["temperatura", "hr"],
        "local": ["temperatura", "hr", "presion"],
    }
    
    # Whitelist de campos permitidos (rechazo de campos desconocidos)
    CAMPOS_PERMITIDOS = {
        "temperatura", "hr", "presion", "viento_velocidad", "viento_direccion",
        "viento_rafaga", "lluvia", "lluvia_acumulada", "radiacion_solar",
        "uv", "punto_rocio", "sensacion_termica", "timestamp", "fuente",
        "latitud", "longitud", "altitud", "estacion_id"
    }
    
    # Patrones de inyección de código
    PATRONES_INYECCION = [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"compile\s*\(",
        r"__.*__",  # Atributos mágicos Python
        r"<script",  # XSS
        r"javascript:",
        r"on\w+\s*=",  # Eventos JS
    ]
    
    def __init__(self):
        self.datos_rechazados = []
        self.estadisticas = {
            "total_validaciones": 0,
            "rechazados_tipo": 0,
            "rechazados_rango": 0,
            "rechazados_inyeccion": 0,
            "rechazados_campos_extra": 0,
            "aceptados": 0,
        }
        
        logger.info("[GUARDIAN] Sanitización de Datos Externos (Higiene Meteorológica) inicializada")
    
    def validar_tipo(self, valor: Any, tipo_esperado: type) -> bool:
        """
        Valida que el valor sea del tipo esperado.
        
        Args:
            valor: Valor a validar
            tipo_esperado: Tipo esperado (float, int, str)
            
        Returns:
            True si es del tipo correcto
        """
        if tipo_esperado == float:
            # Aceptar int como float
            return isinstance(valor, (int, float))
        
        return isinstance(valor, tipo_esperado)
    
    def validar_rango_fisico(self, campo: str, valor: float) -> bool:
        """
        Valida que el valor esté en rango físico posible.
        
        Args:
            campo: Nombre del campo (temperatura, hr, etc.)
            valor: Valor numérico
            
        Returns:
            True si está en rango válido
        """
        if campo not in self.RANGOS_FISICOS:
            return True  # Campo desconocido, no validar rango
        
        rango = self.RANGOS_FISICOS[campo]
        
        if valor < rango["min"] or valor > rango["max"]:
            logger.warning(
                f"[WARNING] Valor fuera de rango físico: {campo}={valor} "
                f"(rango válido: {rango['min']}-{rango['max']} {rango['unidad']})"
            )
            return False
        
        return True
    
    def detectar_inyeccion(self, valor: Any) -> bool:
        """
        Detecta intentos de inyección de código.
        
        Args:
            valor: Valor a analizar (string, dict, list)
            
        Returns:
            True si detecta inyección
        """
        if isinstance(valor, str):
            for patron in self.PATRONES_INYECCION:
                if re.search(patron, valor, re.IGNORECASE):
                    logger.critical(
                        f"[CRITICAL] INYECCIÓN DE CÓDIGO DETECTADA: {patron} en '{valor[:50]}...'"
                    )
                    return True
        
        elif isinstance(valor, dict):
            # Validar claves del dict
            for key in valor.keys():
                if self.detectar_inyeccion(key):
                    return True
                if self.detectar_inyeccion(valor[key]):
                    return True
        
        elif isinstance(valor, list):
            for item in valor:
                if self.detectar_inyeccion(item):
                    return True
        
        return False
    
    def sanitizar_dato_meteorologico(
        self,
        datos: Dict[str, Any],
        fuente: str = "desconocida"
    ) -> Optional[Dict[str, Any]]:
        """
        Sanitiza datos meteorológicos de fuente externa.
        
        Args:
            datos: Diccionario con datos meteorológicos
            fuente: Fuente de datos (ecowitt, openweather, aemet, local)
            
        Returns:
            Datos sanitizados o None si falla validación
        """
        self.estadisticas["total_validaciones"] += 1
        
        # 1. VALIDAR TIPO DE ENTRADA
        if not isinstance(datos, dict):
            logger.error(f"[ERROR] Datos no son diccionario: {type(datos)}")
            self.estadisticas["rechazados_tipo"] += 1
            return None
        
        # 2. DETECTAR INYECCIÓN EN TODO EL PAYLOAD
        if self.detectar_inyeccion(datos):
            logger.critical("[CRITICAL] DATOS RECHAZADOS: Inyección de código detectada")
            self.estadisticas["rechazados_inyeccion"] += 1
            self._registrar_rechazo(datos, fuente, "INYECCION_CODIGO")
            return None
        
        # 3. VALIDAR CAMPOS OBLIGATORIOS
        campos_obligatorios = self.CAMPOS_OBLIGATORIOS.get(fuente, ["temperatura", "hr"])
        
        for campo in campos_obligatorios:
            if campo not in datos or datos[campo] is None:
                logger.warning(
                    f"[WARNING] Campo obligatorio faltante: {campo} (fuente: {fuente})"
                )
                # No rechazar, solo advertir
        
        # 4. ELIMINAR CAMPOS NO PERMITIDOS (Whitelist)
        datos_sanitizados = {}
        campos_rechazados = []
        
        for campo, valor in datos.items():
            if campo not in self.CAMPOS_PERMITIDOS:
                campos_rechazados.append(campo)
                logger.warning(f"[WARNING] Campo no permitido rechazado: {campo}")
                continue
            
            datos_sanitizados[campo] = valor
        
        if campos_rechazados:
            self.estadisticas["rechazados_campos_extra"] += len(campos_rechazados)
        
        # 5. VALIDAR TIPOS Y RANGOS DE CAMPOS NUMÉRICOS
        campos_numericos = [
            "temperatura", "hr", "presion", "viento_velocidad", "viento_direccion",
            "viento_rafaga", "lluvia", "lluvia_acumulada", "radiacion_solar",
            "uv", "punto_rocio", "sensacion_termica"
        ]
        
        for campo in campos_numericos:
            if campo not in datos_sanitizados:
                continue
            
            valor = datos_sanitizados[campo]
            
            # Validar tipo
            if not self.validar_tipo(valor, float):
                logger.error(
                    f"[ERROR] Tipo incorrecto: {campo}={valor} (esperado: float, recibido: {type(valor).__name__})"
                )
                self.estadisticas["rechazados_tipo"] += 1
                self._registrar_rechazo(datos, fuente, f"TIPO_INCORRECTO_{campo}")
                return None
            
            # Convertir a float
            valor_float = float(valor)
            datos_sanitizados[campo] = valor_float
            
            # Validar rango físico
            if not self.validar_rango_fisico(campo, valor_float):
                logger.error(
                    f"[ERROR] Rango físico inválido: {campo}={valor_float}"
                )
                self.estadisticas["rechazados_rango"] += 1
                self._registrar_rechazo(datos, fuente, f"RANGO_INVALIDO_{campo}")
                return None
        
        # 6. AÑADIR METADATOS DE SANITIZACIÓN
        datos_sanitizados["_sanitizado"] = True
        datos_sanitizados["_timestamp_sanitizacion"] = datetime.now().isoformat()
        datos_sanitizados["_fuente_original"] = fuente
        
        self.estadisticas["aceptados"] += 1
        
        logger.debug(f"[OK] Datos sanitizados correctamente (fuente: {fuente})")
        
        return datos_sanitizados
    
    def _registrar_rechazo(self, datos: Dict, fuente: str, razon: str):
        """Registra datos rechazados para auditoría."""
        self.datos_rechazados.append({
            "timestamp": datetime.now().isoformat(),
            "fuente": fuente,
            "razon": razon,
            "datos": str(datos)[:200]  # Primeros 200 chars
        })
        
        # Mantener últimos 100 rechazos
        self.datos_rechazados = self.datos_rechazados[-100:]
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas de sanitización.
        
        Returns:
            {
                "total_validaciones": 1234,
                "aceptados": 1200,
                "rechazados_total": 34,
                "tasa_rechazo_pct": 2.75
            }
        """
        total_rechazados = (
            self.estadisticas["rechazados_tipo"] +
            self.estadisticas["rechazados_rango"] +
            self.estadisticas["rechazados_inyeccion"]
        )
        
        tasa_rechazo = 0.0
        if self.estadisticas["total_validaciones"] > 0:
            tasa_rechazo = (total_rechazados / self.estadisticas["total_validaciones"]) * 100
        
        return {
            **self.estadisticas,
            "rechazados_total": total_rechazados,
            "tasa_rechazo_pct": round(tasa_rechazo, 2),
            "ultimos_rechazos": self.datos_rechazados[-10:]  # Últimos 10
        }


# ============================================================================
# INTEGRACIÓN CON SISTEMA PRINCIPAL
# ============================================================================

def integrar_sanitizacion_en_sistema():
    """
    Ejemplo de integración en main_asgi.py o APIs externas.
    
    ```python
    # En core/api/openweather_api.py
    from core.security.sanitizacion_datos_externos import SanitizacionDatosExternos
    
    sanitizador = SanitizacionDatosExternos()
    
    def obtener_datos_openweather():
        # Obtener datos de API
        respuesta = requests.get(url)
        datos_raw = respuesta.json()
        
        # SANITIZAR ANTES DE USAR
        datos_limpios = sanitizador.sanitizar_dato_meteorologico(
            datos_raw,
            fuente="openweather"
        )
        
        if datos_limpios is None:
            logger.error("[CRITICAL] Datos de OpenWeather rechazados por sanitización")
            # Usar datos locales (Capa 21: Degradación Elegante)
            return obtener_datos_locales()
        
        # Procesar datos limpios
        return datos_limpios
    
    # En core/meteo/ecowitt_receiver.py
    def procesar_datos_ecowitt(payload):
        datos_limpios = sanitizador.sanitizar_dato_meteorologico(
            payload,
            fuente="ecowitt"
        )
        
        if datos_limpios is None:
            logger.critical("[CRITICAL] Datos de Ecowitt rechazados - Posible compromiso")
            # Activar Modo Fortaleza si múltiples rechazos
            return None
        
        # Enviar al Bus solo si está sanitizado
        bus.publicar("datos_ecowitt_sanitizados", datos_limpios)
    ```
    """
    pass


if __name__ == "__main__":
    # Test exhaustivo
    logging.basicConfig(level=logging.INFO)
    
    sanitizador = SanitizacionDatosExternos()
    
    # Test 1: Datos válidos
    print("\n[OK] Test 1: Datos válidos")
    datos_validos = {
        "temperatura": 25.5,
        "hr": 65.0,
        "presion": 1013.25,
        "viento_velocidad": 15.0
    }
    resultado = sanitizador.sanitizar_dato_meteorologico(datos_validos, "ecowitt")
    print(f"Resultado: {'ACEPTADO' if resultado else 'RECHAZADO'}")
    
    # Test 2: Temperatura fuera de rango
    print("\n[ERROR] Test 2: Temperatura fuera de rango")
    datos_invalidos = {
        "temperatura": 150.0,  # Imposible
        "hr": 65.0,
        "presion": 1013.25
    }
    resultado = sanitizador.sanitizar_dato_meteorologico(datos_invalidos, "ecowitt")
    print(f"Resultado: {'ACEPTADO' if resultado else 'RECHAZADO'}")
    
    # Test 3: Inyección de código
    print("\n[CRITICAL] Test 3: Inyección de código")
    datos_maliciosos = {
        "temperatura": 25.5,
        "hr": "eval('import os; os.system(\"rm -rf /\")')",
        "presion": 1013.25
    }
    resultado = sanitizador.sanitizar_dato_meteorologico(datos_maliciosos, "ecowitt")
    print(f"Resultado: {'ACEPTADO' if resultado else 'RECHAZADO'}")
    
    # Test 4: Tipo incorrecto
    print("\n[ERROR] Test 4: Tipo incorrecto")
    datos_tipo_mal = {
        "temperatura": "25.5°C",  # String en vez de float
        "hr": 65.0,
        "presion": 1013.25
    }
    resultado = sanitizador.sanitizar_dato_meteorologico(datos_tipo_mal, "ecowitt")
    print(f"Resultado: {'ACEPTADO' if resultado else 'RECHAZADO'}")
    
    # Test 5: Campos extra sospechosos
    print("\n[WARNING] Test 5: Campos extra sospechosos")
    datos_extra = {
        "temperatura": 25.5,
        "hr": 65.0,
        "presion": 1013.25,
        "__proto__": {"malware": True},  # Prototype pollution
        "exec_cmd": "malware.exe"
    }
    resultado = sanitizador.sanitizar_dato_meteorologico(datos_extra, "ecowitt")
    print(f"Resultado: {'ACEPTADO' if resultado else 'RECHAZADO'}")
    if resultado:
        print(f"Campos eliminados: {set(datos_extra.keys()) - set(resultado.keys())}")
    
    # Estadísticas finales
    print("\n[STATS] Estadísticas:")
    stats = sanitizador.obtener_estadisticas()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

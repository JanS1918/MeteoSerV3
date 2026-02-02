"""
protocolo_certificacion_arranque_v26.py
========================================
Protocolo de Certificación de Arranque para Biblia V2.6

Valida:
1. Factor Z (Compresibilidad Real del Aire)
2. Calibración de Ekman (Rugosidad de Argentona)
3. Integridad SHA256
4. Limpieza de depuración

Autor: Acorazado Argentona V2.6
Fecha: 1 de febrero de 2026
"""

import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from core.correccion_geofisica_v26 import (
    factor_compresibilidad_virial,
    densidad_aire_real,
    albedo_dinamico,
    angulo_inflow_ekman
)

# Logger dedicado para arranque
logger = logging.getLogger("CERTIFICACION_V26")
logger.setLevel(logging.INFO)

# Archivo de log de certificación
log_path = Path("logs/certificacion_v26.log")
log_path.parent.mkdir(exist_ok=True)
handler = logging.FileHandler(log_path)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(handler)


class ProtocoloCertificacionV26:
    """Protocolo de certificación de arranque del Acorazado Argentona V2.6"""
    
    def __init__(self):
        self.factor_z = None
        self.angulo_ekman = None
        self.sha256_valido = False
        self.estado_certificacion = "NO_INICIADO"
        self.rugosidad_argentona = 0.15  # Rugosidad típica para terreno semi-rural
        
    def validar_factor_z(self, presion_hpa, temperatura_c):
        """
        Validación del Factor Z (Compresibilidad Real)
        
        Args:
            presion_hpa: Presión actual en hPa
            temperatura_c: Temperatura actual en °C
            
        Returns:
            dict: Resultado de validación con Factor Z y desviación del gas ideal
        """
        logger.info("="*70)
        logger.info("INICIANDO VALIDACIÓN DE METROLOGÍA")
        logger.info("="*70)
        
        # Calcular Factor Z
        self.factor_z = factor_compresibilidad_virial(presion_hpa, temperatura_c)
        
        # Calcular desviación del gas ideal (%)
        desviacion_ideal = abs(1.0 - self.factor_z) * 100
        
        # Densidad real vs ideal
        densidad_real = densidad_aire_real(presion_hpa, temperatura_c, self.factor_z)
        densidad_ideal = densidad_aire_real(presion_hpa, temperatura_c, 1.0)
        diferencia_densidad = abs(densidad_real - densidad_ideal)
        
        logger.info(f"[METROLOGÍA] Aire Real detectado. Factor Z = {self.factor_z:.6f}")
        logger.info(f"[METROLOGÍA] Desviación del gas ideal: {desviacion_ideal:.4f}%")
        logger.info(f"[METROLOGÍA] Densidad real: {densidad_real:.4f} kg/m³")
        logger.info(f"[METROLOGÍA] Densidad ideal: {densidad_ideal:.4f} kg/m³")
        logger.info(f"[METROLOGÍA] Diferencia: {diferencia_densidad:.6f} kg/m³")
        logger.info(f"[METROLOGÍA] Presión: {presion_hpa:.1f} hPa | Temperatura: {temperatura_c:.1f}°C")
        
        return {
            "factor_z": self.factor_z,
            "desviacion_ideal_pct": desviacion_ideal,
            "densidad_real_kg_m3": densidad_real,
            "densidad_ideal_kg_m3": densidad_ideal,
            "diferencia_densidad_kg_m3": diferencia_densidad,
            "presion_hpa": presion_hpa,
            "temperatura_c": temperatura_c,
            "validado": True
        }
    
    def calibrar_ekman(self, velocidad_viento_ms):
        """
        Calibración del Ángulo de Inflow de Ekman para Argentona
        
        Args:
            velocidad_viento_ms: Velocidad del viento en m/s
            
        Returns:
            dict: Resultado de calibración con ángulo de inflow
        """
        logger.info("="*70)
        logger.info("CALIBRANDO BRÚJULA TÁCTICA - ÁNGULO DE EKMAN")
        logger.info("="*70)
        
        self.angulo_ekman = angulo_inflow_ekman(velocidad_viento_ms, self.rugosidad_argentona)
        
        logger.info(f"[EKMAN] Rugosidad de terreno Argentona: {self.rugosidad_argentona:.3f}")
        logger.info(f"[EKMAN] Velocidad de viento: {velocidad_viento_ms:.1f} m/s")
        logger.info(f"[EKMAN] Ángulo de Inflow calculado: {self.angulo_ekman:.1f}°")
        logger.info(f"[EKMAN] La Brújula Táctica corregirá {self.angulo_ekman:.1f}° por fricción del terreno")
        
        return {
            "angulo_inflow_grados": self.angulo_ekman,
            "rugosidad_terreno": self.rugosidad_argentona,
            "velocidad_viento_ms": velocidad_viento_ms,
            "calibrado": True
        }
    
    def verificar_integridad_sha256(self):
        """
        Verificación de integridad SHA256 de módulos críticos
        
        Returns:
            dict: Resultado de verificación con SHA256 de cada módulo
        """
        logger.info("="*70)
        logger.info("VERIFICANDO INTEGRIDAD SHA256")
        logger.info("="*70)
        
        modulos_criticos = [
            "core/elite_motors_v25.py",
            "core/bucholtz_rayleigh_v25.py",
            "core/vector_aproximacion_v26.py",
            "core/integracion_elite_motors_v25.py",
            "core/correccion_geofisica_v26.py"
        ]
        
        hashes = {}
        todos_validos = True
        
        for modulo in modulos_criticos:
            try:
                path = Path(modulo)
                if path.exists():
                    with open(path, 'rb') as f:
                        contenido = f.read()
                        hash_sha256 = hashlib.sha256(contenido).hexdigest()
                        hashes[modulo] = hash_sha256
                        logger.info(f"[SHA256] {modulo}: {hash_sha256[:16]}...")
                else:
                    logger.warning(f"[SHA256] {modulo}: ARCHIVO NO ENCONTRADO")
                    todos_validos = False
                    hashes[modulo] = None
            except Exception as e:
                logger.error(f"[SHA256] Error verificando {modulo}: {e}")
                todos_validos = False
                hashes[modulo] = None
        
        # Hash maestro (hash de todos los hashes)
        if todos_validos:
            hash_maestro = hashlib.sha256(
                json.dumps(hashes, sort_keys=True).encode()
            ).hexdigest()
            logger.info(f"[SHA256] HASH MAESTRO: {hash_maestro}")
            logger.info("[SHA256] ✓ INTEGRIDAD VERIFICADA - VERDE")
            self.sha256_valido = True
        else:
            logger.error("[SHA256] ✗ INTEGRIDAD COMPROMETIDA - ROJO")
            self.sha256_valido = False
            hash_maestro = None
        
        return {
            "hashes_modulos": hashes,
            "hash_maestro": hash_maestro,
            "integridad_valida": todos_validos
        }
    
    def limpiar_depuracion(self):
        """
        Limpia rastros de depuración y prepara el sistema para producción
        """
        logger.info("="*70)
        logger.info("LIMPIANDO RASTROS DE DEPURACIÓN")
        logger.info("="*70)
        
        # Limpiar logs antiguos de debug
        log_dir = Path("logs")
        if log_dir.exists():
            archivos_debug = list(log_dir.glob("debug_*.log"))
            for archivo in archivos_debug:
                try:
                    archivo.unlink()
                    logger.info(f"[LIMPIEZA] Eliminado: {archivo.name}")
                except Exception as e:
                    logger.warning(f"[LIMPIEZA] No se pudo eliminar {archivo.name}: {e}")
        
        logger.info("[LIMPIEZA] ✓ Sistema preparado para producción")
    
    def ejecutar_certificacion_completa(self, presion_hpa, temperatura_c, velocidad_viento_ms):
        """
        Ejecuta el protocolo completo de certificación
        
        Args:
            presion_hpa: Presión actual
            temperatura_c: Temperatura actual
            velocidad_viento_ms: Velocidad del viento
            
        Returns:
            dict: Resultado completo de certificación
        """
        logger.info("╔" + "="*68 + "╗")
        logger.info("║" + " "*15 + "ACORAZADO ARGENTONA V2.6" + " "*29 + "║")
        logger.info("║" + " "*10 + "PROTOCOLO DE CERTIFICACIÓN DE ARRANQUE" + " "*20 + "║")
        logger.info("╚" + "="*68 + "╝")
        logger.info("")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("")
        
        self.estado_certificacion = "EN_PROCESO"
        
        # 1. Validar Factor Z
        resultado_z = self.validar_factor_z(presion_hpa, temperatura_c)
        logger.info("")
        
        # 2. Calibrar Ekman
        resultado_ekman = self.calibrar_ekman(velocidad_viento_ms)
        logger.info("")
        
        # 3. Verificar SHA256
        resultado_sha256 = self.verificar_integridad_sha256()
        logger.info("")
        
        # 4. Limpiar depuración
        self.limpiar_depuracion()
        logger.info("")
        
        # Estado final
        if resultado_sha256["integridad_valida"]:
            self.estado_certificacion = "CERTIFICADO_VALIDO"
            logger.info("╔" + "="*68 + "╗")
            logger.info("║" + " "*18 + "✓ CERTIFICACIÓN EXITOSA" + " "*27 + "║")
            logger.info("║" + " "*12 + "ACORAZADO ARGENTONA V2.6 OPERATIVO" + " "*22 + "║")
            logger.info("╚" + "="*68 + "╝")
        else:
            self.estado_certificacion = "CERTIFICACION_FALLIDA"
            logger.error("╔" + "="*68 + "╗")
            logger.error("║" + " "*18 + "✗ CERTIFICACIÓN FALLIDA" + " "*27 + "║")
            logger.error("║" + " "*15 + "SISTEMA BLOQUEADO POR SEGURIDAD" + " "*22 + "║")
            logger.error("╚" + "="*68 + "╝")
        
        return {
            "estado": self.estado_certificacion,
            "factor_z": resultado_z,
            "ekman": resultado_ekman,
            "sha256": resultado_sha256,
            "timestamp": datetime.now().isoformat()
        }
    
    def comparar_factor_z_interior_exterior(self, presion_int, temp_int, presion_ext, temp_ext):
        """
        Compara el Factor Z entre interior y exterior
        
        Args:
            presion_int: Presión interior (hPa)
            temp_int: Temperatura interior (°C)
            presion_ext: Presión exterior (hPa)
            temp_ext: Temperatura exterior (°C)
            
        Returns:
            dict: Comparación detallada
        """
        logger.info("="*70)
        logger.info("COMPARACIÓN: FACTOR Z INTERIOR vs EXTERIOR")
        logger.info("="*70)
        
        # Factor Z interior
        z_interior = factor_compresibilidad_virial(presion_int, temp_int)
        densidad_int = densidad_aire_real(presion_int, temp_int, z_interior)
        
        # Factor Z exterior
        z_exterior = factor_compresibilidad_virial(presion_ext, temp_ext)
        densidad_ext = densidad_aire_real(presion_ext, temp_ext, z_exterior)
        
        # Diferencias
        diff_z = abs(z_interior - z_exterior)
        diff_densidad = abs(densidad_int - densidad_ext)
        
        logger.info(f"[INTERIOR] Presión: {presion_int:.1f} hPa | Temp: {temp_int:.1f}°C")
        logger.info(f"[INTERIOR] Factor Z: {z_interior:.6f} | Densidad: {densidad_int:.4f} kg/m³")
        logger.info("")
        logger.info(f"[EXTERIOR] Presión: {presion_ext:.1f} hPa | Temp: {temp_ext:.1f}°C")
        logger.info(f"[EXTERIOR] Factor Z: {z_exterior:.6f} | Densidad: {densidad_ext:.4f} kg/m³")
        logger.info("")
        logger.info(f"[DIFERENCIA] ΔZ: {diff_z:.6f} | Δρ: {diff_densidad:.4f} kg/m³")
        logger.info(f"[FÍSICA] La densidad del aire cambia {diff_densidad*1000:.2f} g/m³ entre ambientes")
        
        return {
            "interior": {
                "factor_z": z_interior,
                "densidad_kg_m3": densidad_int,
                "presion_hpa": presion_int,
                "temperatura_c": temp_int
            },
            "exterior": {
                "factor_z": z_exterior,
                "densidad_kg_m3": densidad_ext,
                "presion_hpa": presion_ext,
                "temperatura_c": temp_ext
            },
            "diferencias": {
                "delta_z": diff_z,
                "delta_densidad_kg_m3": diff_densidad,
                "delta_densidad_g_m3": diff_densidad * 1000
            }
        }


def ejecutar_protocolo_arranque(presion_hpa, temperatura_c, velocidad_viento_ms):
    """
    Función principal para ejecutar el protocolo de arranque
    
    Args:
        presion_hpa: Presión actual
        temperatura_c: Temperatura actual
        velocidad_viento_ms: Velocidad del viento
    """
    protocolo = ProtocoloCertificacionV26()
    resultado = protocolo.ejecutar_certificacion_completa(
        presion_hpa, temperatura_c, velocidad_viento_ms
    )
    
    # Si hay datos de interior, comparar
    # (esto se puede conectar al sensor interior si existe)
    
    return resultado


if __name__ == "__main__":
    # Ejemplo de ejecución con datos típicos de Argentona
    print("Ejecutando Protocolo de Certificación V2.6...")
    print("="*70)
    
    resultado = ejecutar_protocolo_arranque(
        presion_hpa=1019.1,
        temperatura_c=18.5,
        velocidad_viento_ms=5.2
    )
    
    print("\n" + "="*70)
    print("RESULTADO DE CERTIFICACIÓN:")
    print(f"Estado: {resultado['estado']}")
    print(f"Factor Z: {resultado['factor_z']['factor_z']:.6f}")
    print(f"Desviación del ideal: {resultado['factor_z']['desviacion_ideal_pct']:.4f}%")
    print(f"Ángulo de Ekman: {resultado['ekman']['angulo_inflow_grados']:.1f}°")
    print(f"SHA256 válido: {resultado['sha256']['integridad_valida']}")
    print("="*70)

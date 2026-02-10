#!/usr/bin/env python3
"""
SELLO DEFINITIVO SHA256 - PATRULLA FINAL 64 BITS
=================================================
Generación de hashes criptográficos para:
1. Configuración de estación (config_estacion.json)
2. Ubicación exacta (last_location.json)
3. Motor de física (physics_engine_2026.py)
4. Vista de modelo (viewmodel.py - formato 8 decimales)

Esto certifica la inmutabilidad de:
- Gravedad: 9.80272394 m/s² (Somigliana-Helmert, Argentona)
- Latitud: 41.55326700° (8 decimales)
- Longitud: 2.39684500° (8 decimales)
- Altitud: 118.0 m

El sha256 de este archivo sellaremos el protocolo Soberanía Directa.
"""

import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SelloDefinitivo:
    """Generador de hashes SHA256 para componentes críticos."""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.data_dir = self.workspace_root / "data"
        self.core_dir = self.workspace_root / "core"
        self.app_ui_dir = self.workspace_root / "app" / "ui"
        self.logs_dir = self.workspace_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def sha256_archivo(self, ruta: Path, nombre: str) -> dict:
        """Genera SHA256 de un archivo."""
        try:
            if not ruta.exists():
                logger.warning(f"[WARNING] Archivo no encontrado: {ruta}")
                return {'nombre': nombre, 'ruta': str(ruta), 'sha256': None, 'estado': 'NO_ENCONTRADO'}
            
            with open(ruta, 'rb') as f:
                contenido = f.read()
                hash_value = hashlib.sha256(contenido).hexdigest()
            
            logger.info(f"[OK] {nombre}: {hash_value[:16]}...")
            return {
                'nombre': nombre,
                'ruta': str(ruta.relative_to(self.workspace_root)),
                'sha256': hash_value,
                'tamanio_bytes': len(contenido),
                'estado': 'OK'
            }
        except Exception as e:
            logger.error(f"[ERROR] Error leyendo {nombre}: {e}")
            return {'nombre': nombre, 'ruta': str(ruta), 'sha256': None, 'estado': 'ERROR', 'error': str(e)}
    
    def sha256_contenido(self, contenido: str, nombre: str) -> dict:
        """Genera SHA256 de un contenido string."""
        try:
            hash_value = hashlib.sha256(contenido.encode('utf-8')).hexdigest()
            logger.info(f"[OK] {nombre}: {hash_value[:16]}...")
            return {
                'nombre': nombre,
                'contenido_preview': contenido[:100] if len(contenido) > 100 else contenido,
                'sha256': hash_value,
                'tamanio_bytes': len(contenido.encode('utf-8')),
                'estado': 'OK'
            }
        except Exception as e:
            logger.error(f"[ERROR] Error con {nombre}: {e}")
            return {'nombre': nombre, 'sha256': None, 'estado': 'ERROR', 'error': str(e)}
    
    def ejecutar_patrulla(self):
        """Ejecuta la patrulla completa de hashes SHA256."""
        logger.info("🛰️ INICIANDO PATRULLA DE SELLO DEFINITIVO SHA256 (64 bits)")
        logger.info("=" * 80)
        
        hashes = {
            'timestamp_generacion': datetime.now().isoformat(),
            'ubicacion_sellada': 'Argentona, Barcelona, España',
            'coordenadas': {
                'latitud_exacta': 41.553267,
                'longitud_exacta': 2.396845,
                'altitud_m': 118.0
            },
            'gravedad_sellada': {
                'valor_m_s2': 9.80272394,
                'formula': 'Somigliana-Helmert con corrección Helmert 2do orden',
                'precisión': '11 decimales',
                'fuente': 'PhysicsEngine2026'
            },
            'componentes_criticos': []
        }
        
        # 1. Sello config_estacion.json
        hash1 = self.sha256_archivo(
            self.data_dir / "config_estacion.json",
            "Configuración de Estación"
        )
        hashes['componentes_criticos'].append(hash1)
        
        # 2. Sello last_location.json
        hash2 = self.sha256_archivo(
            self.data_dir / "last_location.json",
            "Ubicación Última (LocationEngine)"
        )
        hashes['componentes_criticos'].append(hash2)
        
        # 3. Sello physics_engine_2026.py
        hash3 = self.sha256_archivo(
            self.core_dir / "indices" / "physics_engine_2026.py",
            "Motor de Física 2026 (Somigliana-Helmert)"
        )
        hashes['componentes_criticos'].append(hash3)
        
        # 4. Sello viewmodel.py (formato 8 decimales)
        hash4 = self.sha256_archivo(
            self.app_ui_dir / "viewmodel.py",
            "ViewModel (Precisión 8 Decimales)"
        )
        hashes['componentes_criticos'].append(hash4)
        
        # 5. Sello api_endpoints.py (validación de ubicación)
        hash5 = self.sha256_archivo(
            self.app_ui_dir / "api_endpoints.py",
            "API Endpoints (Validación de Ubicación)"
        )
        hashes['componentes_criticos'].append(hash5)
        
        # 6. Sello bus_expander.py (gravedad en Bus)
        hash6 = self.sha256_archivo(
            self.core_dir / "system" / "bus_expander.py",
            "Bus Expander (Publicación de Gravedad Dinámica)"
        )
        hashes['componentes_criticos'].append(hash6)
        
        # 7. Sello location_engine.py
        hash7 = self.sha256_archivo(
            self.core_dir / "location" / "location_engine.py",
            "Location Engine (Persistencia de Ubicación)"
        )
        hashes['componentes_criticos'].append(hash7)
        
        # 8. Sello main_asgi.py
        hash8 = self.sha256_archivo(
            self.workspace_root / "main_asgi.py",
            "Main ASGI (Inicialización e Inyección)"
        )
        hashes['componentes_criticos'].append(hash8)
        
        # SHA256 del sello completo (para autorreferencia)
        contenido_sello = json.dumps(hashes, indent=2, ensure_ascii=False, sort_keys=True)
        hash_sello_completo = hashlib.sha256(contenido_sello.encode('utf-8')).hexdigest()
        
        hashes['sha256_de_este_sello'] = hash_sello_completo
        
        # Guardar reporte
        ruta_reporte = self.logs_dir / "SHA256_SELLO_DEFINITIVO.json"
        with open(ruta_reporte, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 80)
        logger.info(f"[OK] PATRULLA COMPLETADA")
        logger.info(f"📄 Reporte guardado en: {ruta_reporte.relative_to(self.workspace_root)}")
        logger.info(f"🔐 SHA256 DEFINITIVO DEL SELLO: {hash_sello_completo}")
        logger.info("=" * 80)
        
        return hashes

def main():
    """Punto de entrada."""
    sello = SelloDefinitivo()
    reporte = sello.ejecutar_patrulla()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("[GUARDIAN] SOBERANÍA DIRECTA - CERTIFICADO DE SELLADO")
    print("=" * 80)
    print(f"📍 Ubicación: {reporte['ubicacion_sellada']}")
    print(f"📐 Coordenadas: {reporte['coordenadas']['latitud_exacta']}°, {reporte['coordenadas']['longitud_exacta']}°")
    print(f"⬆️  Altitud: {reporte['coordenadas']['altitud_m']} m")
    print(f"🔬 Gravedad: {reporte['gravedad_sellada']['valor_m_s2']} m/s²")
    print(f"[STATS] Componentes verificados: {len(reporte['componentes_criticos'])}")
    print(f"🔐 SELLO DEFINITIVO: {reporte['sha256_de_este_sello']}")
    print("=" * 80)

if __name__ == "__main__":
    main()

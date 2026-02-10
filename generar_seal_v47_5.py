"""
Generador de SHA-256 Seal V47.5
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime

def generar_seal():
    """Genera seal SHA-256 de todo el código V47.5."""
    
    # Buscar todos los archivos críticos
    archivos_criticos = []
    archivos_criticos.extend(Path('.').rglob('*.py'))
    archivos_criticos.extend(Path('.').rglob('*.md'))
    
    # Filtrar archivos temporales
    archivos_filtrados = [
        f for f in archivos_criticos 
        if not any(x in str(f) for x in ['__pycache__', '.venv', 'backups', 'tests', 'logs'])
    ]
    
    # Calcular hashes
    hashes = {}
    total_lineas = 0
    total_bytes = 0
    
    for archivo in sorted(archivos_filtrados):
        try:
            data = archivo.read_bytes()
            hash_sha256 = hashlib.sha256(data).hexdigest()
            hashes[str(archivo)] = hash_sha256[:16]  # Primeros 16 chars
            
            lineas = len(archivo.read_text(encoding='utf-8', errors='ignore').splitlines())
            total_lineas += lineas
            total_bytes += len(data)
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")
    
    # Generar seal global
    hashes_str = json.dumps(hashes, sort_keys=True)
    seal_sha256 = hashlib.sha256(hashes_str.encode()).hexdigest()
    
    seal = {
        'version': 'V47.5 PATRULLA SOBERANA',
        'fecha': datetime.now().isoformat(),
        'archivos_total': len(archivos_filtrados),
        'archivos_python': len([f for f in archivos_filtrados if f.suffix == '.py']),
        'archivos_markdown': len([f for f in archivos_filtrados if f.suffix == '.md']),
        'lineas_codigo_total': total_lineas,
        'bytes_total': total_bytes,
        'sha256_seal': seal_sha256,
        'componentes_criticos': {
            'guardian_25_capas': 'GUARDIAN_25_CAPAS_V47_5.py',
            'capa_22_cortafuegos': 'core/monitoring/cortafuegos_cascada.py',
            'capa_23_recursos': 'core/monitoring/monitor_recursos_auto_limpieza.py',
            'capa_24_integridad': 'core/security/integridad_codigo_sha256.py',
            'capa_25_sanitizacion': 'core/security/sanitizacion_datos_externos.py',
            'fusion_engine': 'core/monitoring/formula_fusion_engine.py',
            'duel_engine': 'core/monitoring/formula_duel_engine.py'
        }
    }
    
    # Guardar seal
    Path('data').mkdir(exist_ok=True)
    seal_file = Path('data/V47_5_SHA256_SEAL.json')
    seal_file.write_text(json.dumps(seal, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"[OK] SHA-256 Seal V47.5 generado:")
    print(f"   Archivos protegidos: {seal['archivos_total']}")
    print(f"   Líneas totales: {seal['lineas_codigo_total']:,}")
    print(f"   Seal: {seal_sha256[:32]}...")
    print(f"   Guardado en: {seal_file}")
    
    return seal

if __name__ == "__main__":
    seal = generar_seal()

"""
[GUARDIAN] CAPA 24: INTEGRIDAD DE CÓDIGO SHA-256 (SELLO DE ORO)

MISIÓN ÚNICA:
Verificar cada hora que NADIE (virus, error de disco, ataque) ha modificado el código.

FILOSOFÍA:
"El Acorazado Argentona debe saber que sus fórmulas son las originales"

NO ES:
- Firewall de red (ya lo tienes en el router)
- Antivirus (Windows Defender lo hace)
- Sandbox (paranoia innecesaria)
- Kill switch geográfico (absurdo)

ES:
- Auditoría horaria de hashes SHA-256
- Rollback automático si detecta modificación
- Registro forense de cambios

CONSUMO: <0.01% CPU
AUTOR: V47.5 SARCÓFAGO CRIPTOGRÁFICO
FECHA: 2026-02-05
"""

import os
import sys
import json
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IntegridadCodigoSHA256:
    """
    Guardián de integridad de código mediante SHA-256.
    
    Verifica cada hora que el código no ha sido modificado.
    """
    
    # Archivos críticos a vigilar
    ARCHIVOS_CRITICOS = [
        # Núcleo de fórmulas
        "core/indices/formulas_indices.py",
        "core/indices/formulas_mejoradas.py",
        "core/indices/formula_validator.py",
        
        # MOS Clustering y Feedback Learning
        "core/learning/mos_clustering_v472.py",
        "core/learning/feedback_learning_v472.py",
        
        # Validadores críticos
        "core/validation/mos_clustering_validator.py",
        "core/learning/feedback_learning_auditor.py",
        
        # Monitorización
        "core/monitoring/centinela_soberano.py",
        "core/monitoring/cortafuegos_cascada.py",
        "core/monitoring/monitor_recursos_auto_limpieza.py",
        
        # Sistema principal
        "main.py",
        "main_asgi.py",
        
        # Self-mod (CRÍTICO - puede modificar código)
        "self_mod_engine.py",
        "evolution_engine.py",
    ]
    
    def __init__(self, workspace_root: Path = None):
        if workspace_root is None:
            workspace_root = Path.cwd()
        
        self.workspace_root = workspace_root
        self.data_dir = workspace_root / "data"
        self.backups_dir = workspace_root / "backups"
        
        self.hashes_file = self.data_dir / "integridad_sha256_hashes.json"
        self.auditoria_file = self.data_dir / "integridad_sha256_auditoria.json"
        
        self.hashes_baseline = self._cargar_baseline()
        self.auditoria = self._cargar_auditoria()
        
        logger.info("[GUARDIAN] Integridad SHA-256 (Sello de Oro) inicializada")
    
    def _cargar_baseline(self) -> Dict[str, str]:
        """Carga baseline de hashes SHA-256."""
        if self.hashes_file.exists():
            with open(self.hashes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _cargar_auditoria(self) -> List[Dict]:
        """Carga auditoría de cambios."""
        if self.auditoria_file.exists():
            with open(self.auditoria_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _guardar_baseline(self):
        """Guarda baseline de hashes."""
        with open(self.hashes_file, 'w', encoding='utf-8') as f:
            json.dump(self.hashes_baseline, f, indent=2, ensure_ascii=False)
    
    def _guardar_auditoria(self):
        """Guarda auditoría de cambios."""
        # Mantener últimas 1000 auditorías
        self.auditoria = self.auditoria[-1000:]
        
        with open(self.auditoria_file, 'w', encoding='utf-8') as f:
            json.dump(self.auditoria, f, indent=2, ensure_ascii=False)
    
    def calcular_sha256(self, archivo: Path) -> Optional[str]:
        """
        Calcula SHA-256 de un archivo.
        
        Args:
            archivo: Path al archivo
            
        Returns:
            Hash SHA-256 en hexadecimal, o None si error
        """
        try:
            sha256 = hashlib.sha256()
            
            with open(archivo, 'rb') as f:
                # Leer en chunks de 64KB
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
            
            return sha256.hexdigest()
        
        except Exception as e:
            logger.error(f"[ERROR] Error calculando SHA-256 de {archivo}: {e}")
            return None
    
    def crear_baseline(self) -> Dict[str, str]:
        """
        Crea baseline inicial de hashes SHA-256.
        
        Returns:
            {
                "archivo_relativo": "hash_sha256",
                ...
            }
        """
        logger.info("🔐 Creando baseline SHA-256 de código crítico...")
        
        hashes = {}
        
        for archivo_rel in self.ARCHIVOS_CRITICOS:
            archivo = self.workspace_root / archivo_rel
            
            if not archivo.exists():
                logger.warning(f"[WARNING] Archivo no existe: {archivo_rel}")
                continue
            
            hash_sha256 = self.calcular_sha256(archivo)
            
            if hash_sha256:
                hashes[archivo_rel] = hash_sha256
                logger.info(f"[OK] {archivo_rel}: {hash_sha256[:16]}...")
        
        self.hashes_baseline = hashes
        self._guardar_baseline()
        
        logger.info(f"🔐 Baseline creado: {len(hashes)} archivos protegidos")
        
        return hashes
    
    def verificar_integridad(self) -> Dict:
        """
        Verifica integridad de código contra baseline.
        
        Returns:
            {
                "estado": "OK|MODIFICADO|ERROR",
                "archivos_modificados": [...],
                "archivos_nuevos": [...],
                "archivos_borrados": [...]
            }
        """
        if not self.hashes_baseline:
            logger.warning("[WARNING] No hay baseline. Creando...")
            self.crear_baseline()
            return {"estado": "OK", "archivos_modificados": [], "archivos_nuevos": [], "archivos_borrados": []}
        
        archivos_modificados = []
        archivos_nuevos = []
        archivos_borrados = []
        
        # Verificar archivos del baseline
        for archivo_rel, hash_original in self.hashes_baseline.items():
            archivo = self.workspace_root / archivo_rel
            
            if not archivo.exists():
                archivos_borrados.append(archivo_rel)
                logger.critical(f"[CRITICAL] ARCHIVO BORRADO: {archivo_rel}")
                continue
            
            hash_actual = self.calcular_sha256(archivo)
            
            if hash_actual != hash_original:
                archivos_modificados.append({
                    "archivo": archivo_rel,
                    "hash_original": hash_original[:16] + "...",
                    "hash_actual": hash_actual[:16] + "..."
                })
                logger.critical(
                    f"[CRITICAL] MODIFICACIÓN DETECTADA: {archivo_rel}\n"
                    f"   Original: {hash_original[:16]}...\n"
                    f"   Actual:   {hash_actual[:16]}..."
                )
        
        # Detectar archivos nuevos (en ARCHIVOS_CRITICOS pero no en baseline)
        for archivo_rel in self.ARCHIVOS_CRITICOS:
            if archivo_rel not in self.hashes_baseline:
                archivo = self.workspace_root / archivo_rel
                if archivo.exists():
                    archivos_nuevos.append(archivo_rel)
                    logger.warning(f"[WARNING] ARCHIVO NUEVO: {archivo_rel}")
        
        # Determinar estado
        if archivos_modificados or archivos_borrados:
            estado = "MODIFICADO"
        elif archivos_nuevos:
            estado = "OK"  # Nuevos archivos son OK si no hay modificaciones
        else:
            estado = "OK"
        
        # Registrar auditoría
        if estado == "MODIFICADO":
            self._registrar_auditoria(archivos_modificados, archivos_borrados)
        
        return {
            "estado": estado,
            "archivos_modificados": archivos_modificados,
            "archivos_nuevos": archivos_nuevos,
            "archivos_borrados": archivos_borrados,
            "timestamp": datetime.now().isoformat()
        }
    
    def _registrar_auditoria(self, modificados: List, borrados: List):
        """Registra cambios en auditoría forense."""
        self.auditoria.append({
            "timestamp": datetime.now().isoformat(),
            "archivos_modificados": modificados,
            "archivos_borrados": borrados,
            "accion": "ALERTA_MODIFICACION"
        })
        
        self._guardar_auditoria()
    
    def rollback_automatico(self, archivo_rel: str) -> bool:
        """
        Rollback automático de archivo modificado desde último backup.
        
        Args:
            archivo_rel: Path relativo del archivo
            
        Returns:
            True si rollback exitoso, False si error
        """
        # Buscar último backup
        backups = sorted(
            [d for d in self.backups_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not backups:
            logger.error("[ERROR] No hay backups para rollback")
            return False
        
        ultimo_backup = backups[0]
        archivo_backup = ultimo_backup / archivo_rel
        
        if not archivo_backup.exists():
            logger.error(f"[ERROR] Archivo no existe en backup: {archivo_rel}")
            return False
        
        # Hacer rollback
        archivo_actual = self.workspace_root / archivo_rel
        
        try:
            # Backup del archivo corrupto
            archivo_corrupto = self.workspace_root / f"{archivo_rel}.CORRUPTO.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(archivo_actual, archivo_corrupto)
            
            # Restaurar desde backup
            shutil.copy2(archivo_backup, archivo_actual)
            
            logger.info(f"[OK] Rollback exitoso: {archivo_rel}")
            logger.info(f"   Corrupto guardado en: {archivo_corrupto}")
            
            # Registrar auditoría
            self.auditoria.append({
                "timestamp": datetime.now().isoformat(),
                "archivo": archivo_rel,
                "accion": "ROLLBACK_AUTOMATICO",
                "backup_origen": str(ultimo_backup.name),
                "archivo_corrupto": str(archivo_corrupto)
            })
            self._guardar_auditoria()
            
            return True
        
        except Exception as e:
            logger.error(f"[ERROR] Error en rollback: {e}")
            return False
    
    def actualizar_baseline(self, archivo_rel: str = None):
        """
        Actualiza baseline tras modificación autorizada.
        
        Args:
            archivo_rel: Archivo específico, o None para todos
        """
        if archivo_rel:
            # Actualizar solo un archivo
            archivo = self.workspace_root / archivo_rel
            
            if archivo.exists():
                hash_nuevo = self.calcular_sha256(archivo)
                self.hashes_baseline[archivo_rel] = hash_nuevo
                
                logger.info(f"🔐 Baseline actualizado: {archivo_rel}")
                
                # Registrar auditoría
                self.auditoria.append({
                    "timestamp": datetime.now().isoformat(),
                    "archivo": archivo_rel,
                    "accion": "BASELINE_ACTUALIZADO",
                    "hash_nuevo": hash_nuevo[:16] + "..."
                })
        else:
            # Recrear baseline completo
            self.crear_baseline()
            
            logger.info("🔐 Baseline completo actualizado")
        
        self._guardar_baseline()
        self._guardar_auditoria()
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas de integridad.
        
        Returns:
            {
                "archivos_protegidos": 15,
                "auditorias_total": 45,
                "modificaciones_detectadas": 2,
                "rollbacks_ejecutados": 1
            }
        """
        modificaciones = sum(1 for a in self.auditoria if a.get("accion") == "ALERTA_MODIFICACION")
        rollbacks = sum(1 for a in self.auditoria if a.get("accion") == "ROLLBACK_AUTOMATICO")
        
        return {
            "archivos_protegidos": len(self.hashes_baseline),
            "auditorias_total": len(self.auditoria),
            "modificaciones_detectadas": modificaciones,
            "rollbacks_ejecutados": rollbacks,
            "ultima_verificacion": self.auditoria[-1]["timestamp"] if self.auditoria else None
        }


# ============================================================================
# INTEGRACIÓN CON SISTEMA PRINCIPAL
# ============================================================================

def integrar_integridad_en_sistema():
    """
    Ejemplo de integración en main_asgi.py.
    
    ```python
    # En main_asgi.py
    from core.security.integridad_codigo_sha256 import IntegridadCodigoSHA256
    
    integridad = IntegridadCodigoSHA256()
    
    # Crear baseline inicial (solo primera vez)
    if not integridad.hashes_baseline:
        integridad.crear_baseline()
    
    # En loop principal (cada 1 hora)
    if time.time() - ultima_verificacion_integridad > 3600:
        resultado = integridad.verificar_integridad()
        
        if resultado["estado"] == "MODIFICADO":
            logger.critical("[CRITICAL] CÓDIGO MODIFICADO - Ejecutando rollback automático")
            
            for archivo_info in resultado["archivos_modificados"]:
                integridad.rollback_automatico(archivo_info["archivo"])
            
            # Reiniciar sistema para cargar código limpio
            os.execv(sys.executable, ['python'] + sys.argv)
        
        ultima_verificacion_integridad = time.time()
    ```
    """
    pass


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    integridad = IntegridadCodigoSHA256()
    
    # Crear baseline
    print("\n🔐 Creando baseline SHA-256...")
    hashes = integridad.crear_baseline()
    print(f"[OK] {len(hashes)} archivos protegidos")
    
    # Verificar integridad
    print("\n[BUSCAR] Verificando integridad...")
    resultado = integridad.verificar_integridad()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Estadísticas
    print("\n📈 Estadísticas:")
    stats = integridad.obtener_estadisticas()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

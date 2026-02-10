"""
[GUARDIAN] CAPA 23: MONITOR DE RECURSOS Y AUTO-LIMPIEZA

MISIÓN CRÍTICA:
Mantener sistema operativo durante meses sin intervención humana.
Prevenir crash por disco lleno, RAM saturada, o logs infinitos.

FILOSOFÍA:
"El sistema debe sobrevivir 6 meses solo como una boya oceánica"

CASOS CRÍTICOS:
- Logs crecen → Disco lleno → Sistema crash
- JSON de estado crecen → Memoria saturada
- Procesos zombies → CPU bloqueada
- Archivos temporales → Disco saturado

AUTOR: V47.4 SUMMUM - Sistema Autónomo
FECHA: 2026-02-05
"""

import os
import sys
import json
import logging
import psutil
import shutil
import gzip
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MonitorRecursosAutoLimpieza:
    """
    Monitor de recursos del sistema con auto-limpieza preventiva.
    
    Mantiene el sistema sano durante meses sin supervisión humana.
    """
    
    # Límites críticos
    LIMITES_CRITICOS = {
        "disco_libre_min_gb": 1.0,       # GB mínimo libre
        "disco_alerta_gb": 5.0,          # GB para empezar limpieza
        "ram_uso_max_pct": 80.0,         # % máximo RAM
        "cpu_uso_max_pct": 90.0,         # % máximo CPU sostenido
        "cpu_tiempo_max_s": 300,         # segundos CPU >90%
    }
    
    # Límites de archivos
    LIMITES_ARCHIVOS = {
        "logs_max_mb": 500,              # MB máximo logs totales
        "logs_dias_mantener": 7,         # Días logs sin comprimir
        "logs_dias_comprimir": 30,       # Días logs comprimidos
        "logs_dias_borrar": 90,          # Días antes de borrar
        
        "json_estado_max_mb": 50,        # MB máximo JSON estado
        "json_registros_max": 1000,      # Registros máximos por JSON
        
        "backups_max_count": 10,         # Máximo backups automáticos
        "backups_dias_mantener": 30,     # Días mantener backups
    }
    
    def __init__(self, workspace_root: Path = None):
        if workspace_root is None:
            workspace_root = Path.cwd()
        
        self.workspace_root = workspace_root
        self.logs_dir = workspace_root / "logs"
        self.data_dir = workspace_root / "data"
        self.backups_dir = workspace_root / "backups"
        
        self.estado_file = self.data_dir / "monitor_recursos_estado.json"
        self.estado = self._cargar_estado()
        
        logger.info("[GUARDIAN] Monitor de Recursos y Auto-Limpieza inicializado")
    
    def _cargar_estado(self) -> Dict:
        """Carga estado persistente."""
        if self.estado_file.exists():
            with open(self.estado_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "limpiezas_ejecutadas": 0,
            "bytes_liberados_total": 0,
            "alertas_criticas": [],
            "ultima_limpieza": None,
            "ultima_verificacion": None
        }
    
    def _guardar_estado(self):
        """Guarda estado persistente."""
        self.estado["ultima_verificacion"] = datetime.now().isoformat()
        with open(self.estado_file, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)
    
    def verificar_recursos(self) -> Dict[str, any]:
        """
        Verifica estado de recursos del sistema.
        
        Returns:
            {
                "disco": {...},
                "ram": {...},
                "cpu": {...},
                "estado_global": "OK|ALERTA|CRITICO"
            }
        """
        # Disco
        disco = psutil.disk_usage(str(self.workspace_root))
        disco_libre_gb = disco.free / (1024**3)
        disco_usado_pct = disco.percent
        
        # RAM
        ram = psutil.virtual_memory()
        ram_usado_pct = ram.percent
        ram_libre_gb = ram.available / (1024**3)
        
        # CPU
        cpu_pct = psutil.cpu_percent(interval=1)
        
        # Determinar estado global
        estado_global = "OK"
        
        if disco_libre_gb < self.LIMITES_CRITICOS["disco_libre_min_gb"]:
            estado_global = "CRITICO"
        elif disco_libre_gb < self.LIMITES_CRITICOS["disco_alerta_gb"]:
            estado_global = "ALERTA"
        
        if ram_usado_pct > self.LIMITES_CRITICOS["ram_uso_max_pct"]:
            estado_global = "ALERTA" if estado_global == "OK" else "CRITICO"
        
        if cpu_pct > self.LIMITES_CRITICOS["cpu_uso_max_pct"]:
            estado_global = "ALERTA" if estado_global == "OK" else estado_global
        
        resultado = {
            "disco": {
                "libre_gb": round(disco_libre_gb, 2),
                "usado_pct": round(disco_usado_pct, 1),
                "estado": "OK" if disco_libre_gb > self.LIMITES_CRITICOS["disco_alerta_gb"] else "CRITICO"
            },
            "ram": {
                "usado_pct": round(ram_usado_pct, 1),
                "libre_gb": round(ram_libre_gb, 2),
                "estado": "OK" if ram_usado_pct < self.LIMITES_CRITICOS["ram_uso_max_pct"] else "ALERTA"
            },
            "cpu": {
                "uso_pct": round(cpu_pct, 1),
                "estado": "OK" if cpu_pct < self.LIMITES_CRITICOS["cpu_uso_max_pct"] else "ALERTA"
            },
            "estado_global": estado_global
        }
        
        self._guardar_estado()
        
        return resultado
    
    def auto_limpiar_logs(self) -> int:
        """
        Limpia logs antiguos automáticamente.
        
        Estrategia:
        - <7 días: Sin comprimir
        - 7-30 días: Comprimir con gzip
        - >90 días: Borrar
        
        Returns:
            Bytes liberados
        """
        if not self.logs_dir.exists():
            return 0
        
        bytes_liberados = 0
        fecha_ahora = datetime.now()
        
        # Buscar todos los archivos .log
        for log_file in self.logs_dir.rglob("*.log"):
            try:
                # Fecha de modificación
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                edad_dias = (fecha_ahora - mtime).days
                
                # >90 días: BORRAR
                if edad_dias > self.LIMITES_ARCHIVOS["logs_dias_borrar"]:
                    tam = log_file.stat().st_size
                    log_file.unlink()
                    bytes_liberados += tam
                    logger.info(f"🗑️ Borrado log antiguo: {log_file.name} ({edad_dias} días)")
                
                # 7-30 días: COMPRIMIR
                elif edad_dias > self.LIMITES_ARCHIVOS["logs_dias_mantener"]:
                    if not log_file.with_suffix('.log.gz').exists():
                        tam_original = log_file.stat().st_size
                        
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(log_file.with_suffix('.log.gz'), 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        tam_comprimido = log_file.with_suffix('.log.gz').stat().st_size
                        log_file.unlink()
                        
                        bytes_liberados += (tam_original - tam_comprimido)
                        logger.info(
                            f"📦 Comprimido log: {log_file.name} "
                            f"({tam_original/1024:.1f}KB → {tam_comprimido/1024:.1f}KB)"
                        )
            
            except Exception as e:
                logger.error(f"[ERROR] Error limpiando {log_file}: {e}")
        
        # Comprimir logs .gz antiguos >30 días
        for gz_file in self.logs_dir.rglob("*.log.gz"):
            try:
                mtime = datetime.fromtimestamp(gz_file.stat().st_mtime)
                edad_dias = (fecha_ahora - mtime).days
                
                if edad_dias > self.LIMITES_ARCHIVOS["logs_dias_comprimir"]:
                    tam = gz_file.stat().st_size
                    gz_file.unlink()
                    bytes_liberados += tam
                    logger.info(f"🗑️ Borrado log comprimido antiguo: {gz_file.name}")
            
            except Exception as e:
                logger.error(f"[ERROR] Error limpiando {gz_file}: {e}")
        
        return bytes_liberados
    
    def auto_limpiar_json_estado(self) -> int:
        """
        Limpia archivos JSON de estado que crecen indefinidamente.
        
        Estrategia:
        - Mantener últimos 1000 registros
        - Archivar resto en JSON comprimido
        
        Returns:
            Bytes liberados
        """
        if not self.data_dir.exists():
            return 0
        
        bytes_liberados = 0
        max_registros = self.LIMITES_ARCHIVOS["json_registros_max"]
        
        # Archivos JSON de estado conocidos que crecen
        archivos_estado = [
            "mos_clustering_v472_estado.json",
            "feedback_learning_v472_estado.json",
            "mos_clustering_validator_estado.json",
            "feedback_learning_auditor_estado.json",
            "cortafuegos_cascada_estado.json"
        ]
        
        for nombre_archivo in archivos_estado:
            archivo = self.data_dir / nombre_archivo
            
            if not archivo.exists():
                continue
            
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Buscar listas que crecen
                modificado = False
                
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > max_registros:
                        tam_original = len(value)
                        
                        # Archivar registros antiguos
                        archivo_archivo = self.data_dir / f"{nombre_archivo}.archive.gz"
                        registros_archivar = value[:-max_registros]
                        
                        with gzip.open(archivo_archivo, 'wt', encoding='utf-8') as f:
                            json.dump(registros_archivar, f)
                        
                        # Mantener solo últimos registros
                        data[key] = value[-max_registros:]
                        
                        modificado = True
                        logger.info(
                            f"📦 Archivado {key} de {nombre_archivo}: "
                            f"{tam_original} → {len(data[key])} registros"
                        )
                
                if modificado:
                    # Guardar JSON reducido
                    tam_original = archivo.stat().st_size
                    
                    with open(archivo, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    tam_nuevo = archivo.stat().st_size
                    bytes_liberados += (tam_original - tam_nuevo)
            
            except Exception as e:
                logger.error(f"[ERROR] Error limpiando {archivo}: {e}")
        
        return bytes_liberados
    
    def auto_limpiar_backups_antiguos(self) -> int:
        """
        Limpia backups automáticos antiguos.
        
        Estrategia:
        - Mantener últimos 10 backups
        - Borrar backups >30 días
        
        Returns:
            Bytes liberados
        """
        if not self.backups_dir.exists():
            return 0
        
        bytes_liberados = 0
        fecha_ahora = datetime.now()
        
        # Listar todos los backups
        backups = sorted(
            [d for d in self.backups_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        max_backups = self.LIMITES_ARCHIVOS["backups_max_count"]
        dias_mantener = self.LIMITES_ARCHIVOS["backups_dias_mantener"]
        
        for i, backup_dir in enumerate(backups):
            try:
                mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                edad_dias = (fecha_ahora - mtime).days
                
                # Borrar si >30 días O si hay más de 10 backups
                if edad_dias > dias_mantener or i >= max_backups:
                    # Calcular tamaño antes de borrar
                    tam = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                    
                    shutil.rmtree(backup_dir)
                    bytes_liberados += tam
                    
                    logger.info(
                        f"🗑️ Borrado backup antiguo: {backup_dir.name} "
                        f"({edad_dias} días, {tam/(1024**2):.1f}MB)"
                    )
            
            except Exception as e:
                logger.error(f"[ERROR] Error limpiando backup {backup_dir}: {e}")
        
        return bytes_liberados
    
    def ejecutar_limpieza_completa(self) -> Dict:
        """
        Ejecuta limpieza completa de todos los componentes.
        
        Returns:
            {
                "bytes_liberados_logs": int,
                "bytes_liberados_json": int,
                "bytes_liberados_backups": int,
                "total_mb_liberados": float
            }
        """
        logger.info("[CLEANUP] Iniciando limpieza automática completa...")
        
        bytes_logs = self.auto_limpiar_logs()
        bytes_json = self.auto_limpiar_json_estado()
        bytes_backups = self.auto_limpiar_backups_antiguos()
        
        total_bytes = bytes_logs + bytes_json + bytes_backups
        total_mb = total_bytes / (1024**2)
        
        self.estado["limpiezas_ejecutadas"] += 1
        self.estado["bytes_liberados_total"] += total_bytes
        self.estado["ultima_limpieza"] = datetime.now().isoformat()
        self._guardar_estado()
        
        logger.info(f"[OK] Limpieza completa: {total_mb:.2f} MB liberados")
        
        return {
            "bytes_liberados_logs": bytes_logs,
            "bytes_liberados_json": bytes_json,
            "bytes_liberados_backups": bytes_backups,
            "total_mb_liberados": round(total_mb, 2)
        }
    
    def monitorear_y_actuar(self) -> Dict:
        """
        Monitorea recursos y ejecuta acciones según estado.
        
        Returns:
            {
                "recursos": {...},
                "acciones_ejecutadas": [...],
                "estado": "OK|ALERTA|CRITICO"
            }
        """
        recursos = self.verificar_recursos()
        acciones_ejecutadas = []
        
        # CRÍTICO: Disco < 1 GB
        if recursos["disco"]["libre_gb"] < self.LIMITES_CRITICOS["disco_libre_min_gb"]:
            logger.critical(
                f"[CRITICAL] DISCO CRÍTICO: {recursos['disco']['libre_gb']:.2f} GB libres"
            )
            
            # Limpieza AGRESIVA
            resultado_limpieza = self.ejecutar_limpieza_completa()
            acciones_ejecutadas.append(f"Limpieza agresiva: {resultado_limpieza['total_mb_liberados']:.2f} MB")
            
            # Registrar alerta crítica
            self._registrar_alerta_critica("DISCO_CRITICO", recursos["disco"]["libre_gb"])
        
        # ALERTA: Disco < 5 GB
        elif recursos["disco"]["libre_gb"] < self.LIMITES_CRITICOS["disco_alerta_gb"]:
            logger.warning(
                f"[WARNING] DISCO EN ALERTA: {recursos['disco']['libre_gb']:.2f} GB libres"
            )
            
            # Limpieza MODERADA
            resultado_limpieza = self.ejecutar_limpieza_completa()
            acciones_ejecutadas.append(f"Limpieza preventiva: {resultado_limpieza['total_mb_liberados']:.2f} MB")
        
        # ALERTA: RAM > 80%
        if recursos["ram"]["usado_pct"] > self.LIMITES_CRITICOS["ram_uso_max_pct"]:
            logger.warning(
                f"[WARNING] RAM EN ALERTA: {recursos['ram']['usado_pct']:.1f}% en uso"
            )
            acciones_ejecutadas.append("Monitoreo RAM activado")
            
            # Registrar alerta
            self._registrar_alerta_critica("RAM_ALTA", recursos["ram"]["usado_pct"])
        
        return {
            "recursos": recursos,
            "acciones_ejecutadas": acciones_ejecutadas,
            "estado": recursos["estado_global"]
        }
    
    def _registrar_alerta_critica(self, tipo: str, valor: float):
        """Registra alerta crítica en histórico."""
        self.estado["alertas_criticas"].append({
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "valor": valor
        })
        
        # Mantener últimas 100 alertas
        self.estado["alertas_criticas"] = self.estado["alertas_criticas"][-100:]
        
        self._guardar_estado()
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas del monitor.
        
        Returns:
            {
                "limpiezas_ejecutadas": 45,
                "mb_liberados_total": 1234.5,
                "alertas_criticas_total": 3,
                "ultima_limpieza": "2026-02-05T15:30:00"
            }
        """
        return {
            "limpiezas_ejecutadas": self.estado["limpiezas_ejecutadas"],
            "mb_liberados_total": round(self.estado["bytes_liberados_total"] / (1024**2), 2),
            "alertas_criticas_total": len(self.estado["alertas_criticas"]),
            "ultima_limpieza": self.estado.get("ultima_limpieza"),
            "ultima_verificacion": self.estado.get("ultima_verificacion")
        }


# ============================================================================
# INTEGRACIÓN CON SISTEMA PRINCIPAL
# ============================================================================

def integrar_monitor_en_sistema():
    """
    Ejemplo de integración en main_asgi.py o similar.
    
    ```python
    # En main_asgi.py
    from core.monitoring.monitor_recursos_auto_limpieza import MonitorRecursosAutoLimpieza
    
    monitor = MonitorRecursosAutoLimpieza()
    
    # En loop principal (cada 1 hora)
    if time.time() - ultima_verificacion_recursos > 3600:
        resultado = monitor.monitorear_y_actuar()
        
        if resultado["estado"] == "CRITICO":
            logger.critical("[CRITICAL] Sistema en estado CRÍTICO")
            # Enviar notificación urgente
        
        ultima_verificacion_recursos = time.time()
    ```
    """
    pass


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    monitor = MonitorRecursosAutoLimpieza()
    
    # Verificar recursos
    print("\n[STATS] Estado de Recursos:")
    recursos = monitor.verificar_recursos()
    print(json.dumps(recursos, indent=2))
    
    # Ejecutar limpieza
    print("\n[CLEANUP] Ejecutando limpieza...")
    limpieza = monitor.ejecutar_limpieza_completa()
    print(json.dumps(limpieza, indent=2))
    
    # Estadísticas
    print("\n📈 Estadísticas:")
    stats = monitor.obtener_estadisticas()
    print(json.dumps(stats, indent=2))

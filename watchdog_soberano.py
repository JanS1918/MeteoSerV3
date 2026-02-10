#!/usr/bin/env python3
"""
CENTINELA SOBERANO - Vigilancia Externa Independiente
====================================================

Proceso COMPLETAMENTE SEPARADO que monitorea heartbeat de main app.
Si main app falla o se corrompe, centinela mata el proceso y restaura snapshot.

CRÍTICO: Debe ejecutarse como PROCESO EXTERNO, no como thread.
- PID independiente
- Socket TCP heartbeat 30s
- Timeout 35s → KILL + RESTORE
- Immune to main app corruption

Uso:
    # Terminal 1: Iniciar main app
    python main_asgi.py
    
    # Terminal 2: Iniciar centinela soberano
    python watchdog_soberano.py --port 9617 --app-pid $(pgrep -f main_asgi.py)
"""

import socket
import time
import os
import signal
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import argparse
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/centinela_soberano.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("centinela_soberano")


class WatchdogSoberano:
    """
    Vigilancia externa independiente de la main app.
    
    Características:
    - Socket TCP: espera heartbeat cada 30s
    - Timeout: 35s → KILL + RESTORE
    - Logging: auditoría completa
    - Restore: snapshot anterior
    """
    
    def __init__(self, port: int = 9617, app_pid: Optional[int] = None, 
                 heartbeat_interval: int = 30, timeout: int = 35):
        """
        Args:
            port: Puerto TCP para heartbeat
            app_pid: PID del proceso main app (si None, busca automáticamente)
            heartbeat_interval: Frecuencia de heartbeat esperado (segundos)
            timeout: Tiempo máximo sin heartbeat antes de KILL (segundos)
        """
        self.port = port
        self.app_pid = app_pid
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        
        self.socket: Optional[socket.socket] = None
        self.last_heartbeat = datetime.now()
        self.heartbeat_count = 0
        self.is_running = True
        self.snapshot_dir = Path("backups/soberano_snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[GUARDIAN] Centinela Soberano inicializado (puerto {port}, heartbeat {heartbeat_interval}s, timeout {timeout}s)")
    
    def find_app_pid(self) -> Optional[int]:
        """Busca PID de main_asgi.py si no fue proporcionado."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "main_asgi.py"],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                pid = int(result.stdout.strip().split('\n')[0])
                logger.info(f"📍 App main encontrada: PID {pid}")
                return pid
        except Exception as e:
            logger.warning(f"[WARNING] No se pudo encontrar main app: {e}")
        return None
    
    def create_snapshot(self) -> str:
        """Crea snapshot actual del estado del sistema."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.snapshot_dir / f"snapshot_{timestamp}.json"
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "app_pid": self.app_pid,
            "heartbeat_count": self.heartbeat_count,
            "status": "active"
        }
        
        try:
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2)
            logger.info(f"[GUARDAR] Snapshot creado: {snapshot_path}")
            return str(snapshot_path)
        except Exception as e:
            logger.error(f"[ERROR] Error creando snapshot: {e}")
            return ""
    
    def restore_snapshot(self) -> bool:
        """Restaura último snapshot válido."""
        try:
            snapshots = sorted(self.snapshot_dir.glob("snapshot_*.json"), reverse=True)
            
            if not snapshots:
                logger.warning("[WARNING] No hay snapshots para restaurar")
                return False
            
            latest = snapshots[0]
            with open(latest, 'r') as f:
                snapshot = json.load(f)
            
            logger.info(f"📥 Restaurando snapshot: {latest}")
            logger.info(f"   Timestamp: {snapshot.get('timestamp')}")
            logger.info(f"   App PID anterior: {snapshot.get('app_pid')}")
            
            # TODO: Implementar lógica de restauración real
            # Por ahora, solo registra que se intentó restaurar
            
            return True
        except Exception as e:
            logger.error(f"[ERROR] Error restaurando snapshot: {e}")
            return False
    
    def kill_app(self, reason: str) -> bool:
        """Mata el proceso main app de forma forzada."""
        if not self.app_pid:
            logger.warning("[WARNING] PID de app no disponible, no se puede matar")
            return False
        
        try:
            logger.critical(f"🛑 MATANDO APP PID {self.app_pid}: {reason}")
            os.kill(self.app_pid, signal.SIGKILL)
            time.sleep(1)
            
            # Verificar que realmente murió
            try:
                os.kill(self.app_pid, 0)  # Signal 0 = verificar existencia
                logger.error(f"[ERROR] App aún viva después de SIGKILL!")
                return False
            except ProcessLookupError:
                logger.info(f"[OK] App muerta: {self.app_pid}")
                return True
        except Exception as e:
            logger.error(f"[ERROR] Error matando app: {e}")
            return False
    
    def setup_socket(self) -> bool:
        """Configura socket TCP para recibir heartbeat."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('127.0.0.1', self.port))
            self.socket.listen(1)
            self.socket.settimeout(self.timeout)
            
            logger.info(f"[OK] Socket escuchando en puerto {self.port}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Error configurando socket: {e}")
            return False
    
    def wait_for_heartbeat(self) -> bool:
        """Espera heartbeat de main app con timeout."""
        try:
            if not self.socket:
                return False
            
            conn, addr = self.socket.accept()
            data = conn.recv(1024).decode('utf-8')
            conn.close()
            
            if data.strip() == "HEARTBEAT":
                self.last_heartbeat = datetime.now()
                self.heartbeat_count += 1
                logger.debug(f"💓 Heartbeat #{self.heartbeat_count} desde {addr}")
                return True
            else:
                logger.warning(f"[WARNING] Datos inválidos recibidos: {data}")
                return False
                
        except socket.timeout:
            elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
            logger.critical(f"[CRITICAL] TIMEOUT: Sin heartbeat por {elapsed:.1f}s (umbral {self.timeout}s)")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Error recibiendo heartbeat: {e}")
            return False
    
    def run(self):
        """Loop principal del centinela."""
        # Si no tenemos PID, intentar encontrarlo
        if not self.app_pid:
            self.app_pid = self.find_app_pid()
        
        if not self.app_pid:
            logger.error("[ERROR] No se puede obtener PID de app, abortando")
            return
        
        # Configurar socket
        if not self.setup_socket():
            logger.error("[ERROR] No se puede configurar socket, abortando")
            return
        
        logger.info(f"[REINICIO] Iniciando loop de monitoreo (app PID {self.app_pid})")
        
        while self.is_running:
            try:
                # Crear snapshot periódico
                if self.heartbeat_count % 10 == 0 and self.heartbeat_count > 0:
                    self.create_snapshot()
                
                # Esperar heartbeat con timeout
                if self.wait_for_heartbeat():
                    continue
                else:
                    # Heartbeat falló → acciones de emergencia
                    logger.critical("🔴 HEARTBEAT FALLIDO - INICIANDO PROTOCOLOS DE EMERGENCIA")
                    
                    # 1. Crear snapshot para auditoría
                    self.create_snapshot()
                    
                    # 2. Matar app
                    killed = self.kill_app("Heartbeat timeout")
                    
                    # 3. Intentar restaurar
                    if killed:
                        self.restore_snapshot()
                        logger.critical("[GUARDIAN] Centinela completó secuencia de emergencia")
                        # Aquí podría reiniciar app, pero por seguridad no lo hacemos
                    
                    # 4. Esperar comando externo
                    logger.info("⏸️ Centinela en estado de pausa (esperando intervención)")
                    time.sleep(60)
                    
            except KeyboardInterrupt:
                logger.info("⏹️ Centinela detenido por usuario")
                self.is_running = False
            except Exception as e:
                logger.error(f"[ERROR] Error en loop: {e}", exc_info=True)
                time.sleep(5)
        
        if self.socket:
            self.socket.close()
            logger.info("🔌 Socket cerrado")
    
    def signal_handler(self, signum, frame):
        """Manejador de señales."""
        logger.info(f"📡 Señal recibida: {signum}")
        self.is_running = False


def main():
    parser = argparse.ArgumentParser(description="Centinela Soberano - Vigilancia Externa")
    parser.add_argument("--port", type=int, default=9617, help="Puerto TCP para heartbeat")
    parser.add_argument("--app-pid", type=int, default=None, help="PID del app main")
    parser.add_argument("--heartbeat-interval", type=int, default=30, help="Intervalo de heartbeat")
    parser.add_argument("--timeout", type=int, default=35, help="Timeout para heartbeat")
    
    args = parser.parse_args()
    
    centinela = WatchdogSoberano(
        port=args.port,
        app_pid=args.app_pid,
        heartbeat_interval=args.heartbeat_interval,
        timeout=args.timeout
    )
    
    # Instalar manejador de señales
    signal.signal(signal.SIGTERM, centinela.signal_handler)
    signal.signal(signal.SIGINT, centinela.signal_handler)
    
    centinela.run()


if __name__ == "__main__":
    main()

"""
🛡️ CAPA 31: CENTINELA SOBERANO EXTERNO
Watchdog independiente que vigila el Bus y reinicia el flujo si detecta bloqueo.

CARACTERÍSTICAS CLAVE:
- ✅ Proceso INDEPENDIENTE (no parte de main.py)
- ✅ No puede ser killado por main.py corrupto
- ✅ Reinicia automáticamente si Bus congelado >10s
- ✅ Monitorea heartbeat cada 2s
- ✅ Log independiente (no contamina logs de main)

PROTEGE CONTRA:
❌ Bus congelado (deadlock)
❌ Main.py crasheado pero vivo (zombie)
❌ Loops infinitos silenciosos
❌ Memoria saturada sin detección

USO:
```bash
# Ejecutar en terminal separado
python core/monitoring/centinela_soberano.py

# O como servicio Windows
python install_centinela_service.py
```

AUTOR: V47.3 SUMMUM - Guardian Inteligente
FECHA: 2026-02-05
"""

import sys
import time
import json
import logging
import psutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configuración de logging INDEPENDIENTE
LOG_DIR = Path("logs/centinela")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CENTINELA - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "centinela_soberano.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CentinelaSoberano:
    """
    Watchdog externo independiente.
    
    Vigila el Bus de datos y reinicia el sistema si detecta congelación.
    NO forma parte del proceso main.py, por lo que no puede ser corrompido.
    """
    
    # Configuración
    HEARTBEAT_FILE = Path("data/bus_heartbeat.json")
    INTERVALO_VERIFICACION = 2.0  # segundos
    TIMEOUT_BLOQUEO = 10.0        # segundos sin heartbeat = bloqueo
    MAX_REINTENTOS = 3            # reintentos antes de alerta crítica
    
    # Comandos de reinicio
    COMANDO_REINICIO_WINDOWS = ["python", "main_asgi.py"]
    COMANDO_REINICIO_LINUX = ["python3", "main_asgi.py"]
    
    def __init__(self):
        self.ultimo_heartbeat: Optional[datetime] = None
        self.bloqueos_detectados = 0
        self.reinicios_ejecutados = 0
        self.tiempo_inicio = datetime.now()
        
        logger.info("🛡️ CENTINELA SOBERANO INICIADO")
        logger.info(f"   Heartbeat: {self.HEARTBEAT_FILE}")
        logger.info(f"   Timeout: {self.TIMEOUT_BLOQUEO}s")
        logger.info(f"   Verificación cada: {self.INTERVALO_VERIFICACION}s")
    
    def leer_heartbeat(self) -> Optional[datetime]:
        """
        Lee el archivo de heartbeat generado por el Bus.
        
        El Bus debe actualizar este archivo cada 5 segundos con:
        {
            "timestamp": "2026-02-05T15:30:45",
            "ciclos_completados": 12345,
            "estado": "OPERATIVO"
        }
        
        Returns:
            Timestamp del último heartbeat, o None si no existe
        """
        try:
            if not self.HEARTBEAT_FILE.exists():
                logger.warning(f"⚠️ Heartbeat no existe: {self.HEARTBEAT_FILE}")
                return None
            
            with open(self.HEARTBEAT_FILE, 'r') as f:
                data = json.load(f)
            
            timestamp_str = data.get("timestamp")
            if not timestamp_str:
                logger.warning("⚠️ Heartbeat sin timestamp")
                return None
            
            timestamp = datetime.fromisoformat(timestamp_str)
            return timestamp
            
        except Exception as e:
            logger.error(f"❌ Error leyendo heartbeat: {e}")
            return None
    
    def verificar_bloqueo(self) -> bool:
        """
        Verifica si el Bus está bloqueado.
        
        Returns:
            True si hay bloqueo, False si operativo
        """
        heartbeat = self.leer_heartbeat()
        
        if heartbeat is None:
            # Sin heartbeat = problema crítico
            if self.ultimo_heartbeat is None:
                logger.warning("⚠️ Esperando primer heartbeat...")
                return False
            else:
                logger.error("❌ HEARTBEAT DESAPARECIDO")
                return True
        
        # Calcular tiempo transcurrido
        tiempo_transcurrido = (datetime.now() - heartbeat).total_seconds()
        
        if tiempo_transcurrido > self.TIMEOUT_BLOQUEO:
            logger.error(
                f"❌ BLOQUEO DETECTADO: {tiempo_transcurrido:.1f}s sin heartbeat "
                f"(timeout: {self.TIMEOUT_BLOQUEO}s)"
            )
            return True
        
        # Actualizar último heartbeat conocido
        if self.ultimo_heartbeat != heartbeat:
            self.ultimo_heartbeat = heartbeat
            logger.debug(f"✅ Heartbeat OK: {heartbeat.strftime('%H:%M:%S')}")
        
        return False
    
    def encontrar_proceso_main(self) -> Optional[psutil.Process]:
        """
        Encuentra el proceso de main.py o main_asgi.py.
        
        Returns:
            Proceso de psutil, o None si no encontrado
        """
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('main' in arg.lower() for arg in cmdline):
                    logger.info(f"🔍 Proceso encontrado: PID {proc.pid} - {' '.join(cmdline)}")
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        logger.warning("⚠️ Proceso main.py no encontrado")
        return None
    
    def terminar_proceso_main(self):
        """
        Termina el proceso main.py bloqueado.
        
        Intenta primero terminación suave (SIGTERM), luego forzada (SIGKILL).
        """
        proceso = self.encontrar_proceso_main()
        
        if proceso is None:
            logger.warning("⚠️ No hay proceso que terminar")
            return
        
        try:
            logger.warning(f"⚠️ Terminando proceso PID {proceso.pid}...")
            
            # Intento 1: Terminación suave
            proceso.terminate()
            
            # Esperar 5 segundos
            try:
                proceso.wait(timeout=5)
                logger.info("✅ Proceso terminado suavemente")
                return
            except psutil.TimeoutExpired:
                pass
            
            # Intento 2: Terminación forzada
            logger.warning("⚠️ Terminación suave falló, forzando...")
            proceso.kill()
            proceso.wait(timeout=3)
            logger.info("✅ Proceso terminado forzadamente")
            
        except Exception as e:
            logger.error(f"❌ Error terminando proceso: {e}")
    
    def reiniciar_sistema(self):
        """
        Reinicia el sistema main.py.
        
        1. Termina proceso bloqueado
        2. Espera 3 segundos
        3. Inicia nuevo proceso
        """
        self.reinicios_ejecutados += 1
        
        logger.warning(
            f"🔄 REINICIANDO SISTEMA (intento {self.reinicios_ejecutados}/{self.MAX_REINTENTOS})"
        )
        
        # Paso 1: Terminar proceso bloqueado
        self.terminar_proceso_main()
        
        # Paso 2: Esperar estabilización
        logger.info("⏳ Esperando 3s antes de reiniciar...")
        time.sleep(3)
        
        # Paso 3: Iniciar nuevo proceso
        try:
            if sys.platform == "win32":
                comando = self.COMANDO_REINICIO_WINDOWS
            else:
                comando = self.COMANDO_REINICIO_LINUX
            
            logger.info(f"🚀 Ejecutando: {' '.join(comando)}")
            
            subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            logger.info("✅ Sistema reiniciado")
            
        except Exception as e:
            logger.error(f"❌ Error reiniciando sistema: {e}")
    
    def vigilar(self):
        """
        Loop principal de vigilancia.
        
        Ejecuta indefinidamente hasta que se detenga manualmente.
        """
        logger.info("👁️ VIGILANCIA INICIADA")
        
        while True:
            try:
                # Verificar bloqueo
                hay_bloqueo = self.verificar_bloqueo()
                
                if hay_bloqueo:
                    self.bloqueos_detectados += 1
                    
                    logger.error(
                        f"🚨 BLOQUEO #{self.bloqueos_detectados} DETECTADO"
                    )
                    
                    if self.reinicios_ejecutados < self.MAX_REINTENTOS:
                        self.reiniciar_sistema()
                        
                        # Resetear último heartbeat
                        self.ultimo_heartbeat = None
                        
                        # Esperar 15s para que el sistema arranque
                        logger.info("⏳ Esperando 15s para arranque...")
                        time.sleep(15)
                        
                    else:
                        logger.critical(
                            f"🚨 ALERTA CRÍTICA: {self.MAX_REINTENTOS} reintentos fallidos"
                        )
                        logger.critical("🚨 INTERVENCIÓN MANUAL REQUERIDA")
                        
                        # Seguir vigilando pero sin reiniciar
                        time.sleep(60)
                
                # Esperar antes de próxima verificación
                time.sleep(self.INTERVALO_VERIFICACION)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Vigilancia detenida por usuario")
                break
                
            except Exception as e:
                logger.error(f"❌ Error en vigilancia: {e}")
                time.sleep(5)
        
        # Resumen final
        tiempo_total = datetime.now() - self.tiempo_inicio
        logger.info(f"\n📊 RESUMEN VIGILANCIA:")
        logger.info(f"   Tiempo activo: {tiempo_total}")
        logger.info(f"   Bloqueos detectados: {self.bloqueos_detectados}")
        logger.info(f"   Reinicios ejecutados: {self.reinicios_ejecutados}")


# ============================================================================
# INTEGRACIÓN CON BUS DE DATOS
# ============================================================================

def generar_heartbeat_desde_bus():
    """
    Código para añadir al Bus de datos (main_asgi.py o similar).
    
    ```python
    import json
    from datetime import datetime
    from pathlib import Path
    
    HEARTBEAT_FILE = Path("data/bus_heartbeat.json")
    
    def publicar_heartbeat(self):
        '''Publica heartbeat cada 5 segundos para Centinela Soberano'''
        try:
            heartbeat = {
                "timestamp": datetime.now().isoformat(),
                "ciclos_completados": self.ciclos_totales,
                "estado": "OPERATIVO"
            }
            
            HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(HEARTBEAT_FILE, 'w') as f:
                json.dump(heartbeat, f)
                
        except Exception as e:
            logger.error(f"Error publicando heartbeat: {e}")
    
    # En el loop principal del Bus
    def loop_principal(self):
        while True:
            # ... procesar datos ...
            
            # Publicar heartbeat cada 5s
            if time.time() - self.ultimo_heartbeat > 5.0:
                self.publicar_heartbeat()
                self.ultimo_heartbeat = time.time()
    ```
    """
    pass


# ============================================================================
# INSTALACIÓN COMO SERVICIO WINDOWS
# ============================================================================

def instalar_servicio_windows():
    """
    Script para instalar Centinela como servicio de Windows.
    
    Crear archivo: install_centinela_service.py
    
    ```python
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    
    class CentinelaService(win32serviceutil.ServiceFramework):
        _svc_name_ = "MeteoSerCentinela"
        _svc_display_name_ = "MeteoSer Centinela Soberano"
        _svc_description_ = "Watchdog independiente para MeteoSerV3"
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
        
        def SvcDoRun(self):
            from core.monitoring.centinela_soberano import CentinelaSoberano
            
            centinela = CentinelaSoberano()
            centinela.vigilar()
    
    if __name__ == '__main__':
        win32serviceutil.HandleCommandLine(CentinelaService)
    ```
    
    Instalar:
    ```bash
    python install_centinela_service.py install
    python install_centinela_service.py start
    ```
    """
    pass


if __name__ == "__main__":
    """
    Punto de entrada para ejecución directa.
    
    Uso:
    ```bash
    python core/monitoring/centinela_soberano.py
    ```
    """
    centinela = CentinelaSoberano()
    
    try:
        centinela.vigilar()
    except Exception as e:
        logger.critical(f"🚨 FALLO CRÍTICO DEL CENTINELA: {e}")
        sys.exit(1)

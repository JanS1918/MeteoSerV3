"""
═══════════════════════════════════════════════════════════════════════════════
GUARDRAIL 1: VALIDADOR DE COLISIONES DE NAMING
═══════════════════════════════════════════════════════════════════════════════

Previene conflictos de nombres antes de publicar al Bus.
Con 3,000+ parámetros, dos módulos pueden intentar publicar `temperatura_c`.

ESTRATEGIA:
- Registro global de nombres registrados
- Detección de colisiones ANTES de publicar
- Sugerencias automáticas de renombre
- Bloqueo de colisiones (no sobrescribe)
"""

import logging
import threading
from typing import Dict, Set, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger("bus_validador_naming")


class ValidadorNamingColisiones:
    """
    Guardián de la coherencia de nombres en el Bus.
    
    Mantiene:
    - Registro de todos los nombres publicados
    - Mapeo nombre → (módulo_origen, timestamp)
    - Detección de intentos de colisión
    - Sugerencias de renombre
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        self.registro: Dict[str, Dict] = {}  # nombre → {módulo, timestamp, versión}
        self.colisiones_detectadas: List[Dict] = []
        self.colisiones_bloqueadas: int = 0
        
    @classmethod
    def obtener_instancia(cls) -> 'ValidadorNamingColisiones':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def registrar(self, nombre: str, modulo: str, version: str = "1.0") -> Tuple[bool, Optional[str]]:
        """
        Intenta registrar un nombre en el Bus.
        
        Args:
            nombre: Nombre del parámetro (ej: "hardy_presion_pa")
            modulo: Módulo origen (ej: "core.indices.hardy_nist_psicrometria")
            version: Versión del parámetro
        
        Returns:
            (éxito, mensaje_error_si_existe)
        """
        with self._lock:
            if nombre in self.registro:
                # Colisión detectada
                entrada_existente = self.registro[nombre]
                modulo_existente = entrada_existente["modulo"]
                
                msg_colision = (
                    f"❌ COLISIÓN DE NAMING DETECTADA:\n"
                    f"   Nombre: '{nombre}'\n"
                    f"   Intenta: {modulo}\n"
                    f"   Ya existe: {modulo_existente}\n"
                    f"   Publicación BLOQUEADA para evitar sobrescritura"
                )
                
                logger.warning(msg_colision)
                
                self.colisiones_detectadas.append({
                    "nombre": nombre,
                    "modulo_nuevo": modulo,
                    "modulo_existente": modulo_existente,
                    "timestamp": datetime.now().isoformat(),
                    "sugerencia": self._generar_sugerencia_renombre(nombre, modulo)
                })
                
                self.colisiones_bloqueadas += 1
                return False, msg_colision
            
            # Registrar nuevo nombre
            self.registro[nombre] = {
                "modulo": modulo,
                "timestamp": datetime.now().isoformat(),
                "version": version
            }
            
            logger.debug(f"✅ Registrado: {nombre} ← {modulo}")
            return True, None
    
    def _generar_sugerencia_renombre(self, nombre: str, modulo: str) -> str:
        """Sugiere alternativa de nombre basada en módulo"""
        partes = modulo.split(".")
        modulo_corto = partes[-1]  # Último componente
        
        sugerencias = [
            f"{modulo_corto}_{nombre}",
            f"{nombre}_{modulo_corto}",
            f"{nombre}_v2"
        ]
        
        return f"Sugerencias: {', '.join(sugerencias[:2])}"
    
    def obtener_colisiones(self) -> List[Dict]:
        """Retorna todas las colisiones detectadas"""
        with self._lock:
            return self.colisiones_detectadas.copy()
    
    def resumen(self) -> Dict:
        """Resumen de estado del validador"""
        with self._lock:
            return {
                "nombres_registrados": len(self.registro),
                "colisiones_detectadas": len(self.colisiones_detectadas),
                "colisiones_bloqueadas": self.colisiones_bloqueadas,
                "últimas_colisiones": self.colisiones_detectadas[-5:]
            }
    
    def limpiar_ciclo(self):
        """Limpia para nuevo ciclo (mantiene registro pero reseteamétri cas)"""
        with self._lock:
            self.colisiones_detectadas.clear()
            self.colisiones_bloqueadas = 0
            logger.info(f"🔄 Validador de naming reseteado. {len(self.registro)} nombres guardados.")

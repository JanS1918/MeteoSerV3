"""
AUDIT TRAIL Y LOGGING CENTRALIZADO
Propósito: registro estructurado de anomalías, cambios y decisiones del sistema
Formato: JSON-lines para fácil parseo y consultas
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Crear handler personalizado para logs en JSON-lines
class AnomalyLogHandler(logging.Handler):
    """Handler que escribe anomalías en JSON-lines para fácil parseo."""
    
    def __init__(self, log_file_path: str):
        super().__init__()
        self.log_file = Path(log_file_path)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, record: logging.LogRecord):
        """Escribe un evento de anomalía en formato JSON-lines."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "event_type": "anomaly_detection" if "anomaly" in record.name.lower() else "system_event"
            }
            
            # Agregar información adicional si está disponible
            if hasattr(record, "extra_data"):
                log_entry.update(record.extra_data)
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        except Exception as e:
            self.handleError(record)


def setup_audit_logging(workspace_path: str):
    """
    Configura logging centralizado para anomalías y auditoría.
    """
    logs_dir = Path(workspace_path) / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Logger para anomalías
    anomaly_logger = logging.getLogger("meteoser.anomalies")
    anomaly_logger.setLevel(logging.WARNING)
    
    # Handler: archivo JSON-lines
    json_handler = AnomalyLogHandler(str(logs_dir / "anomalies.log"))
    json_handler.setFormatter(logging.Formatter("%(message)s"))
    anomaly_logger.addHandler(json_handler)
    
    # Handler: archivo texto para legibilidad
    text_file_handler = logging.FileHandler(
        logs_dir / "anomalies_human.log",
        encoding="utf-8"
    )
    text_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s"
    )
    text_file_handler.setFormatter(text_formatter)
    anomaly_logger.addHandler(text_file_handler)
    
    # Logger para auditoría general del sistema
    audit_logger = logging.getLogger("meteoser.audit")
    audit_logger.setLevel(logging.INFO)
    
    audit_file_handler = logging.FileHandler(
        logs_dir / "audit.log",
        encoding="utf-8"
    )
    audit_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s]: %(message)s"
    )
    audit_file_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_file_handler)
    
    return anomaly_logger, audit_logger


# Interfaz simplificada para usar en el código principal
def log_anomaly(sensor_id: str, anomaly_type: str, details: Dict[str, Any]):
    """Registra una anomalía detectada."""
    logger = logging.getLogger("meteoser.anomalies")
    
    entry = {
        "sensor_id": sensor_id,
        "anomaly_type": anomaly_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.warning(f"ANOMALY: {sensor_id} - {anomaly_type} - {json.dumps(details)}")


def log_fallback_activation(sensor_id: str, original_value: float, fallback_value: float, reason: str):
    """Registra la activación de un fallback automático."""
    logger = logging.getLogger("meteoser.audit")
    
    logger.warning(f"FALLBACK_ACTIVATED: {sensor_id} - original={original_value}, fallback={fallback_value}, reason={reason}")


def log_system_decision(decision_type: str, parameters: Dict[str, Any], result: str):
    """Registra decisiones automáticas del sistema."""
    logger = logging.getLogger("meteoser.audit")
    
    logger.info(f"SYSTEM_DECISION: {decision_type} - params={json.dumps(parameters)} - result={result}")


if __name__ == "__main__":
    # Test
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        anomaly_logger, audit_logger = setup_audit_logging(tmpdir)
        
        log_anomaly("sensor_1", "temperature_jump", {"old": 15.0, "new": 35.0, "delta": 20.0})
        log_fallback_activation("sensor_2", 1010.5, 1013.0, "pressure_out_of_range")
        log_system_decision("auto_rollback", {"checkpoint": "baseline"}, "success")
        
        print(f"Logs escritos en {tmpdir}/logs/")
        
        # Mostrar contenido
        with open(Path(tmpdir) / "logs" / "anomalies.log") as f:
            print("\n=== anomalies.log (JSON-lines) ===")
            print(f.read())
        
        with open(Path(tmpdir) / "logs" / "audit.log") as f:
            print("\n=== audit.log (Human-readable) ===")
            print(f.read())

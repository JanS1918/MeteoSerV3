# REGISTRO HISTÓRICO CENTRALIZADO - MeteoSer V3
# ═════════════════════════════════════════════════════════════════════════════
# Abstracción unificada para gestión de históricos (auditoría, feedback, 
# predicciones, índices, validación) evitando duplicación y facilitando 
# integración con CI/CD y auto-auditería.
#
# Metadata: core_manager_v1.0 | Soberanía de Datos | Single Source of Truth
# ═════════════════════════════════════════════════════════════════════════════

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

logger = logging.getLogger("historical_registry")


class RecordType(str, Enum):
    """Tipos de registros en el histórico centralizado."""
    AUDIT = "audit"                    # Cambios en configuración y sistema
    FEEDBACK = "feedback"              # Evaluación del usuario sobre predicciones
    PREDICTION = "prediction"          # Predicción realizada (base para validación)
    ACTUAL = "actual"                  # Valor real observado (para comparación)
    VALIDATION = "validation"          # Resultado de validación predicción vs real
    SENSOR = "sensor"                  # Lectura de sensor bruta
    INDEX = "index"                    # Índice calculado
    ERROR = "error"                    # Error o excepción del sistema
    CALIBRATION = "calibration"        # Evento de calibración
    MAINTENANCE = "maintenance"        # Mantenimiento o cambio de hardware


class ConfidenceLevel(str, Enum):
    """Niveles de confianza para datos."""
    REAL = "real"                      # Dato real medido por sensor
    ESTIMATED = "estimated"            # Dato estimado/derivado
    SYNTHETIC = "synthetic"            # Dato sintético para testing
    DEGRADED = "degraded"              # Dato con precisión reducida (fallback)


@dataclass
class HistoricalRecord:
    """Registro atómico en el histórico centralizado."""
    timestamp: datetime                 # Marca de tiempo UTC
    record_type: RecordType             # Tipo de registro
    entity: str                         # Entidad afectada (ej: "temperatura", "cape_termicas")
    value: Any                          # Valor principal
    confidence: ConfidenceLevel         # Confianza en el dato
    metadata: Dict[str, Any]            # Información adicional
    source: str                         # Fuente del registro
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "record_type": self.record_type.value,
            "entity": self.entity,
            "value": self.value,
            "confidence": self.confidence.value,
            "metadata": self.metadata,
            "source": self.source
        }
    
    def hash(self) -> str:
        """Genera hash SHA256 del registro para integridad."""
        record_str = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(record_str.encode()).hexdigest()


class HistoricalRegistry:
    """
    Gestor centralizado de históricos para MeteoSer.
    
    RESPONSABILIDADES:
    - Registrar todos los eventos del sistema en un único lugar (JSONL)
    - Proporcionar interfaz unificada para acceso a históricos
    - Validar integridad y consistencia de datos
    - Facilitar auditoría automática y generación de reportes
    - Integración con testing y CI/CD
    
    CARACTERÍSTICAS:
    - Thread-safe (bloqueos para escritura)
    - Persistencia en JSONL (legible, auditable, versionable)
    - Metadatos ricos (confianza, fuente, fórmula, etc.)
    - Índices en memoria para búsqueda rápida
    - Limpieza automática por antigüedad
    """
    
    def __init__(self, base_path: str = "data/historical_registry"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Archivo principal de históricos (JSONL)
        self.registry_file = self.base_path / "registry.jsonl"
        
        # Índices para búsqueda rápida
        self.index_by_entity: Dict[str, List[int]] = defaultdict(list)
        self.index_by_type: Dict[str, List[int]] = defaultdict(list)
        self.records: List[HistoricalRecord] = []
        
        # Bloqueo para escritura thread-safe
        import threading
        self._lock = threading.Lock()
        
        # Cargar históricos existentes
        self._load_from_disk()
        
        logger.info(f"[HISTORICAL_REGISTRY] Inicializado con {len(self.records)} registros")
    
    def register(
        self,
        record_type: RecordType,
        entity: str,
        value: Any,
        confidence: ConfidenceLevel = ConfidenceLevel.ESTIMATED,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Registra un evento en el histórico centralizado.
        
        Args:
            record_type: Tipo de registro
            entity: Entidad afectada
            value: Valor a registrar
            confidence: Nivel de confianza del dato
            metadata: Información adicional (fórmula, parámetros, etc.)
            source: Fuente del registro (módulo, función, usuario)
            timestamp: Marca de tiempo (default: ahora en UTC)
        
        Returns:
            Hash SHA256 del registro para integridad
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        record = HistoricalRecord(
            timestamp=timestamp,
            record_type=record_type,
            entity=entity,
            value=value,
            confidence=confidence,
            metadata=metadata or {},
            source=source
        )
        
        with self._lock:
            # Guardar en memoria
            idx = len(self.records)
            self.records.append(record)
            self.index_by_entity[entity].append(idx)
            self.index_by_type[record_type.value].append(idx)
            
            # Guardar en disco
            self._append_to_disk(record)
        
        record_hash = record.hash()
        logger.debug(f"[REGISTRY] Registrado: {record_type.value}:{entity} "
                     f"(confianza={confidence.value}, hash={record_hash[:8]}...)")
        
        return record_hash
    
    def query(
        self,
        entity: Optional[str] = None,
        record_type: Optional[RecordType] = None,
        limit: int = 100,
        offset: int = 0,
        after: Optional[datetime] = None
    ) -> List[HistoricalRecord]:
        """
        Consulta históricos con filtros.
        
        Args:
            entity: Filtrar por entidad
            record_type: Filtrar por tipo de registro
            limit: Número máximo de resultados
            offset: Saltar primeros N registros
            after: Solo registros posteriores a esta fecha
        
        Returns:
            Lista de registros coincidentes
        """
        results = []
        
        if entity and record_type:
            # Carrera rápida: intersección de índices
            entity_indices = set(self.index_by_entity.get(entity, []))
            type_indices = set(self.index_by_type.get(record_type.value, []))
            indices = sorted(entity_indices & type_indices)
        elif entity:
            indices = self.index_by_entity.get(entity, [])
        elif record_type:
            indices = self.index_by_type.get(record_type.value, [])
        else:
            indices = list(range(len(self.records)))
        
        # Aplicar filtro temporal
        for idx in reversed(indices):  # Orden inverso: más recientes primero
            record = self.records[idx]
            if after and record.timestamp <= after:
                continue
            results.append(record)
            if len(results) >= limit:
                break
        
        return results[offset:offset+limit]
    
    def get_entity_history(self, entity: str, limit: int = 100) -> List[HistoricalRecord]:
        """Obtiene el histórico de una entidad específica."""
        return self.query(entity=entity, limit=limit)
    
    def get_validations(self, entity: str, limit: int = 100) -> List[HistoricalRecord]:
        """Obtiene validaciones de una entidad."""
        records = []
        for idx in reversed(self.index_by_type.get(RecordType.VALIDATION.value, [])):
            record = self.records[idx]
            if record.metadata.get("entity") == entity or record.entity == entity:
                records.append(record)
                if len(records) >= limit:
                    break
        return records
    
    def get_feedback(self, entity: Optional[str] = None, limit: int = 100) -> List[HistoricalRecord]:
        """Obtiene feedback del usuario."""
        results = []
        for idx in reversed(self.index_by_type.get(RecordType.FEEDBACK.value, [])):
            record = self.records[idx]
            if entity is None or record.entity == entity:
                results.append(record)
                if len(results) >= limit:
                    break
        return results
    
    def get_statistics(self, entity: str) -> Dict[str, Any]:
        """
        Genera estadísticas para una entidad.
        
        Returns:
            Dict con:
            - total_predictions: Total de predicciones
            - total_validations: Total de validaciones
            - accuracy: % de predicciones correctas (±std)
            - confidence_distribution: Distribución de confianza
            - sources: Top fuentes de datos
        """
        predictions = self.query(entity=entity, record_type=RecordType.PREDICTION)
        validations = self.query(entity=entity, record_type=RecordType.VALIDATION)
        
        if not predictions:
            return {
                "entity": entity,
                "total_predictions": 0,
                "total_validations": 0,
                "note": "Sin datos de predicción"
            }
        
        # Calcular precisión
        correct = sum(1 for v in validations if v.metadata.get("is_correct"))
        accuracy = (correct / len(validations) * 100) if validations else None
        
        # Distribución de confianza
        confidence_dist = defaultdict(int)
        for pred in predictions:
            confidence_dist[pred.confidence.value] += 1
        
        # Top fuentes
        sources = defaultdict(int)
        for rec in predictions + validations:
            sources[rec.source] += 1
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "entity": entity,
            "total_predictions": len(predictions),
            "total_validations": len(validations),
            "accuracy_pct": round(accuracy, 2) if accuracy else None,
            "confidence_distribution": dict(confidence_dist),
            "top_sources": dict(top_sources),
            "date_range": {
                "first": predictions[0].timestamp.isoformat() if predictions else None,
                "last": predictions[-1].timestamp.isoformat() if predictions else None
            }
        }
    
    def validate_prediction(
        self,
        entity: str,
        predicted_value: Any,
        actual_value: Any,
        tolerance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra validación de predicción (predicted vs actual).
        
        Args:
            entity: Entidad predicha
            predicted_value: Valor predicho
            actual_value: Valor real observado
            tolerance: Tolerancia para considerar "correcta"
            metadata: Información adicional
        
        Returns:
            Hash del registro de validación
        """
        # Determinar si la predicción fue correcta
        is_correct = False
        error = None
        if isinstance(predicted_value, (int, float)) and isinstance(actual_value, (int, float)):
            error = abs(predicted_value - actual_value)
            if tolerance:
                is_correct = error <= tolerance
        
        val_metadata = metadata or {}
        val_metadata.update({
            "predicted": predicted_value,
            "actual": actual_value,
            "error": error,
            "tolerance": tolerance,
            "is_correct": is_correct
        })
        
        return self.register(
            record_type=RecordType.VALIDATION,
            entity=entity,
            value=is_correct,
            confidence=ConfidenceLevel.REAL,
            metadata=val_metadata,
            source="validation_engine"
        )
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Limpia registros más antiguos que N días.
        
        Returns:
            Número de registros eliminados
        """
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = cutoff.replace(day=cutoff.day - days)
        
        initial_count = len(self.records)
        
        with self._lock:
            # Recrear índices sin registros viejos
            self.records = [r for r in self.records if r.timestamp > cutoff]
            self._rebuild_indices()
            
            # Reescribir archivo JSONL
            self._rewrite_disk()
        
        removed = initial_count - len(self.records)
        logger.info(f"[CLEANUP] Eliminados {removed} registros anteriores a {cutoff}")
        
        return removed
    
    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS PRIVADOS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _load_from_disk(self) -> None:
        """Carga históricos desde archivo JSONL."""
        if not self.registry_file.exists():
            return
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        record = self._dict_to_record(data)
                        self.records.append(record)
                    except Exception as e:
                        logger.warning(f"[REGISTRY] Error cargando línea {line_no}: {e}")
            
            self._rebuild_indices()
            logger.info(f"[REGISTRY] Cargados {len(self.records)} registros del disco")
        except Exception as e:
            logger.error(f"[REGISTRY] Error cargando históricos: {e}")
    
    def _append_to_disk(self, record: HistoricalRecord) -> None:
        """Añade un registro al archivo JSONL."""
        try:
            with open(self.registry_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), default=str) + '\n')
        except Exception as e:
            logger.error(f"[REGISTRY] Error escribiendo registro: {e}")
    
    def _rewrite_disk(self) -> None:
        """Reescribe el archivo JSONL completo (usado después de limpiar)."""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                for record in self.records:
                    f.write(json.dumps(record.to_dict(), default=str) + '\n')
        except Exception as e:
            logger.error(f"[REGISTRY] Error reescribiendo históricos: {e}")
    
    def _rebuild_indices(self) -> None:
        """Reconstruye índices en memoria."""
        self.index_by_entity.clear()
        self.index_by_type.clear()
        for idx, record in enumerate(self.records):
            self.index_by_entity[record.entity].append(idx)
            self.index_by_type[record.record_type.value].append(idx)
    
    def _dict_to_record(self, data: Dict[str, Any]) -> HistoricalRecord:
        """Convierte diccionario JSON a HistoricalRecord."""
        return HistoricalRecord(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            record_type=RecordType(data["record_type"]),
            entity=data["entity"],
            value=data["value"],
            confidence=ConfidenceLevel(data["confidence"]),
            metadata=data.get("metadata", {}),
            source=data["source"]
        )


# Instancia global (singleton)
_global_registry: Optional[HistoricalRegistry] = None


def get_registry() -> HistoricalRegistry:
    """Obtiene la instancia global del registro histórico."""
    global _global_registry
    if _global_registry is None:
        _global_registry = HistoricalRegistry()
    return _global_registry


def register_event(
    record_type: RecordType,
    entity: str,
    value: Any,
    confidence: ConfidenceLevel = ConfidenceLevel.ESTIMATED,
    metadata: Optional[Dict[str, Any]] = None,
    source: str = "unknown"
) -> str:
    """Helper function para registrar eventos."""
    return get_registry().register(
        record_type=record_type,
        entity=entity,
        value=value,
        confidence=confidence,
        metadata=metadata,
        source=source
    )

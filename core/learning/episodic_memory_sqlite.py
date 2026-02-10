#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
        MEMORIA EPISODICA SQLITE - ALTERNATIVA SIN EMBEDDINGS
        Sistema de Memoria con Busqueda SQL Tradicional
================================================================================

OBJETIVO: Proporcionar memoria episodica sin dependencias complejas.
          Usa SQLite nativo de Python (sin instalacion adicional).

VENTAJAS VS CHROMADB:
- Sin dependencias externas (SQLite viene con Python)
- Compatible con cualquier version de Python
- Mas simple y mas rapido para datasets pequeños
- Full-text search integrado (FTS5)

DESVENTAJAS:
- No hay busqueda semantica (solo keywords)
- No hay clustering automatico
- Menos sofisticado que embeddings vectoriales

ARQUITECTURA:
- Base de datos SQLite con 4 tablas principales
- FTS5 (Full-Text Search) para busqueda rapida
- Indices B-tree para consultas por metadatas

METADATA: motor: SQLiteMemory_v1.0
================================================================================
"""

import logging
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger("sqlite_memory")

# ════════════════════════════════════════════════════════════════
# CONFIGURACION
# ════════════════════════════════════════════════════════════════

MEMORY_DB_PATH = Path("data/episodic_memory.db")


class EpisodicMemorySQL:
    """
    Memoria episodica basada en SQLite con Full-Text Search.
    
    Mas simple que ChromaDB pero sin busqueda semantica.
    """
    
    def __init__(self, db_path: Path = MEMORY_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Retornar filas como dict
        
        self._initialize_schema()
        
        logger.info(f"🧠 MEMORIA EPISODICA SQLITE INICIALIZADA: {db_path}")
        stats = self.get_memory_stats()
        for table, count in stats["tables"].items():
            logger.info(f"   ├─ {table}: {count} registros")
    
    def _initialize_schema(self):
        """Crea las tablas de la base de datos."""
        cursor = self.conn.cursor()
        
        # Tabla principal: Patrones meteorologicos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_patterns (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            description TEXT NOT NULL,
            temperatura_c REAL,
            presion_hpa REAL,
            humedad_pct REAL,
            viento_ms REAL,
            lluvia_mm REAL,
            flujo_calor_sensible_H REAL,
            radiacion_neta_Rn REAL,
            utci REAL,
            tipo_patron TEXT,
            metadata_json TEXT
        )
        """)
        
        # FTS5 para busqueda full-text en weather_patterns
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS weather_patterns_fts USING fts5(
            description,
            content=weather_patterns,
            content_rowid=rowid
        )
        """)
        
        # Tabla: Episodios de anomalias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_episodes (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            sensor_id TEXT NOT NULL,
            anomaly_status TEXT,
            description TEXT NOT NULL,
            resolution_type TEXT,
            confidence_score REAL,
            metadata_json TEXT
        )
        """)
        
        # FTS5 para anomalias
        cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS anomaly_episodes_fts USING fts5(
            description,
            content=anomaly_episodes,
            content_rowid=rowid
        )
        """)
        
        # Tabla: Firmas fisicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS physics_signatures (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            H_sensible REAL,
            Rn_radiacion REAL,
            utci REAL,
            balance_energetico REAL,
            description TEXT NOT NULL,
            metadata_json TEXT
        )
        """)
        
        # Tabla: Comportamiento de sensores
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_behaviors (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            sensor_id TEXT NOT NULL,
            behavior_type TEXT,
            description TEXT NOT NULL,
            metadata_json TEXT
        )
        """)
        
        # Indices para consultas rapidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wp_timestamp ON weather_patterns(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wp_tipo ON weather_patterns(tipo_patron)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_sensor ON anomaly_episodes(sensor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ae_timestamp ON anomaly_episodes(timestamp)")
        
        self.conn.commit()
    
    # ════════════════════════════════════════════════════════════════
    # INGESTION DE EPISODIOS
    # ════════════════════════════════════════════════════════════════
    
    def memorize_weather_pattern(
        self,
        estado_global: Dict[str, Any],
        subfactores: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Memoriza un patron meteorologico.
        
        Args:
            estado_global: Estado global del bus
            subfactores: Los 372 subfactores
            timestamp: Timestamp (default: now)
        
        Returns:
            ID del registro
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Generar descripcion
        description = self._generate_weather_description(estado_global, subfactores)
        
        # ID unico
        record_id = f"wp_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Datos
        data = {
            "id": record_id,
            "timestamp": timestamp.isoformat(),
            "description": description,
            "temperatura_c": estado_global.get("temperatura", 0.0),
            "presion_hpa": estado_global.get("presion", 0.0),
            "humedad_pct": estado_global.get("humedad", 0.0),
            "viento_ms": estado_global.get("viento", 0.0),
            "lluvia_mm": estado_global.get("lluvia_acumulada", 0.0),
            "flujo_calor_sensible_H": subfactores.get("flujo_calor_sensible_H", 0.0),
            "radiacion_neta_Rn": subfactores.get("radiacion_neta_Rn", 0.0),
            "utci": subfactores.get("utci", 0.0),
            "tipo_patron": self._classify_pattern(estado_global),
            "metadata_json": json.dumps(subfactores)
        }
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO weather_patterns VALUES 
            (:id, :timestamp, :description, :temperatura_c, :presion_hpa, 
             :humedad_pct, :viento_ms, :lluvia_mm, :flujo_calor_sensible_H,
             :radiacion_neta_Rn, :utci, :tipo_patron, :metadata_json)
            """, data)
            
            # Actualizar FTS
            cursor.execute("""
            INSERT INTO weather_patterns_fts(rowid, description) 
            VALUES ((SELECT rowid FROM weather_patterns WHERE id = ?), ?)
            """, (record_id, description))
            
            self.conn.commit()
            logger.debug(f"📝 Patron memorizado: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error memorizando patron: {e}")
            self.conn.rollback()
            return ""
    
    def memorize_anomaly_episode(
        self,
        anomaly_data: Dict[str, Any],
        resolution: str,
        context: Dict[str, Any]
    ) -> str:
        """Memoriza episodio de anomalia."""
        timestamp = datetime.now(timezone.utc)
        
        sensor = anomaly_data.get("sensor_id", "unknown")
        status = anomaly_data.get("status", "DUDOSO")
        reasons = ", ".join(anomaly_data.get("reasons", []))
        
        description = (
            f"Anomalia en {sensor}: {status}. "
            f"Razones: {reasons}. "
            f"Resolucion: {resolution}. "
            f"Contexto: temp={context.get('temperatura', 0):.1f}C"
        )
        
        record_id = f"ae_{timestamp.strftime('%Y%m%d_%H%M%S')}_{sensor}"
        
        data = {
            "id": record_id,
            "timestamp": timestamp.isoformat(),
            "sensor_id": sensor,
            "anomaly_status": status,
            "description": description,
            "resolution_type": resolution,
            "confidence_score": anomaly_data.get("score", 0.0),
            "metadata_json": json.dumps({**anomaly_data, **context})
        }
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO anomaly_episodes VALUES
            (:id, :timestamp, :sensor_id, :anomaly_status, :description,
             :resolution_type, :confidence_score, :metadata_json)
            """, data)
            
            cursor.execute("""
            INSERT INTO anomaly_episodes_fts(rowid, description)
            VALUES ((SELECT rowid FROM anomaly_episodes WHERE id = ?), ?)
            """, (record_id, description))
            
            self.conn.commit()
            logger.info(f"[CRITICAL] Anomalia memorizada: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error memorizando anomalia: {e}")
            self.conn.rollback()
            return ""
    
    def memorize_physics_signature(
        self,
        H: float,
        Rn: float,
        utci: float,
        context: Dict[str, Any]
    ) -> str:
        """Memoriza firma fisica."""
        timestamp = datetime.now(timezone.utc)
        
        description = (
            f"Firma fisica: H={H:.1f}W/m², Rn={Rn:.1f}W/m², UTCI={utci:.1f}°C. "
            f"Balance energetico: {H+Rn:.1f}W/m²"
        )
        
        record_id = f"ps_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        data = {
            "id": record_id,
            "timestamp": timestamp.isoformat(),
            "H_sensible": H,
            "Rn_radiacion": Rn,
            "utci": utci,
            "balance_energetico": H + Rn,
            "description": description,
            "metadata_json": json.dumps(context)
        }
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO physics_signatures VALUES
            (:id, :timestamp, :H_sensible, :Rn_radiacion, :utci,
             :balance_energetico, :description, :metadata_json)
            """, data)
            
            self.conn.commit()
            logger.debug(f"⚛️ Firma fisica memorizada: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Error memorizando firma: {e}")
            self.conn.rollback()
            return ""
    
    # ════════════════════════════════════════════════════════════════
    # BUSQUEDA (FTS5 + SQL)
    # ════════════════════════════════════════════════════════════════
    
    def search_similar_situations(
        self,
        query: str,
        table: str = "weather_patterns",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca situaciones usando Full-Text Search.
        
        Args:
            query: Texto a buscar (keywords)
            table: Tabla donde buscar
            limit: Numero de resultados
        
        Returns:
            Lista de registros similares
        
        Ejemplo:
            memory.search_similar_situations("viento fuerte presion baja")
        """
        fts_table = f"{table}_fts"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
            SELECT t.*, fts.rank
            FROM {table} t
            JOIN {fts_table} fts ON t.rowid = fts.rowid
            WHERE {fts_table} MATCH ?
            ORDER BY fts.rank
            LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["metadata"] = json.loads(result.get("metadata_json", "{}"))
                results.append(result)
            
            logger.info(f"[BUSCAR] Encontrados {len(results)} resultados para: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error en busqueda: {e}")
            return []
    
    def find_similar_anomalies(
        self,
        current_anomaly: Dict[str, Any],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Encuentra anomalias pasadas similares."""
        sensor = current_anomaly.get("sensor_id", "unknown")
        reasons = " ".join(current_anomaly.get("reasons", []))
        
        query = f"{sensor} {reasons}"
        
        return self.search_similar_situations(query, "anomaly_episodes", limit)
    
    def get_patterns_by_type(
        self,
        tipo_patron: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene patrones por tipo (storm, windy, cold, hot, normal)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT * FROM weather_patterns
            WHERE tipo_patron = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """, (tipo_patron, limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["metadata"] = json.loads(result.get("metadata_json", "{}"))
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error obteniendo patrones: {e}")
            return []
    
    def get_recent_episodes(
        self,
        table: str = "weather_patterns",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtiene los episodios mas recientes."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
            SELECT * FROM {table}
            ORDER BY timestamp DESC
            LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["metadata"] = json.loads(result.get("metadata_json", "{}"))
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error obteniendo episodios: {e}")
            return []
    
    # ════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ════════════════════════════════════════════════════════════════
    
    def _generate_weather_description(
        self,
        estado_global: Dict[str, Any],
        subfactores: Dict[str, float]
    ) -> str:
        """Genera descripcion del patron."""
        temp = estado_global.get("temperatura", 0.0)
        viento = estado_global.get("viento", 0.0)
        lluvia = estado_global.get("lluvia_acumulada", 0.0)
        humedad = estado_global.get("humedad", 0.0)
        
        parts = []
        
        if temp < 5:
            parts.append("muy frio")
        elif temp < 15:
            parts.append("frio")
        elif temp < 25:
            parts.append("templado")
        else:
            parts.append("caluroso")
        
        if viento > 20:
            parts.append("viento muy fuerte")
        elif viento > 10:
            parts.append("viento moderado")
        
        if lluvia > 10:
            parts.append("lluvia intensa")
        elif lluvia > 1:
            parts.append("lluvia ligera")
        
        if humedad > 80:
            parts.append("muy humedo")
        elif humedad < 30:
            parts.append("muy seco")
        
        return f"Patron: {', '.join(parts)}"
    
    def _classify_pattern(self, estado_global: Dict[str, Any]) -> str:
        """Clasifica el patron."""
        temp = estado_global.get("temperatura", 20.0)
        viento = estado_global.get("viento", 0.0)
        lluvia = estado_global.get("lluvia_acumulada", 0.0)
        
        if lluvia > 5:
            return "storm"
        elif viento > 15:
            return "windy"
        elif temp < 5:
            return "cold"
        elif temp > 30:
            return "hot"
        else:
            return "normal"
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Estadisticas de la memoria."""
        cursor = self.conn.cursor()
        
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "db_path": str(self.db_path),
            "tables": {}
        }
        
        for table in ["weather_patterns", "anomaly_episodes", "physics_signatures", "sensor_behaviors"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats["tables"][table] = cursor.fetchone()[0]
        
        return stats
    
    def export_to_json(self, output_path: Path):
        """Exporta toda la base de datos a JSON."""
        export_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.get_memory_stats(),
            "data": {}
        }
        
        cursor = self.conn.cursor()
        
        for table in ["weather_patterns", "anomaly_episodes", "physics_signatures"]:
            cursor.execute(f"SELECT * FROM {table}")
            export_data["data"][table] = [dict(row) for row in cursor.fetchall()]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[GUARDAR] Memoria exportada a: {output_path}")
    
    def close(self):
        """Cierra la conexion."""
        self.conn.close()
        logger.info("🔒 Conexion cerrada")


# ════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════

def demo_sqlite_memory():
    """Demo de memoria episodica SQL."""
    print("\n" + "="*80)
    print("DEMO: MEMORIA EPISODICA SQLITE (Sin dependencias externas)")
    print("="*80 + "\n")
    
    # Inicializar
    memory = EpisodicMemorySQL()
    
    # Memorizar patron 1
    print("[1/4] Memorizando: Dia soleado caluroso...")
    estado1 = {
        "temperatura": 32.5,
        "presion": 1015.0,
        "humedad": 45.0,
        "viento": 3.2,
        "lluvia_acumulada": 0.0
    }
    subfactores1 = {
        "flujo_calor_sensible_H": 120.5,
        "radiacion_neta_Rn": 450.0,
        "utci": 34.2
    }
    id1 = memory.memorize_weather_pattern(estado1, subfactores1)
    print(f"   ✓ ID: {id1}")
    
    # Memorizar patron 2
    print("\n[2/4] Memorizando: Tormenta viento fuerte...")
    estado2 = {
        "temperatura": 18.5,
        "presion": 995.0,
        "humedad": 85.0,
        "viento": 22.5,
        "lluvia_acumulada": 12.5
    }
    subfactores2 = {
        "flujo_calor_sensible_H": -75.2,
        "radiacion_neta_Rn": -25.0,
        "utci": 12.8
    }
    id2 = memory.memorize_weather_pattern(estado2, subfactores2)
    print(f"   ✓ ID: {id2}")
    
    # Busqueda FTS
    print("\n[3/4] Buscando: 'caluroso sol'...")
    results = memory.search_similar_situations("caluroso", limit=2)
    
    for i, result in enumerate(results, 1):
        print(f"\n   Resultado {i}:")
        print(f"   - ID: {result['id']}")
        print(f"   - Descripcion: {result['description']}")
        print(f"   - Temperatura: {result['temperatura_c']}°C")
    
    # Estadisticas
    print("\n[4/4] Estadisticas:")
    stats = memory.get_memory_stats()
    for table, count in stats["tables"].items():
        print(f"   - {table}: {count} registros")
    
    memory.close()
    
    print("\n" + "="*80)
    print("[OK] DEMO COMPLETADA - Memoria SQLite operativa (SIN DEPENDENCIAS)")
    print("="*80 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )
    
    demo_sqlite_memory()

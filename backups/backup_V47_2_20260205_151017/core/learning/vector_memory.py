#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
        MEMORIA VECTORIAL DEL ACORAZADO - CHROMADB INTEGRATION
        Sistema de Memoria Episodica con Embeddings Semanticos
================================================================================

OBJETIVO: Convertir el Acorazado en un sistema con MEMORIA REAL que recuerda
          situaciones pasadas y puede buscar "casos similares" semanticamente.

ARQUITECTURA:
- ChromaDB: Base de datos vectorial local (sin servidor externo)
- Embeddings: all-MiniLM-L6-v2 (rapido, 384 dimensiones)
- Colecciones:
  * weather_patterns: Patrones meteorologicos historicos
  * anomaly_episodes: Episodios de anomalias resueltas
  * physics_signatures: Firmas fisicas (H, Rn, UTCI) caracteristicas

VENTAJAS VS JSONL:
- Busqueda semantica: "situaciones con viento fuerte y caida de presion"
- Clustering automatico: Detecta patrones sin supervision
- Memoria episodica: "¿cuando paso algo parecido antes?"
- Escalabilidad: Millones de vectores sin degradacion

METADATA: motor: VectorMemory_Chroma_v1.0
================================================================================
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB no disponible. Instalar con: pip install chromadb")

logger = logging.getLogger("vector_memory")

# ════════════════════════════════════════════════════════════════
# CONFIGURACION
# ════════════════════════════════════════════════════════════════

VECTOR_DB_PATH = Path("data/vector_memory")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Modelo sentence-transformers


class VectorMemoryEngine:
    """
    Motor de memoria vectorial para el Acorazado.
    
    Almacena y recupera situaciones meteorologicas pasadas usando embeddings.
    """
    
    def __init__(self, db_path: Path = VECTOR_DB_PATH):
        if not CHROMA_AVAILABLE:
            raise RuntimeError("ChromaDB no esta instalado. pip install chromadb")
        
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        
        # Colecciones
        self.collections = {}
        self._initialize_collections()
        
        logger.info(f"🧠 MEMORIA VECTORIAL INICIALIZADA: {db_path}")
        logger.info(f"   ├─ Modelo embeddings: {EMBEDDING_MODEL}")
        logger.info(f"   └─ Colecciones: {list(self.collections.keys())}")
    
    def _initialize_collections(self):
        """Inicializa las colecciones de ChromaDB."""
        
        collection_specs = [
            {
                "name": "weather_patterns",
                "metadata": {"description": "Patrones meteorologicos historicos"}
            },
            {
                "name": "anomaly_episodes",
                "metadata": {"description": "Episodios de anomalias y resoluciones"}
            },
            {
                "name": "physics_signatures",
                "metadata": {"description": "Firmas fisicas caracteristicas (H, Rn, UTCI)"}
            },
            {
                "name": "sensor_behaviors",
                "metadata": {"description": "Comportamiento de sensores en diferentes condiciones"}
            }
        ]
        
        for spec in collection_specs:
            try:
                collection = self.client.get_or_create_collection(
                    name=spec["name"],
                    embedding_function=self.embedding_fn,
                    metadata=spec["metadata"]
                )
                self.collections[spec["name"]] = collection
                logger.info(f"   ✓ Colección '{spec['name']}': {collection.count()} vectores")
            except Exception as e:
                logger.error(f"   ✗ Error creando colección {spec['name']}: {e}")
    
    # ════════════════════════════════════════════════════════════════
    # INGESTIÓN DE PATRONES
    # ════════════════════════════════════════════════════════════════
    
    def memorize_weather_pattern(
        self,
        estado_global: Dict[str, Any],
        subfactores: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Memoriza un patron meteorologico completo.
        
        Args:
            estado_global: Estado global del bus (sensores principales)
            subfactores: Los 372 subfactores calculados
            timestamp: Timestamp del patron (default: now)
        
        Returns:
            ID del vector almacenado
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Generar descripción semantica
        description = self._generate_weather_description(estado_global, subfactores)
        
        # ID unico
        vector_id = f"wp_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Metadata completa
        metadata = {
            "timestamp": timestamp.isoformat(),
            "temperatura_c": estado_global.get("temperatura", 0.0),
            "presion_hpa": estado_global.get("presion", 0.0),
            "humedad_pct": estado_global.get("humedad", 0.0),
            "viento_ms": estado_global.get("viento", 0.0),
            "lluvia_mm": estado_global.get("lluvia_acumulada", 0.0),
            "flujo_calor_sensible_H": subfactores.get("flujo_calor_sensible_H", 0.0),
            "radiacion_neta_Rn": subfactores.get("radiacion_neta_Rn", 0.0),
            "utci": subfactores.get("utci", 0.0),
            "tipo_patron": self._classify_pattern(estado_global)
        }
        
        # Almacenar en ChromaDB
        try:
            self.collections["weather_patterns"].add(
                documents=[description],
                metadatas=[metadata],
                ids=[vector_id]
            )
            logger.debug(f"📝 Patron memorizado: {vector_id}")
            return vector_id
        except Exception as e:
            logger.error(f"Error memorizando patron: {e}")
            return ""
    
    def memorize_anomaly_episode(
        self,
        anomaly_data: Dict[str, Any],
        resolution: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Memoriza un episodio de anomalia y su resolucion.
        
        Args:
            anomaly_data: Datos de la anomalia (sensor, valor, score)
            resolution: Como se resolvio (fallback ISA, calibracion, etc)
            context: Contexto meteorologico cuando ocurrio
        
        Returns:
            ID del vector almacenado
        """
        timestamp = datetime.now(timezone.utc)
        
        # Descripcion semantica del episodio
        sensor = anomaly_data.get("sensor_id", "unknown")
        status = anomaly_data.get("status", "DUDOSO")
        reasons = ", ".join(anomaly_data.get("reasons", []))
        
        description = (
            f"Anomalia en {sensor}: {status}. "
            f"Razones: {reasons}. "
            f"Resolucion aplicada: {resolution}. "
            f"Contexto: temp={context.get('temperatura', 0):.1f}C, "
            f"presion={context.get('presion', 0):.0f}hPa, "
            f"humedad={context.get('humedad', 0):.0f}%"
        )
        
        vector_id = f"ae_{timestamp.strftime('%Y%m%d_%H%M%S')}_{sensor}"
        
        metadata = {
            "timestamp": timestamp.isoformat(),
            "sensor_id": sensor,
            "anomaly_status": status,
            "resolution_type": resolution,
            "confidence_score": anomaly_data.get("score", 0.0),
            **context
        }
        
        try:
            self.collections["anomaly_episodes"].add(
                documents=[description],
                metadatas=[metadata],
                ids=[vector_id]
            )
            logger.info(f"🚨 Episodio de anomalia memorizado: {vector_id}")
            return vector_id
        except Exception as e:
            logger.error(f"Error memorizando anomalia: {e}")
            return ""
    
    def memorize_physics_signature(
        self,
        H: float,  # Flujo calor sensible
        Rn: float,  # Radiacion neta
        utci: float,  # Confort termico
        context: Dict[str, Any]
    ) -> str:
        """
        Memoriza una firma fisica caracteristica.
        
        Args:
            H: Flujo de calor sensible (W/m²)
            Rn: Radiacion neta (W/m²)
            utci: Indice UTCI (confort termico)
            context: Contexto meteorologico
        
        Returns:
            ID del vector almacenado
        """
        timestamp = datetime.now(timezone.utc)
        
        # Interpretacion fisica
        h_interpretation = "enfriamiento" if H < 0 else "calentamiento"
        rn_interpretation = "radiativo neto positivo" if Rn > 0 else "perdida radiativa"
        utci_interpretation = self._interpret_utci(utci)
        
        description = (
            f"Firma fisica: H={H:.1f}W/m² ({h_interpretation}), "
            f"Rn={Rn:.1f}W/m² ({rn_interpretation}), "
            f"UTCI={utci:.1f}°C ({utci_interpretation}). "
            f"Condiciones: temp={context.get('temperatura', 0):.1f}C, "
            f"viento={context.get('viento', 0):.1f}m/s"
        )
        
        vector_id = f"ps_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            "timestamp": timestamp.isoformat(),
            "H_sensible": H,
            "Rn_radiacion": Rn,
            "utci": utci,
            "balance_energetico": H + Rn,
            **context
        }
        
        try:
            self.collections["physics_signatures"].add(
                documents=[description],
                metadatas=[metadata],
                ids=[vector_id]
            )
            logger.debug(f"⚛️ Firma fisica memorizada: {vector_id}")
            return vector_id
        except Exception as e:
            logger.error(f"Error memorizando firma: {e}")
            return ""
    
    # ════════════════════════════════════════════════════════════════
    # BUSQUEDA SEMANTICA
    # ════════════════════════════════════════════════════════════════
    
    def recall_similar_situations(
        self,
        query: str,
        collection_name: str = "weather_patterns",
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca situaciones similares usando embeddings semanticos.
        
        Args:
            query: Descripcion de la situacion a buscar
            collection_name: Nombre de la coleccion
            n_results: Numero de resultados
            where: Filtros de metadata (opcional)
        
        Returns:
            Lista de situaciones similares con distancia y metadata
        
        Ejemplo:
            engine.recall_similar_situations(
                "viento fuerte con caida rapida de presion",
                n_results=3
            )
        """
        if collection_name not in self.collections:
            logger.error(f"Colección '{collection_name}' no existe")
            return []
        
        collection = self.collections[collection_name]
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Formatear resultados
            similar = []
            for i in range(len(results['ids'][0])):
                similar.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i]
                })
            
            logger.info(f"🔍 Encontrados {len(similar)} casos similares a: '{query}'")
            return similar
            
        except Exception as e:
            logger.error(f"Error en busqueda semantica: {e}")
            return []
    
    def find_similar_anomalies(
        self,
        current_anomaly: Dict[str, Any],
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Encuentra anomalias pasadas similares para aprender de resoluciones previas.
        
        Args:
            current_anomaly: Anomalia actual
            n_results: Numero de resultados
        
        Returns:
            Lista de anomalias similares con sus resoluciones
        """
        sensor = current_anomaly.get("sensor_id", "unknown")
        reasons = ", ".join(current_anomaly.get("reasons", []))
        
        query = f"Anomalia en {sensor} con {reasons}"
        
        return self.recall_similar_situations(
            query,
            collection_name="anomaly_episodes",
            n_results=n_results
        )
    
    # ════════════════════════════════════════════════════════════════
    # UTILIDADES
    # ════════════════════════════════════════════════════════════════
    
    def _generate_weather_description(
        self,
        estado_global: Dict[str, Any],
        subfactores: Dict[str, float]
    ) -> str:
        """Genera descripcion semantica del patron meteorologico."""
        temp = estado_global.get("temperatura", 0.0)
        presion = estado_global.get("presion", 0.0)
        humedad = estado_global.get("humedad", 0.0)
        viento = estado_global.get("viento", 0.0)
        lluvia = estado_global.get("lluvia_acumulada", 0.0)
        
        H = subfactores.get("flujo_calor_sensible_H", 0.0)
        utci = subfactores.get("utci", temp)
        
        # Construir descripcion natural
        parts = []
        
        # Temperatura
        if temp < 5:
            parts.append("muy frio")
        elif temp < 15:
            parts.append("frio")
        elif temp < 25:
            parts.append("templado")
        else:
            parts.append("caluroso")
        
        # Viento
        if viento > 20:
            parts.append("con viento muy fuerte")
        elif viento > 10:
            parts.append("con viento moderado")
        elif viento > 3:
            parts.append("con brisa suave")
        
        # Lluvia
        if lluvia > 10:
            parts.append("bajo lluvia intensa")
        elif lluvia > 1:
            parts.append("con lluvia ligera")
        
        # Humedad
        if humedad > 80:
            parts.append("muy humedo")
        elif humedad < 30:
            parts.append("muy seco")
        
        # Presion
        if presion > 1020:
            parts.append("alta presion atmosferica")
        elif presion < 1000:
            parts.append("baja presion atmosferica")
        
        # Fisica
        if H < -50:
            parts.append("enfriamiento rapido por conveccion")
        elif H > 50:
            parts.append("calentamiento convectivo activo")
        
        description = f"Patron meteorologico: {', '.join(parts)}. "
        description += f"Temp={temp:.1f}C, Presion={presion:.0f}hPa, Humedad={humedad:.0f}%, Viento={viento:.1f}m/s, UTCI={utci:.1f}C"
        
        return description
    
    def _classify_pattern(self, estado_global: Dict[str, Any]) -> str:
        """Clasifica el patron en categorias generales."""
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
    
    def _interpret_utci(self, utci: float) -> str:
        """Interpreta el indice UTCI."""
        if utci < -40:
            return "frio extremo"
        elif utci < -27:
            return "muy frio"
        elif utci < -13:
            return "frio"
        elif utci < 0:
            return "fresco"
        elif utci < 9:
            return "ligeramente fresco"
        elif utci < 26:
            return "confortable"
        elif utci < 32:
            return "ligeramente caluroso"
        elif utci < 38:
            return "caluroso"
        elif utci < 46:
            return "muy caluroso"
        else:
            return "calor extremo"
    
    # ════════════════════════════════════════════════════════════════
    # ESTADISTICAS Y MANTENIMIENTO
    # ════════════════════════════════════════════════════════════════
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas de la memoria vectorial."""
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "db_path": str(self.db_path),
            "embedding_model": EMBEDDING_MODEL,
            "collections": {}
        }
        
        for name, collection in self.collections.items():
            stats["collections"][name] = {
                "count": collection.count(),
                "metadata": collection.metadata
            }
        
        return stats
    
    def export_to_json(self, output_path: Path):
        """Exporta toda la memoria vectorial a JSON (backup)."""
        export_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.get_memory_stats(),
            "collections": {}
        }
        
        for name, collection in self.collections.items():
            # Obtener todos los vectores
            all_data = collection.get()
            export_data["collections"][name] = {
                "ids": all_data["ids"],
                "documents": all_data["documents"],
                "metadatas": all_data["metadatas"]
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Memoria exportada a: {output_path}")
    
    def reset_collection(self, collection_name: str):
        """Resetea una coleccion (PELIGRO: borra todo)."""
        if collection_name in self.collections:
            self.client.delete_collection(collection_name)
            logger.warning(f"🗑️ Colección '{collection_name}' eliminada")
            self._initialize_collections()


# ════════════════════════════════════════════════════════════════
# DEMO Y TESTING
# ════════════════════════════════════════════════════════════════

def demo_vector_memory():
    """Demo de la memoria vectorial."""
    print("\n" + "="*80)
    print("DEMO: MEMORIA VECTORIAL DEL ACORAZADO")
    print("="*80 + "\n")
    
    if not CHROMA_AVAILABLE:
        print("❌ ChromaDB no instalado. Ejecutar: pip install chromadb")
        return
    
    # Inicializar engine
    engine = VectorMemoryEngine()
    
    # Simular patron meteorologico 1
    print("[1/4] Memorizando patron: Dia soleado y caluroso...")
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
    id1 = engine.memorize_weather_pattern(estado1, subfactores1)
    print(f"   ✓ Memorizado: {id1}")
    
    # Simular patron meteorologico 2
    print("\n[2/4] Memorizando patron: Tormenta con viento fuerte...")
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
    id2 = engine.memorize_weather_pattern(estado2, subfactores2)
    print(f"   ✓ Memorizado: {id2}")
    
    # Busqueda semantica
    print("\n[3/4] Buscando: 'dia caluroso con sol'...")
    results = engine.recall_similar_situations(
        "dia caluroso con sol y poca humedad",
        n_results=2
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n   Resultado {i}:")
        print(f"   - ID: {result['id']}")
        print(f"   - Descripcion: {result['document'][:100]}...")
        print(f"   - Distancia: {result['distance']:.4f}")
        print(f"   - Temperatura: {result['metadata'].get('temperatura_c')}°C")
    
    # Estadisticas
    print("\n[4/4] Estadisticas de memoria:")
    stats = engine.get_memory_stats()
    for coll_name, coll_stats in stats["collections"].items():
        print(f"   - {coll_name}: {coll_stats['count']} vectores")
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETADA - Memoria vectorial operativa")
    print("="*80 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )
    
    demo_vector_memory()

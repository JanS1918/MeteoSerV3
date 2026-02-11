from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import block_a
from . import block_d
from . import block_c

logger = logging.getLogger("meteoser_ia.block_g")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE G] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

HEARTBEAT_INTERVAL = 2.0
HEARTBEAT_TIMEOUT = 6.0
LEADER_ELECTION_TIMEOUT = 3.0
STATE_REPLICA_INTERVAL = 5.0


@dataclass
class NodeInfo:
    node_id: str
    host: str
    port: int
    last_heartbeat: float = field(default_factory=time.time)
    is_leader: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusterStateSnapshot:
    nodes: Dict[str, NodeInfo] = field(default_factory=dict)
    leader_id: Optional[str] = None
    last_updated: float = field(default_factory=time.time)


class ClusterRegistry:
    def __init__(self) -> None:
        self._nodes: Dict[str, NodeInfo] = {}
        self._lock = threading.Lock()

    def register_node(
        self, host: str = "127.0.0.1", port: int = 0, metadata: Dict[str, Any] = None
    ) -> NodeInfo:
        with self._lock:
            nid = f"node_{uuid.uuid4().hex[:8]}"
            node = NodeInfo(
                node_id=nid, host=host, port=port or 0, metadata=metadata or {}
            )
            self._nodes[nid] = node
            logger.info(f"Cluster: nodo registrado {nid} host={host} port={port}")
            return node

    def unregister_node(self, node_id: str) -> None:
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                logger.info(f"Cluster: nodo eliminado {node_id}")

    def list_nodes(self) -> List[NodeInfo]:
        with self._lock:
            return list(self._nodes.values())

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        with self._lock:
            return self._nodes.get(node_id)

    def update_heartbeat(self, node_id: str) -> None:
        with self._lock:
            n = self._nodes.get(node_id)
            if n:
                n.last_heartbeat = time.time()
                logger.debug(f"Cluster: heartbeat actualizado para {node_id}")

    def snapshot(self) -> ClusterStateSnapshot:
        with self._lock:
            leader = next(
                (n.node_id for n in self._nodes.values() if n.is_leader), None
            )
            return ClusterStateSnapshot(
                nodes=dict(self._nodes), leader_id=leader, last_updated=time.time()
            )


CLUSTER_REGISTRY = ClusterRegistry()


def elect_leader() -> Optional[str]:
    nodes = CLUSTER_REGISTRY.list_nodes()
    if not nodes:
        logger.info("Cluster: no hay nodos para elegir líder.")
        return None
    leader = sorted(nodes, key=lambda n: n.node_id)[0]
    for n in nodes:
        n.is_leader = False
    leader.is_leader = True
    logger.info(f"Cluster: nuevo líder elegido {leader.node_id}")
    return leader.node_id


def _prune_dead_nodes() -> None:
    now = time.time()
    removed = []
    for n in CLUSTER_REGISTRY.list_nodes():
        if (now - n.last_heartbeat) > HEARTBEAT_TIMEOUT:
            removed.append(n.node_id)
    for nid in removed:
        CLUSTER_REGISTRY.unregister_node(nid)
        logger.warning(f"Cluster: nodo {nid} eliminado por timeout de heartbeat.")
        inc = block_d.INCIDENT_LOG.create(
            module="cluster", severity="critical", description=f"Node {nid} timed out"
        )
        block_d.autocure_incident("cluster", inc)


def _gather_critical_state() -> Dict[str, Any]:
    state = {}
    try:
        state["sensors"] = block_a.SENSOR_REGISTRY.snapshot().sensors.keys()
    except Exception:
        state["sensors"] = []
    try:
        state["alg_versions"] = [v.id for v in block_c.ALGO_REPO.list_versions()]
    except Exception:
        state["alg_versions"] = []
    try:
        state["health"] = {
            s.module: s.healthy for s in block_d.HEALTH_REGISTRY.list_all()
        }
    except Exception:
        state["health"] = {}
    state["timestamp"] = time.time()
    return state


def replicate_state_to_nodes() -> None:
    snapshot = CLUSTER_REGISTRY.snapshot()
    state = _gather_critical_state()
    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[1] / "data" / "cluster_state"
    base_dir.mkdir(parents=True, exist_ok=True)
    for n in snapshot.nodes.values():
        target = None
        if isinstance(n.metadata, dict):
            target = n.metadata.get("state_file")
        path = Path(target) if target else base_dir / f"{n.node_id}.json"
        try:
            path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.debug(f"Cluster: estado replicado en {path}")
        except Exception as e:
            logger.warning(f"Cluster: fallo replicando estado a {n.node_id}: {e}")
    logger.info("Cluster: replicación de estado completada.")


def perform_failover(failed_node_id: str) -> None:
    logger.warning(f"Cluster: iniciando failover por fallo en {failed_node_id}")
    snap = CLUSTER_REGISTRY.snapshot()
    if snap.leader_id == failed_node_id:
        logger.info("Cluster: líder caído, procediendo a nueva elección.")
        elect_leader()
    replicate_state_to_nodes()
    try:
        if hasattr(block_d, "_invoke_ha_hook"):
            inc = block_d.INCIDENT_LOG.create(
                module="cluster",
                severity="critical",
                description=f"Failover triggered for {failed_node_id}",
            )
            block_d._invoke_ha_hook("cluster", inc)
    except Exception as e:
        logger.warning(f"Cluster: error al invocar hook HA: {e}")


class LocalNodeAgent(threading.Thread):
    def __init__(
        self, host: str = "127.0.0.1", port: int = 0, metadata: Dict[str, Any] = None
    ) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port or 0
        self.metadata = metadata or {}
        self.node: Optional[NodeInfo] = None
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        self.node = CLUSTER_REGISTRY.register_node(
            host=self.host, port=self.port, metadata=self.metadata
        )
        try:
            while not self._stop.is_set():
                CLUSTER_REGISTRY.update_heartbeat(self.node.node_id)
                snap = CLUSTER_REGISTRY.snapshot()
                if snap.leader_id is None:
                    elect_leader()
                if self.node.is_leader:
                    replicate_state_to_nodes()
                _prune_dead_nodes()
                time.sleep(HEARTBEAT_INTERVAL)
        finally:
            if self.node:
                CLUSTER_REGISTRY.unregister_node(self.node.node_id)


def start_local_agent(
    host: str = "127.0.0.1", port: int = 0, metadata: Dict[str, Any] = None
) -> LocalNodeAgent:
    agent = LocalNodeAgent(host=host, port=port, metadata=metadata)
    agent.start()
    logger.info("Cluster: agente local iniciado.")
    return agent


def list_cluster_nodes() -> Dict[str, Any]:
    snap = CLUSTER_REGISTRY.snapshot()
    nodes = {
        nid: {
            "host": n.host,
            "port": n.port,
            "is_leader": n.is_leader,
            "last_heartbeat": n.last_heartbeat,
        }
        for nid, n in snap.nodes.items()
    }
    return {"nodes": nodes, "leader": snap.leader_id, "last_updated": snap.last_updated}


def get_cluster_state() -> ClusterStateSnapshot:
    return CLUSTER_REGISTRY.snapshot()


def force_election() -> Optional[str]:
    return elect_leader()


def trigger_manual_failover(node_id: str) -> None:
    perform_failover(node_id)


def smoke_test() -> None:
    logger.info("SMOKE TEST Bloque G: clustering y HA.")

    agents = [start_local_agent(metadata={"role": f"worker_{i}"}) for i in range(3)]
    time.sleep(1)

    leader = force_election()
    print("Líder elegido:", leader)

    print("Nodos del clúster (inicial):")
    print(json.dumps(list_cluster_nodes(), indent=2, ensure_ascii=False))

    if leader:
        leader_node = CLUSTER_REGISTRY.get_node(leader)
        if leader_node:
            print(f"Forzando caída del líder {leader}")
            leader_node.last_heartbeat = time.time() - (HEARTBEAT_TIMEOUT + 1)
            time.sleep(HEARTBEAT_INTERVAL * 2)
            _prune_dead_nodes()
            print("Nodos del clúster (tras caída forzada):")
            print(json.dumps(list_cluster_nodes(), indent=2, ensure_ascii=False))

    for a in agents:
        a.stop()
        a.join(timeout=2.0)


if __name__ == "__main__":
    smoke_test()

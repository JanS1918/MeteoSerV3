from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

# Importa tu algoritmo principal (meteoser.py) si existe
try:
    import meteoser as core  # tu archivo principal debe llamarse meteoser.py
except Exception:
    core = None

# Importa los bloques IA
from meteoser_ia import (
    block_a,
    block_b,
    block_c,
    block_d,
    block_e,
    block_f,
    block_g,
    block_h,
)

logger = logging.getLogger("meteoser_ia.integration")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter("[%(asctime)s] [INTEGRATION] [%(levelname)s] %(message)s")
    )
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


def initialize_integration(mock_mode: bool = True) -> None:
    mode = block_a.ExternalIntegrationMode.LIVE
    block_a.EXTERNAL_INTEGRATION_MODE = mode
    for mod in (block_c, block_d, block_e, block_f, block_g, block_h):
        try:
            setattr(mod, "EXTERNAL_INTEGRATION_MODE", mode)
        except Exception:
            pass
    logger.info(f"Integración inicializada en modo: {mode.value}")


def integration_status() -> Dict[str, Any]:
    status = {
        "core_present": core is not None,
        "blocks": {
            "A": True,
            "B": True,
            "C": True,
            "D": True,
            "E": True,
            "F": True,
            "G": True,
            "H": True,
        },
        "mode": block_a.EXTERNAL_INTEGRATION_MODE.value,
    }
    try:
        status["sensors_count"] = len(block_a.SENSOR_REGISTRY.snapshot().sensors)
    except Exception:
        status["sensors_count"] = None
    try:
        status["alg_versions"] = len(block_c.ALGO_REPO.list_versions())
    except Exception:
        status["alg_versions"] = None
    return status


def run_full_smoke_tests() -> Dict[str, Any]:
    report: Dict[str, Any] = {"timestamp": time.time(), "results": {}}

    try:
        snap = block_a.discover_all_sensors()
        report["results"]["block_a"] = {"sensors": len(snap.sensors)}
    except Exception as e:
        report["results"]["block_a"] = {"error": str(e)}

    try:
        block_b.register_default_rules()
        report["results"]["block_b"] = {"rules_registered": True}
    except Exception as e:
        report["results"]["block_b"] = {"error": str(e)}

    try:
        v = block_c.generate_algorithm_from_spec(
            {"objective": "integration_smoke", "inputs": ["temps"]}
        )
        metrics = block_c.evaluate_algorithm_version(v.id, [{"temps": [10, 11, 12]}])
        ext = block_c.validate_with_external_services(v.id)
        report["results"]["block_c"] = {
            "version": v.id,
            "metrics": metrics,
            "external_validation": ext,
        }
    except Exception as e:
        report["results"]["block_c"] = {"error": str(e)}

    try:
        wd = block_d.Watchdog(interval=1.0)
        wd.start()
        time.sleep(2)
        wd.stop()
        wd.join(timeout=2.0)
        report["results"]["block_d"] = {"watchdog_ran": True}
    except Exception as e:
        report["results"]["block_d"] = {"error": str(e)}

    try:
        recs = block_e.get_hardening_recommendations()
        report["results"]["block_e"] = {"hardening_recommendations": bool(recs)}
    except Exception as e:
        report["results"]["block_e"] = {"error": str(e)}

    try:
        sid = block_f.start_session(user_id="integration_smoke")
        out = block_f.handle_user_text(sid, "¿Qué me pongo hoy?")
        report["results"]["block_f"] = {"dialog_response": out.get("text")}
    except Exception as e:
        report["results"]["block_f"] = {"error": str(e)}

    try:
        agents = [
            block_g.start_local_agent(metadata={"role": f"smoke_{i}"}) for i in range(2)
        ]
        time.sleep(1)
        for a in agents:
            a.stop()
            a.join(timeout=2.0)
        report["results"]["block_g"] = {"agents_started": True}
    except Exception as e:
        report["results"]["block_g"] = {"error": str(e)}

    try:
        bk = block_h.create_backup(
            block_h.TARGET_MAIN_FILENAME, note="integration_smoke"
        )
        ok, issues = block_h.run_predeployment_checks()
        report["results"]["block_h"] = {
            "backup": bk.id,
            "predeploy_ok": ok,
            "issues": issues,
        }
    except Exception as e:
        report["results"]["block_h"] = {"error": str(e)}

    return report


def create_algorithm_and_deploy(
    spec: Dict[str, Any], test_inputs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        version = block_c.generate_algorithm_from_spec(spec)
        out["version_id"] = version.id
        out["evaluate"] = block_c.evaluate_algorithm_version(version.id, test_inputs)
        out["validate"] = block_c.validate_with_external_services(version.id)
        out["deploy"] = block_c.deploy_algorithm(version.id)
    except Exception as e:
        out["error"] = str(e)
    return out


def safe_deploy_latest_algorithm() -> Dict[str, Any]:
    try:
        versions = block_c.ALGO_REPO.list_versions()
        if not versions:
            return {"ok": False, "reason": "no_versions"}
        latest = sorted(versions, key=lambda v: v.timestamp)[-1]
        ok = block_c.deploy_algorithm(latest.id)
        return {"ok": ok, "version": latest.id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def attach_to_core_startup() -> None:
    if core is None:
        logger.warning(
            "No se detectó meteoser.py; no se puede adjuntar hooks de arranque."
        )
        return

    start_fn = getattr(core, "start", None)
    if callable(start_fn):

        def wrapped_start(*args, **kwargs):
            logger.info("Inicializando capa IA antes del arranque del core.")
            initialize_integration(mock_mode=True)
            try:
                block_a.discover_all_sensors()
            except Exception:
                pass
            return start_fn(*args, **kwargs)

        setattr(core, "start", wrapped_start)
        logger.info("Hook de arranque adjuntado a meteoser.start()")
    else:
        logger.info("meteoser.py no expone start(); no se adjuntó hook de arranque.")


def print_integration_report() -> None:
    st = integration_status()
    logger.info("Estado de integración:")
    for k, v in st.items():
        logger.info(f"  {k}: {v}")


if __name__ == "__main__":
    initialize_integration(mock_mode=True)
    print("Estado inicial:", integration_status())
    rpt = run_full_smoke_tests()
    import json

    print(json.dumps(rpt, indent=2, ensure_ascii=False))

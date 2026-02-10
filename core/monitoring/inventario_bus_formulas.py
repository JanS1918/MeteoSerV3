import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.monitoring.formula_catalog import FormulaCatalogo
from core.bus.formula_hierarchy import FORMULA_HIERARCHY


def _extraer_publicaciones(path: Path) -> List[str]:
    if not path.exists():
        return []
    texto = path.read_text(encoding="utf-8", errors="ignore")
    claves = set()
    for match in re.finditer(r"\.publicar\(\s*['\"]([^'\"]+)['\"]", texto):
        claves.add(match.group(1))
    for match in re.finditer(r"\.publicar_elite\(\s*['\"]([^'\"]+)['\"]", texto):
        claves.add(match.group(1))
    return sorted(claves)


def _serializar_formula(formula) -> Dict[str, Any]:
    return {
        "nivel": getattr(formula.nivel, "name", str(formula.nivel)),
        "nombre_tecnico": formula.nombre_tecnico,
        "nombre_legible": formula.nombre_legible,
        "modulo": formula.módulo,
        "referencia": formula.referencia,
        "precision": formula.precisión,
        "velocidad": formula.velocidad,
        "rango_validez": list(formula.rango_validez),
        "requisitos_datos": list(formula.requisitos_datos),
        "notas": formula.notas,
    }


def _inventario_formula_hierarchy() -> Dict[str, Any]:
    inventario = {}
    for parametro, jerarquia in FORMULA_HIERARCHY.items():
        inventario[parametro] = {
            "niveles": {
                nivel.name: _serializar_formula(formula)
                for nivel, formula in jerarquia.items()
            }
        }
    return inventario


def _inventario_catalogo_formulas() -> List[Dict[str, Any]]:
    catalogo = FormulaCatalogo()
    catalogo.cargar()
    return [_serializar_formula(f) for f in catalogo.obtener_todas()]


def _inventario_index_catalog() -> Dict[str, Any]:
    try:
        from core.indices.index_catalog import INDEX_CATALOG
    except Exception:
        INDEX_CATALOG = {}
    if not isinstance(INDEX_CATALOG, dict):
        return {}
    return {k: v for k, v in INDEX_CATALOG.items()}


def _inventario_sensores_virtuales() -> Dict[str, Any]:
    try:
        from core.indices.soluciones_auditoría_v49 import crear_sensores_virtuales_automaticos
    except Exception:
        return {}
    specs = crear_sensores_virtuales_automaticos()
    if not isinstance(specs, dict):
        return {}
    inventario = {}
    for vid, spec in specs.items():
        if not isinstance(spec, dict):
            continue
        inventario[vid] = {
            "descripcion": spec.get("descripcion"),
            "inputs": spec.get("inputs", []),
            "unidad": spec.get("unidad"),
            "confianza": spec.get("confianza"),
            "activo": spec.get("activo"),
            "categoria": spec.get("categoria"),
        }
    return inventario


def generar_inventario() -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parents[2]
    bus_expander_path = base_dir / "core" / "system" / "bus_expander.py"
    env_indices_path = base_dir / "core" / "indices" / "environmental_indices.py"
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    bus_publicaciones_detalle = {
        "core/system/bus_expander.py": _extraer_publicaciones(bus_expander_path),
        "core/indices/environmental_indices.py": _extraer_publicaciones(env_indices_path),
    }
    bus_publicaciones = sorted({
        clave
        for claves in bus_publicaciones_detalle.values()
        for clave in claves
    })

    inventario = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bus_publicaciones": bus_publicaciones,
        "bus_publicaciones_detalle": bus_publicaciones_detalle,
        "formula_hierarchy": _inventario_formula_hierarchy(),
        "formulas_catalogo": _inventario_catalogo_formulas(),
        "index_catalog": _inventario_index_catalog(),
        "sensores_virtuales": _inventario_sensores_virtuales(),
    }

    inventario["stats"] = {
        "bus_publicaciones": len(inventario["bus_publicaciones"]),
        "bus_publicaciones_bus_expander": len(bus_publicaciones_detalle["core/system/bus_expander.py"]),
        "bus_publicaciones_environmental_indices": len(bus_publicaciones_detalle["core/indices/environmental_indices.py"]),
        "parametros_hierarchy": len(inventario["formula_hierarchy"]),
        "formulas_catalogo": len(inventario["formulas_catalogo"]),
        "index_catalog": len(inventario["index_catalog"]),
        "sensores_virtuales": len(inventario["sensores_virtuales"]),
    }

    salida = data_dir / "inventario_bus_formulas.json"
    salida.write_text(json.dumps(inventario, ensure_ascii=False, indent=2), encoding="utf-8")
    return inventario


if __name__ == "__main__":
    generar_inventario()

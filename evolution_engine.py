# ============================================================
# MÓDULO 5 — AUTO‑EVOLUCIÓN
# Archivo: core/evolution/evolution_engine.py
# ============================================================
"""
Funciones seguras para auto‑evolución:
- crear carpetas/archivos nuevos siguiendo plantillas
- reorganizar estructura (mover archivos de forma controlada)
- generar/actualizar MANIFEST.md (documento maestro)
- registrar cambios en un log de evolución
- simular cambios en modo sandbox antes de aplicar
No realiza auto‑modificación de código ejecutable; solo gestión de archivos,
documentación y estructura. El módulo está pensado para ser llamado por un
operador o por un proceso supervisado.
"""

import os
import shutil
import json
import time
from typing import Dict, List, Optional, Tuple

MANIFEST_FILENAME = "MANIFEST.md"
EVOLUTION_LOG = "evolution_log.json"


# ------------------------------------------------------------
# UTILIDADES BÁSICAS
# ------------------------------------------------------------
def _now_ts() -> float:
    return time.time()


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _write_text(path: str, content: str):
    _ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_text(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------
# PLANTILLAS SIMPLES
# ------------------------------------------------------------
def template_py_module(name: str, description: str = "") -> str:
    return f'''# ============================================================
# Módulo generado: {name}
# Descripción: {description}
# Generado: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
# ============================================================

def info():
    return {{
        "module": "{name}",
        "description": "{description}"
    }}
'''


def template_manifest_entry(relpath: str, summary: str) -> str:
    return f"- **{relpath}** — {summary}\n"


# ------------------------------------------------------------
# CLASE EvolutionEngine
# ------------------------------------------------------------
class EvolutionEngine:
    """
    Motor de auto‑evolución (controlado).
    - base_path: carpeta raíz del proyecto (ej: meteoserV3/meteoser_ia)
    - sandbox: si True, simula cambios sin aplicarlos
    """

    def __init__(self, base_path: str, sandbox: bool = True):
        self.base_path = base_path.rstrip("/")
        self.sandbox = sandbox
        self.log_path = os.path.join(self.base_path, EVOLUTION_LOG)
        _ensure_dir(self.base_path)
        self._load_log()

    # -------------------------
    # LOG DE EVOLUCIÓN
    # -------------------------
    def _load_log(self):
        self.log: List[Dict] = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    self.log = json.load(f)
            except Exception:
                self.log = []

    def _append_log(self, action: str, details: Dict):
        entry = {"ts": _now_ts(), "action": action, "details": details}
        self.log.append(entry)
        if not self.sandbox:
            try:
                with open(self.log_path, "w", encoding="utf-8") as f:
                    json.dump(self.log, f, indent=2)
            except Exception:
                pass

    # -------------------------
    # MANIFEST (DOCUMENTO MAESTRO)
    # -------------------------
    def update_manifest(
        self, additions: List[Tuple[str, str]] = None, remove_paths: List[str] = None
    ):
        """
        Actualiza o crea MANIFEST.md en la raíz de base_path.
        - additions: lista de (ruta_relativa, resumen)
        - remove_paths: lista de rutas relativas a eliminar del manifiesto
        """
        manifest_path = os.path.join(self.base_path, MANIFEST_FILENAME)
        current = _read_text(manifest_path) or "# MANIFEST\n\n"
        lines = current.splitlines(keepends=True)

        # Simple: reconstruir manifest agregando nuevas entradas al final
        if remove_paths:
            # eliminar líneas que contengan las rutas indicadas (búsqueda simple)
            new_lines = []
            for ln in lines:
                if not any(rp in ln for rp in remove_paths):
                    new_lines.append(ln)
            lines = new_lines

        if additions:
            lines.append("\n## Nuevos elementos\n\n")
            for rel, summary in additions:
                lines.append(template_manifest_entry(rel, summary))

        new_content = "".join(lines)
        if self.sandbox:
            self._append_log(
                "manifest_preview",
                {"path": manifest_path, "content_preview": new_content[:1000]},
            )
            return new_content
        else:
            _write_text(manifest_path, new_content)
            self._append_log(
                "manifest_updated",
                {
                    "path": manifest_path,
                    "additions": additions or [],
                    "removed": remove_paths or [],
                },
            )
            return new_content

    # -------------------------
    # CREAR MÓDULOS Y ESTRUCTURA
    # -------------------------
    def create_module(
        self, rel_dir: str, module_name: str, description: str = ""
    ) -> str:
        """
        Crea un archivo .py con plantilla en rel_dir relativo a base_path.
        Devuelve la ruta completa del archivo (o la ruta simulada en sandbox).
        """
        target_dir = os.path.join(self.base_path, rel_dir)
        target_file = os.path.join(target_dir, f"{module_name}.py")
        content = template_py_module(module_name, description)

        if self.sandbox:
            self._append_log(
                "create_module_preview",
                {"target": target_file, "content_preview": content[:500]},
            )
            return target_file
        else:
            _ensure_dir(target_dir)
            _write_text(target_file, content)
            # crear __init__.py si no existe
            initp = os.path.join(target_dir, "__init__.py")
            if not os.path.exists(initp):
                _write_text(initp, "# package init\n")
            self._append_log("module_created", {"target": target_file})
            return target_file

    # -------------------------
    # MOVER / REORGANIZAR ARCHIVOS (CONTROLADO)
    # -------------------------
    def move_path(
        self, src_rel: str, dst_rel: str, allow_overwrite: bool = False
    ) -> Dict:
        """
        Mueve un archivo o carpeta de src_rel a dst_rel (relativos a base_path).
        Devuelve un dict con resultado. En sandbox no realiza el movimiento.
        """
        src = os.path.join(self.base_path, src_rel)
        dst = os.path.join(self.base_path, dst_rel)

        if not os.path.exists(src):
            result = {"ok": False, "reason": "src_not_found", "src": src_rel}
            self._append_log("move_failed", result)
            return result

        if os.path.exists(dst) and not allow_overwrite:
            result = {"ok": False, "reason": "dst_exists", "dst": dst_rel}
            self._append_log("move_failed", result)
            return result

        if self.sandbox:
            self._append_log("move_preview", {"src": src_rel, "dst": dst_rel})
            return {"ok": True, "preview": True, "src": src_rel, "dst": dst_rel}

        # aplicar movimiento
        try:
            _ensure_dir(os.path.dirname(dst) or ".")
            shutil.move(src, dst)
            self._append_log("moved", {"src": src_rel, "dst": dst_rel})
            return {"ok": True, "src": src_rel, "dst": dst_rel}
        except Exception as e:
            result = {"ok": False, "reason": "exception", "error": str(e)}
            self._append_log("move_failed", result)
            return result

    # -------------------------
    # GENERAR DOCUMENTACIÓN AUTOMÁTICA (BÁSICA)
    # -------------------------
    def generate_doc_for_module(self, rel_module_path: str) -> Optional[str]:
        """
        Lee un módulo .py y genera una sección de documentación en markdown.
        Devuelve el texto generado (o None si no existe).
        """
        full = os.path.join(self.base_path, rel_module_path)
        src = _read_text(full)
        if src is None:
            self._append_log(
                "doc_failed", {"module": rel_module_path, "reason": "not_found"}
            )
            return None

        # heurística simple: extraer primeras líneas de comentario y funciones top-level
        lines = src.splitlines()
        header_lines = []
        for ln in lines[:30]:
            if ln.strip().startswith("#"):
                header_lines.append(ln.strip("# ").rstrip())
            else:
                break
        # buscar definiciones de funciones y clases
        funcs = []
        for ln in lines:
            s = ln.strip()
            if s.startswith("def "):
                name = s.split("(")[0].replace("def ", "")
                funcs.append(name)
            if s.startswith("class "):
                name = s.split("(")[0].replace("class ", "")
                funcs.append(name)

        md = f"### Documentación automática: `{rel_module_path}`\n\n"
        if header_lines:
            md += "Descripción:\n\n" + "\n".join(header_lines) + "\n\n"
        if funcs:
            md += "Elementos detectados:\n\n"
            for f in funcs:
                md += f"- `{f}`\n"
        else:
            md += "No se detectaron funciones o clases top-level.\n"

        if self.sandbox:
            self._append_log(
                "doc_preview", {"module": rel_module_path, "doc_preview": md[:1000]}
            )
            return md
        else:
            docs_dir = os.path.join(self.base_path, "docs")
            _ensure_dir(docs_dir)
            out_path = os.path.join(docs_dir, rel_module_path.replace("/", "_") + ".md")
            _write_text(out_path, md)
            self._append_log(
                "doc_generated", {"module": rel_module_path, "out": out_path}
            )
            return md

    # -------------------------
    # APLICAR CAMBIOS EN LOTE (OPERACIÓN ATÓMICA SIMULADA)
    # -------------------------
    def apply_plan(self, plan: List[Dict]) -> List[Dict]:
        """
        plan: lista de acciones con formato:
        {"action":"create_module","rel_dir":"core/new","module_name":"m1","description":"..."}
        {"action":"move","src":"old.py","dst":"new.py"}
        {"action":"update_manifest","additions":[("path","sum")]}
        Devuelve lista de resultados por acción.
        """
        results = []
        # si sandbox está activado, solo previsualizar
        original_sandbox = self.sandbox
        try:
            for act in plan:
                a = act.get("action")
                if a == "create_module":
                    res = {
                        "action": a,
                        "target": self.create_module(
                            act.get("rel_dir", ""),
                            act.get("module_name", ""),
                            act.get("description", ""),
                        ),
                    }
                elif a == "move":
                    res = {
                        "action": a,
                        "result": self.move_path(
                            act.get("src", ""),
                            act.get("dst", ""),
                            act.get("allow_overwrite", False),
                        ),
                    }
                elif a == "update_manifest":
                    res = {
                        "action": a,
                        "result": self.update_manifest(
                            additions=act.get("additions"),
                            remove_paths=act.get("remove_paths"),
                        ),
                    }
                elif a == "generate_doc":
                    res = {
                        "action": a,
                        "doc": self.generate_doc_for_module(
                            act.get("rel_module_path", "")
                        ),
                    }
                else:
                    res = {"action": a, "error": "unknown_action"}
                results.append(res)
            # si no sandbox, persistir log ya se hace en cada operación
            return results
        finally:
            self.sandbox = original_sandbox


# ============================================================
# FIN DEL MÓDULO
# ============================================================

"""
VANGUARD OJEADOR V34.1
- Descubre fórmulas en el sistema
- Escanea fuentes públicas (arXiv, Crossref, PyPI, GitHub opcional)
- Ordena alertas por uso y mejora
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import feedparser
import requests

from core.bus.formula_hierarchy import FORMULA_HIERARCHY
from core.bus.parametros_canonicos import (
    normalizar_lista_parametros_entrada,
    normalizar_parametro_bus,
)
from core.indices.bus_estado_global import BusEstadoGlobal
from core.monitoring.formula_comparator import FormulaComparator

logger = logging.getLogger("meteoser.vanguard_ojeador")

REQUEST_TIMEOUT = (1, 2)  # (conexión, lectura) en segundos
MAX_SOURCE_SECONDS = 3
MAX_SCAN_SECONDS = 20


@dataclass
class FormulaEntry:
    nombre: str
    modulo: str
    referencia: str
    descripcion: str
    categoria: str


class FormulaDiscovery:
    def __init__(self, workspace: Path):
        self.workspace = workspace

    def discover_from_registry(self) -> List[FormulaEntry]:
        entries: List[FormulaEntry] = []
        for param, niveles in FORMULA_HIERARCHY.items():
            for formula in niveles.values():
                entries.append(
                    FormulaEntry(
                        nombre=formula.nombre_legible,
                        modulo=formula.módulo,
                        referencia=formula.referencia,
                        descripcion=formula.notas,
                        categoria=param,
                    )
                )
        return entries

    def discover_from_code(self) -> List[FormulaEntry]:
        entries: List[FormulaEntry] = []
        search_paths = [self.workspace / "core"]
        for base in search_paths:
            for py_file in base.rglob("*.py"):
                if "__pycache__" in py_file.parts:
                    continue
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if self._is_formula_function(node):
                            entries.append(
                                FormulaEntry(
                                    nombre=node.name,
                                    modulo=str(py_file.relative_to(self.workspace)).replace("\\", "/"),
                                    referencia="local",
                                    descripcion=ast.get_docstring(node) or "",
                                    categoria="auto",
                                )
                            )
        return entries

    def _is_formula_function(self, node: ast.FunctionDef) -> bool:
        name = node.name.lower()
        if any(k in name for k in ["indice", "calculo", "formula", "punto", "densidad", "radiacion", "utci", "et0", "evap", "viento", "humedad", "presion"]):
            return True
        # Heurística: contiene operaciones aritméticas
        for child in ast.walk(node):
            if isinstance(child, (ast.BinOp, ast.Call)):
                return True
        return False


class VanguardOjeador:
    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path(__file__).resolve().parents[2]
        self.state_path = self.workspace / "data" / "vanguard_state.json"
        self.alerts_path = self.workspace / "data" / "vanguard_alerts.json"
        self.discovery = FormulaDiscovery(self.workspace)
        self.comparator = FormulaComparator()
        self.last_run = None
        self.alerts: List[Dict] = []
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self.last_run = data.get("last_run")
            except Exception:
                self.last_run = None
        if self.alerts_path.exists():
            try:
                self.alerts = json.loads(self.alerts_path.read_text(encoding="utf-8"))
            except Exception:
                self.alerts = []

    def _save_state(self):
        self.state_path.write_text(
            json.dumps({"last_run": self.last_run}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.alerts_path.write_text(
            json.dumps(self.alerts, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_due(self) -> bool:
        if not self.last_run:
            return True
        try:
            last = datetime.fromisoformat(self.last_run)
        except Exception:
            return True
        return datetime.now() - last >= timedelta(days=7)

    def run_if_due(self) -> List[Dict]:
        if not self.is_due():
            return self.alerts
        return self.run_scan()

    def run_scan(self) -> List[Dict]:
        from core.bus.formula_hierarchy import FORMULA_HIERARCHY, NivelElite
        from core.indices.bus_estado_global import BusEstadoGlobal

        bus = BusEstadoGlobal.obtener_instancia()
        bus_vars = set((bus.obtener_todas_variables() or {}).keys())
        entries = self.discovery.discover_from_registry()
        entries += self.discovery.discover_from_code()
        seen = set()
        unique_entries = []
        for e in entries:
            key = (e.nombre, e.modulo)
            if key in seen:
                continue
            seen.add(key)
            unique_entries.append(e)

        alerts = []
        # Construir un mapa de nivel actual por categoría
        nivel_actual_por_cat = {}
        for param, niveles in FORMULA_HIERARCHY.items():
            max_nivel = max(niveles.keys(), key=lambda n: n.value)
            nivel_actual_por_cat[param] = niveles[max_nivel]

        scan_deadline = time.monotonic() + MAX_SCAN_SECONDS
        for entry in unique_entries:
            if time.monotonic() > scan_deadline:
                break
            categoria = entry.categoria
            if categoria and categoria != "auto":
                categoria = normalizar_parametro_bus(categoria)
                if not self._categoria_tiene_datos(categoria, bus_vars):
                    logger.warning(
                        "⚠️ Vanguard: datos insuficientes para '%s' (saltando sugerencias)",
                        categoria,
                    )
                    continue
            candidates = self._search_sources(entry)
            # Buscar la fórmula "actual" más precisa para la categoría
            actual_formula = nivel_actual_por_cat.get(categoria or entry.categoria)
            actual_prec = None
            actual_vel = None
            if actual_formula:
                actual_prec = actual_formula.precisión
                actual_vel = actual_formula.velocidad
            for cand in candidates:
                comparison = self.comparator.comparar(
                    {"referencia": entry.referencia},
                    cand
                )
                mejora = comparison.get("mejora_estimadapct", 0.0)
                # Obtener precisión y velocidad de la candidata si están disponibles
                cand_prec = cand.get("precisión")
                cand_vel = cand.get("velocidad")
                # Solo sugerir si hay mejora REAL de precisión (menor valor numérico)
                sugerir = False
                if actual_prec and cand_prec:
                    try:
                        # Extraer el valor numérico de precisión (ej: '±0.001°C' -> 0.001)
                        def parse_prec(p):
                            return float(p.replace("±", "").replace("°C", "").replace("C", "").strip())
                        prec_actual_val = parse_prec(actual_prec)
                        prec_cand_val = parse_prec(cand_prec)
                        if prec_cand_val < prec_actual_val:
                            sugerir = True
                    except Exception:
                        sugerir = False
                if sugerir:
                    alerts.append({
                        "formula": entry.nombre,
                        "modulo": entry.modulo,
                        "categoria": entry.categoria,
                        "titulo": cand.get("titulo"),
                        "referencia": cand.get("referencia"),
                        "resumen": cand.get("resumen"),
                        "fuente": cand.get("fuente"),
                        "mejora_estimadapct": mejora,
                        "beneficios": comparison.get("beneficios"),
                        "riesgos": comparison.get("riesgos"),
                        "timestamp": datetime.now().isoformat(),
                        "precisión": cand_prec,
                        "velocidad": cand_vel,
                    })

        self.alerts = self._ordenar_alertas(alerts)
        self.last_run = datetime.now().isoformat()
        self._save_state()
        return self.alerts

    def _categoria_tiene_datos(self, categoria: str, bus_vars: set) -> bool:
        if not categoria:
            return False
        jerarquia = FORMULA_HIERARCHY.get(categoria)
        if not jerarquia:
            return False
        if not bus_vars:
            return True
        for formula in jerarquia.values():
            requisitos = normalizar_lista_parametros_entrada(formula.requisitos_datos)
            if all(req in bus_vars for req in requisitos):
                return True
        return False

    def _ordenar_alertas(self, alerts: List[Dict]) -> List[Dict]:
        bus = BusEstadoGlobal.obtener_instancia()
        stats = bus.obtener_estadisticas()
        uso = {item["variable"]: item["accesos"] for item in stats.get("top_reutilizadas", [])}

        def score(alert: Dict) -> float:
            uso_score = uso.get(alert.get("formula"), 0)
            mejora = alert.get("mejora_estimadapct", 0.0)
            return (uso_score * 1.2) + (mejora * 10)

        return sorted(alerts, key=score, reverse=True)

    def get_top_alerts(self, offset: int = 0, limit: int = 5) -> Dict:
        total = len(self.alerts)
        sliced = self.alerts[offset: offset + limit]
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": sliced,
        }

    def resumen(self) -> Dict:
        return {
            "last_run": self.last_run,
            "total_alertas": len(self.alerts),
        }

    def _search_sources(self, entry: FormulaEntry) -> List[Dict]:
        terms = self._build_terms(entry)
        results: List[Dict] = []
        start = time.monotonic()
        results += self._search_arxiv(terms)
        if time.monotonic() - start > MAX_SOURCE_SECONDS:
            return self._filter_and_dedupe_results(results, entry)
        results += self._search_crossref(terms)
        if time.monotonic() - start > MAX_SOURCE_SECONDS:
            return self._filter_and_dedupe_results(results, entry)
        results += self._search_pypi(terms)
        if time.monotonic() - start > MAX_SOURCE_SECONDS:
            return self._filter_and_dedupe_results(results, entry)
        results += self._search_github(terms)
        return self._filter_and_dedupe_results(results, entry)

    def _build_terms(self, entry: FormulaEntry) -> str:
        parts = [entry.nombre, entry.categoria, entry.referencia]
        return " ".join([p for p in parts if p]).strip()

    def _filter_and_dedupe_results(self, results: List[Dict], entry: FormulaEntry) -> List[Dict]:
        # Palabras clave para relevancia
        keywords = set(re.findall(r"[a-zA-Z0-9]+", self._build_terms(entry).lower()))
        keywords = {k for k in keywords if len(k) >= 4}

        deduped = []
        seen = set()
        for item in results:
            titulo = (item.get("titulo") or "").strip()
            resumen = (item.get("resumen") or "").strip()
            referencia = (item.get("referencia") or "").strip()
            fuente = (item.get("fuente") or "").strip()

            key = (titulo.lower(), referencia.lower(), fuente.lower())
            if key in seen:
                continue

            text = f"{titulo} {resumen} {referencia}".lower()
            tokens = set(re.findall(r"[a-zA-Z0-9]+", text))
            if keywords and not (tokens & keywords):
                continue

            seen.add(key)
            deduped.append(item)

        return deduped

    def _search_arxiv(self, terms: str) -> List[Dict]:
        try:
            url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{terms}",
                "start": 0,
                "max_results": 3,
            }
            feed = feedparser.parse(requests.get(url, params=params, timeout=REQUEST_TIMEOUT).text)
            results = []
            for entry in feed.entries:
                results.append({
                    "titulo": entry.get("title"),
                    "referencia": entry.get("id"),
                    "resumen": entry.get("summary"),
                    "fuente": "arXiv",
                })
            return results
        except Exception:
            return []

    def _search_crossref(self, terms: str) -> List[Dict]:
        try:
            url = "https://api.crossref.org/works"
            params = {"query": terms, "rows": 3}
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            results = []
            for item in items:
                title = (item.get("title") or [""])[0]
                doi = item.get("DOI")
                results.append({
                    "titulo": title,
                    "referencia": doi or item.get("URL"),
                    "resumen": item.get("container-title", [""])[0],
                    "fuente": "Crossref",
                })
            return results
        except Exception:
            return []

    def _search_pypi(self, terms: str) -> List[Dict]:
        packages = ["metpy", "teos-10", "iapws"]
        results = []
        for pkg in packages:
            try:
                url = f"https://pypi.org/pypi/{pkg}/json"
                resp = requests.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                info = data.get("info", {})
                desc = (info.get("summary") or "")
                if terms.lower()[:6] not in (desc.lower() + pkg):
                    # uso heurístico: solo si términos principales se encuentran
                    pass
                results.append({
                    "titulo": f"PyPI {pkg} {info.get('version')}",
                    "referencia": info.get("project_url") or info.get("home_page"),
                    "resumen": desc,
                    "fuente": "PyPI",
                })
            except Exception:
                continue
        return results

    def _search_github(self, terms: str) -> List[Dict]:
        token = os.getenv("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            url = "https://api.github.com/search/code"
            params = {"q": terms, "per_page": 3}
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "titulo": item.get("name"),
                    "referencia": item.get("html_url"),
                    "resumen": item.get("repository", {}).get("full_name"),
                    "fuente": "GitHub",
                })
            return results
        except Exception:
            return []

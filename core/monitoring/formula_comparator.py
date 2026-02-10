"""
COMPARADOR DE FÓRMULAS V34.1
Evalúa beneficios y riesgos entre fórmula actual y candidata.
"""
from __future__ import annotations

from typing import Dict, List

AUTHORITY_SCORE = {
    "NIST": 10,
    "WMO": 9,
    "OMM": 9,
    "IAPWS": 9,
    "ISO": 8,
    "ASCE": 8,
    "FAO": 7,
    "NASA": 8,
    "NOAA": 7,
    "METPY": 6,
    "ARXIV": 5,
}

KEYWORDS_UPGRADE = ["improved", "updated", "revision", "standard", "enhanced", "v2", "v3", "202", "2024", "2025", "2026"]
KEYWORDS_RISK = ["preprint", "experimental", "draft", "unverified", "beta"]


def _score_authority(text: str) -> int:
    text = (text or "").upper()
    for key, score in AUTHORITY_SCORE.items():
        if key in text:
            return score
    return 5


def _score_upgrade(text: str) -> int:
    text_low = (text or "").lower()
    return sum(1 for k in KEYWORDS_UPGRADE if k in text_low)


def _score_risk(text: str) -> int:
    text_low = (text or "").lower()
    return sum(1 for k in KEYWORDS_RISK if k in text_low)


class FormulaComparator:
    def comparar(self, actual: Dict, candidata: Dict) -> Dict:
        actual_ref = actual.get("referencia", "")
        cand_ref = candidata.get("referencia", "")
        cand_title = candidata.get("titulo", "")
        cand_summary = candidata.get("resumen", "")

        score_actual = _score_authority(actual_ref)
        score_cand = max(_score_authority(cand_ref), _score_authority(cand_title))
        upgrade = _score_upgrade(cand_title + " " + cand_summary)
        risk = _score_risk(cand_title + " " + cand_summary)

        mejora = max(0.0, (score_cand - score_actual) * 1.5 + upgrade * 0.5 - risk * 1.0)
        mejora = min(15.0, mejora)

        beneficios = []
        riesgos = []
        if score_cand > score_actual:
            beneficios.append("Mayor autoridad científica (estándar superior)")
        if upgrade > 0:
            beneficios.append("Referencia reciente con mejoras documentadas")
        if risk > 0:
            riesgos.append("Fuente con indicios de revisión preliminar")
        if score_cand == score_actual:
            beneficios.append("Equivalencia de autoridad (posible optimización menor)")

        return {
            "score_actual": score_actual,
            "score_candidata": score_cand,
            "mejora_estimadapct": round(mejora, 2),
            "beneficios": beneficios,
            "riesgos": riesgos,
        }

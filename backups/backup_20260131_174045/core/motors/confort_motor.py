from typing import Dict, Any

class MotorConfort:
    def calcular_indice(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: calcular confort usando índices
        indices = datos.get("indices", {}) if isinstance(datos, dict) else {}
        resultado = {"indice_confort": None, "detalles": {}}

        confort = indices.get("confort_general", {}).get("valor")
        bochorno = indices.get("bochorno_real", {}).get("valor")
        aire_seco = indices.get("aire_seco", {}).get("valor")
        aire_pegajoso = indices.get("aire_pegajoso", {}).get("valor")

        score = 100.0
        for v in [bochorno, aire_seco, aire_pegajoso]:
            if v is not None:
                score -= float(v) * 0.3
        if confort is not None:
            score = (score + float(confort)) / 2.0

        resultado["indice_confort"] = round(max(0.0, min(100.0, score)), 2)
        resultado["detalles"] = {
            "confort_general": confort,
            "bochorno": bochorno,
            "aire_seco": aire_seco,
            "aire_pegajoso": aire_pegajoso,
        }
        return resultado

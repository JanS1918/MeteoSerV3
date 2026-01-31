from typing import Dict, Any, Optional, List


def mejor_valor_indices(indices: Dict[str, dict], candidatos: List[str], fallback: Optional[Any] = None) -> Optional[Any]:
    """
    Retorna el primer `valor` disponible en `indices` según el orden en `candidatos`.

    - `indices` es un diccionario donde cada clave apunta a un dict con clave 'valor'.
    - `candidatos` es la lista de claves a probar en orden de preferencia.
    - `fallback` se retorna si ninguna clave tiene valor.
    """
    if not isinstance(indices, dict):
        return fallback
    for clave in candidatos:
        entry = indices.get(clave)
        if isinstance(entry, dict):
            val = entry.get("valor")
            if val is not None:
                return val
    return fallback


def mejor_entrada_indices(indices: Dict[str, dict], candidatos: List[str]) -> Optional[Dict[str, Any]]:
    """
    Retorna la primera entrada (dict) disponible entre `candidatos`, o None.
    """
    if not isinstance(indices, dict):
        return None
    for clave in candidatos:
        entry = indices.get(clave)
        if isinstance(entry, dict) and entry.get("valor") is not None:
            return entry
    return None

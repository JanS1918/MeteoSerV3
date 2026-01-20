from typing import Dict, Any

class MotorListaCompra:
    def gestionar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver lista de compra local
        lista = datos.get("lista_compra", []) if isinstance(datos, dict) else []
        return {"lista_compra": lista, "total": len(lista)}

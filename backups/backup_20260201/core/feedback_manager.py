# Sistema de feedback y aprendizaje de predicciones
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

class FeedbackManager:
    """Gestiona el feedback del usuario sobre predicciones e índices."""
    
    def __init__(self, historial_path: str = "data/feedback_registros.jsonl"):
        self.historial_path = Path(historial_path)
        self.historial_path.parent.mkdir(parents=True, exist_ok=True)
        self.confianza_indices: Dict[str, float] = {}
        self.feedback_reciente: List[Dict[str, Any]] = []
        self._cargar_confianza()
    
    def _cargar_confianza(self):
        """Carga los factores de confianza desde el historial."""
        try:
            if self.historial_path.exists():
                with open(self.historial_path, 'r', encoding='utf-8') as f:
                    for linea in f:
                        registro = json.loads(linea)
                        nombre = registro.get('nombre_indice')
                        if nombre and nombre not in self.confianza_indices:
                            self.confianza_indices[nombre] = 0.8  # Confianza inicial
        except Exception as e:
            print(f"Error cargando confianza: {e}")
    
    def registrar_feedback(self, nombre_indice: str, valor_predicho: float, valor_real: float, 
                          es_correcto: bool, comentario: Optional[str] = None) -> Dict[str, Any]:
        """Registra feedback del usuario sobre una predicción."""
        
        # Calcular error
        error = abs(valor_predicho - valor_real)
        error_relativo = error / max(abs(valor_real), 1.0)
        
        # Ajustar confianza
        if nombre_indice not in self.confianza_indices:
            self.confianza_indices[nombre_indice] = 0.8
        
        confianza_actual = self.confianza_indices[nombre_indice]
        
        # Factor de aprendizaje adaptativo
        factor_aprendizaje = 0.1 if len(self.feedback_reciente) < 10 else 0.05
        
        if es_correcto:
            # Aumentar confianza
            nueva_confianza = min(1.0, confianza_actual + factor_aprendizaje * (1 - error_relativo))
        else:
            # Disminuir confianza
            nueva_confianza = max(0.1, confianza_actual - factor_aprendizaje * (1 + error_relativo))
        
        self.confianza_indices[nombre_indice] = nueva_confianza
        
        # Crear registro
        registro = {
            'nombre_indice': nombre_indice,
            'valor_predicho': valor_predicho,
            'valor_real': valor_real,
            'error': error,
            'error_relativo': error_relativo,
            'es_correcto': es_correcto,
            'comentario': comentario,
            'confianza_anterior': confianza_actual,
            'confianza_nueva': nueva_confianza,
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar en historial
        self._guardar_registro(registro)
        self.feedback_reciente.append(registro)
        if len(self.feedback_reciente) > 100:
            self.feedback_reciente = self.feedback_reciente[-100:]
        
        return registro
    
    def _guardar_registro(self, registro: Dict[str, Any]):
        """Guarda un registro de feedback en el archivo."""
        try:
            with open(self.historial_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(registro, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error guardando feedback: {e}")
    
    def obtener_confianza(self, nombre_indice: str) -> float:
        """Obtiene el factor de confianza actual de un índice."""
        return self.confianza_indices.get(nombre_indice, 0.8)
    
    def obtener_estadisticas(self, nombre_indice: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene estadísticas de feedback."""
        if nombre_indice:
            registros = [r for r in self.feedback_reciente if r['nombre_indice'] == nombre_indice]
        else:
            registros = self.feedback_reciente
        
        if not registros:
            return {'total': 0, 'correctos': 0, 'incorrectos': 0, 'precision': 0.0}
        
        total = len(registros)
        correctos = sum(1 for r in registros if r['es_correcto'])
        incorrectos = total - correctos
        precision = correctos / total if total > 0 else 0.0
        
        return {
            'total': total,
            'correctos': correctos,
            'incorrectos': incorrectos,
            'precision': precision,
            'confianza_actual': self.confianza_indices.get(nombre_indice, 0.8) if nombre_indice else None
        }
    
    def obtener_feedback_reciente(self, limite: int = 20) -> List[Dict[str, Any]]:
        """Obtiene los registros de feedback más recientes."""
        return self.feedback_reciente[-limite:]

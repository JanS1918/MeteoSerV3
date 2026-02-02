# Motor de recomendaciones dinámicas para la UI
from typing import Dict, List, Any, Optional
from datetime import datetime

class RecomendacionesMotor:
    """Genera recomendaciones dinámicas basadas en contexto y estado del sistema."""
    
    def __init__(self):
        self.recomendaciones_cache: List[str] = []
    
    def generar_recomendaciones(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera recomendaciones coloquiales y contextuales.
        
        Args:
            contexto: Dict con sensores, índices, arco solar/lunar, predicciones
        
        Returns:
            Dict con texto de recomendación, iconos y detalles
        """
        sensores = contexto.get('sensores', {})
        indices = contexto.get('indices', {})
        arco = contexto.get('arco_solar', {})
        es_de_dia = arco.get('es_de_dia', True)
        
        recomendaciones = []
        iconos = []
        
        # Obtener valores clave
        temp = self._get_valor(sensores, 'temperatura')
        humedad = self._get_valor(sensores, 'humedad')
        lluvia_prob = self._get_valor(indices, 'probabilidad_lluvia')
        viento = self._get_valor(sensores, 'viento')
        radiacion = self._get_valor(indices, 'radiacion_uv')
        
        # Recomendaciones de temperatura
        if temp is not None:
            if temp < 10:
                recomendaciones.append("Hace frío, mejor abrígate bien")
                iconos.append('coat')
            elif temp < 15:
                recomendaciones.append("Temperatura fresca, lleva una chaqueta")
                iconos.append('jacket')
            elif temp > 30:
                recomendaciones.append("Hace mucho calor, hidrátate bien")
                iconos.append('water')
        
        # Recomendaciones de lluvia
        if lluvia_prob is not None and lluvia_prob > 60:
            recomendaciones.append("Lleva paraguas, hay riesgo de lluvia")
            iconos.append('umbrella')
        
        # Recomendaciones de viento
        if viento is not None and viento > 30:
            recomendaciones.append("Mucho viento, cuidado con objetos sueltos")
            iconos.append('wind_warning')
        
        # Recomendaciones de radiación UV
        if radiacion is not None and radiacion > 6 and es_de_dia:
            recomendaciones.append("Radiación UV alta, usa protección solar")
            iconos.append('sun_protection')
        
        # Recomendaciones nocturnas
        if not es_de_dia:
            if temp is not None and temp < 15:
                recomendaciones.append("Noche fresca, cierra bien las ventanas")
                iconos.append('window_close')
            elif humedad is not None and humedad > 80:
                recomendaciones.append("Humedad alta esta noche, vigila la condensación")
                iconos.append('humidity_warning')
        
        # Recomendaciones de ventilación
        if humedad is not None and temp is not None:
            if humedad > 70 and temp > 20 and es_de_dia:
                recomendaciones.append("Buen momento para ventilar la casa")
                iconos.append('ventilation')
        
        # Si no hay recomendaciones específicas
        if not recomendaciones:
            if es_de_dia:
                recomendaciones.append("Condiciones normales, disfruta del día")
                iconos.append('check')
            else:
                recomendaciones.append("Buenas condiciones para descansar")
                iconos.append('sleep')
        
        # Texto unificado
        texto_unificado = ". ".join(recomendaciones) + "."
        
        self.recomendaciones_cache = recomendaciones
        
        return {
            'texto': texto_unificado,
            'recomendaciones': recomendaciones,
            'iconos': iconos,
            'es_nocturno': not es_de_dia,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_valor(self, datos: Dict[str, Any], clave_parcial: str) -> Optional[float]:
        """Obtiene un valor del dict, buscando por clave parcial."""
        for key, value in datos.items():
            if clave_parcial.lower() in key.lower():
                if isinstance(value, dict):
                    return value.get('valor', value.get('value'))
                return value
        return None

# viewmodel.py
# ViewModel para la nueva interfaz MeteoSer

from typing import Dict, List, Any, Optional
from core.data_model import ValorSistema, GrupoValores, JerarquiaUI
from core.context.fallback_universal import obtener_fallback_universal, EstadoFisico
from core.fiabilidad_manager import FiabilidadManager
from core.arcos_solares import calcular_posicion_sol, calcular_fase_lunar, calcular_posicion_luna
from core.recomendaciones_motor import RecomendacionesMotor
from datetime import datetime

class PanelViewModel:
    """
    Clase base para la lógica de presentación del panel.
    Gestiona la jerarquía, cajones, valores y submenús.
    """
    
    def __init__(self, fiabilidad_mgr: Optional[FiabilidadManager] = None):
        self.fiabilidad_mgr = fiabilidad_mgr or FiabilidadManager()
        self.recomendaciones_motor = RecomendacionesMotor()
        self.jerarquia: Optional[JerarquiaUI] = None
        self.cajones: List[Dict[str, Any]] = []
        self.configuracion_cajones: Dict[str, Dict[str, Any]] = {}
        
    def inicializar_jerarquia(self, grupos: List[GrupoValores]):
        """Inicializa la jerarquía de valores desde los grupos."""
        self.jerarquia = JerarquiaUI(grupos)
        self._generar_cajones()
    
    def _generar_cajones(self):
        """Genera la estructura de cajones desde la jerarquía."""
        if not self.jerarquia:
            return
        
        self.cajones = []
        for grupo in self.jerarquia.grupos[:6]:  # Máximo 6 cajones
            # Obtener los 2 valores más prioritarios para la tapa
            valores_tapa = grupo.valores[:2]
            
            cajon = {
                'id': f"cajon_{grupo.nombre.lower().replace(' ', '_')}",
                'nombre': grupo.nombre,
                'icono': grupo.icono,
                'prioridad': grupo.prioridad,
                'valores_tapa': [self._serializar_valor(v) for v in valores_tapa],
                'valores_completos': [self._serializar_valor(v) for v in grupo.valores],
                'total_valores': len(grupo.valores)
            }
            self.cajones.append(cajon)
            self.configuracion_cajones[cajon['id']] = {
                'nombre_custom': grupo.nombre,
                'posicion': len(self.cajones) - 1
            }
    
    def _serializar_valor(self, valor: ValorSistema) -> Dict[str, Any]:
        """Serializa un ValorSistema para la UI."""
        return {
            'nombre': valor.nombre,
            'tipo': valor.tipo,
            'valor': valor.valor,
            'unidad': valor.unidad,
            'fiabilidad': valor.fiabilidad.value if hasattr(valor.fiabilidad, 'value') else valor.fiabilidad,
            'icono': valor.icono,
            'prioridad': valor.prioridad,
            'alerta': valor.alerta,
            'tiene_alerta': valor.alerta is not None
        }
    
    def obtener_panel_superior(self, lat: float, lon: float, estacion: str) -> Dict[str, Any]:
        """Genera los datos para el panel superior fijo."""
        fecha_actual = datetime.now()
        
        return {
            'nombre_sistema': 'MeteoSer',
            'ubicacion': {
                'latitud': lat,
                'longitud': lon,
                'poblacion': 'Argentona'  # Obtener dinámicamente en producción
            },
            'estacion': estacion,
            'fecha': fecha_actual.strftime('%d/%m/%Y'),
            'hora': fecha_actual.strftime('%H:%M'),
            'timestamp': fecha_actual.isoformat()
        }
    
    def obtener_arcos_solares(self, lat: float, lon: float, nubosidad: Optional[float] = None) -> Dict[str, Any]:
        """Genera los datos para los arcos solar y lunar."""
        fecha_actual = datetime.now()
        
        # Calcular posición del sol
        datos_sol = calcular_posicion_sol(lat, lon, fecha_actual)
        
        # Calcular fase lunar
        datos_luna = calcular_fase_lunar(fecha_actual)
        
        # Calcular posición de la luna
        posicion_luna = calcular_posicion_luna(
            fecha_actual,
            datos_sol['amanecer'],
            datos_sol['anochecer'],
            datos_sol['es_de_dia']
        )
        
        return {
            'sol': {
                'posicion': datos_sol['posicion_sol'],
                'amanecer': datos_sol['amanecer'],
                'anochecer': datos_sol['anochecer'],
                'duracion_dia': datos_sol['duracion_dia'],
                'es_de_dia': datos_sol['es_de_dia'],
                'nublado': nubosidad is not None and nubosidad > 50
            },
            'luna': {
                'posicion': posicion_luna,
                'fase': datos_luna['fase'],
                'nombre_fase': datos_luna['nombre'],
                'icono': datos_luna['icono'],
                'duracion_noche': datos_sol['duracion_noche']
            }
        }
    
    def obtener_panel_central(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera los datos para el panel central (recomendaciones y sensación)."""
        sensores = contexto.get('sensores', {})
        indices = contexto.get('indices', {})
        
        # Generar recomendaciones
        recomendaciones = self.recomendaciones_motor.generar_recomendaciones(contexto)
        
        # Obtener valores clave
        temperatura = self._extraer_valor(sensores, 'temperatura')
        humedad = self._extraer_valor(sensores, 'humedad')
        presion = self._extraer_valor(sensores, 'presion')
        viento = self._extraer_valor(sensores, 'viento')
        
        # ⚡ LEY DEL ENTERO: Forzar INT si el valor es redondo (sin decimales)
        def _forzar_int_si_redondo(dict_valor):
            if dict_valor and isinstance(dict_valor, dict) and 'valor' in dict_valor:
                val = dict_valor['valor']
                try:
                    if isinstance(val, float) and val == int(val):
                        dict_valor['valor'] = int(val)
                except Exception:
                    pass
            return dict_valor
        
        humedad = _forzar_int_si_redondo(humedad)
        viento = _forzar_int_si_redondo(viento)
        presion = _forzar_int_si_redondo(presion)
        
        # Sensación térmica (UTCI)
        utci_edificio = self._extraer_valor(indices, 'utci_edificio')
        utci_persona = self._extraer_valor(indices, 'utci_persona')
        
        sensacion = {
            'unificado': utci_edificio == utci_persona if (utci_edificio and utci_persona) else True,
            'edificio': utci_edificio,
            'persona': utci_persona
        }
        
        return {
            'recomendaciones': recomendaciones,
            'temperatura': temperatura,
            'humedad': humedad,
            'presion': presion,
            'viento': viento,
            'sensacion': sensacion,
            'estado_tiempo': self._detectar_estado_tiempo(sensores, indices)
        }
    
    def _detectar_estado_tiempo(self, sensores: Dict, indices: Dict) -> Dict[str, Any]:
        """Detecta el estado actual del tiempo para las animaciones."""
        lluvia = sensores.get('lluvia', {}).get('valor', 0)
        nieve = sensores.get('nieve', {}).get('valor', 0)
        nubosidad = sensores.get('nubosidad', {}).get('valor', 0)
        viento = sensores.get('viento', {}).get('valor', 0)
        temp = sensores.get('temperatura', {}).get('valor', 15)
        rayos = sensores.get('rayos_detectados', {}).get('valor', False)
        
        estado = {
            'precipitacion': None,
            'nubosidad': nubosidad,
            'viento': viento,
            'tormenta': rayos
        }
        
        if nieve > 0:
            estado['precipitacion'] = {
                'tipo': 'nieve',
                'intensidad': 'alta' if nieve > 5 else 'media' if nieve > 2 else 'baja'
            }
        elif lluvia > 0:
            estado['precipitacion'] = {
                'tipo': 'lluvia',
                'intensidad': 'alta' if lluvia > 10 else 'media' if lluvia > 5 else 'baja'
            }
        
        return estado
    
    def obtener_cajones(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de cajones para la UI."""
        return self.cajones
    
    def obtener_submenu_valor(self, nombre_valor: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera el contenido del submenú explicativo para un valor."""
        # Buscar el valor en la jerarquía
        valor_encontrado = None
        for grupo in self.jerarquia.grupos if self.jerarquia else []:
            for valor in grupo.valores:
                if valor.nombre == nombre_valor:
                    valor_encontrado = valor
                    break
            if valor_encontrado:
                break
        
        if not valor_encontrado:
            return {'error': 'Valor no encontrado'}
        
        return {
            'nombre': valor_encontrado.nombre,
            'tipo': valor_encontrado.tipo,
            'valor': valor_encontrado.valor,
            'unidad': valor_encontrado.unidad,
            'fiabilidad': valor_encontrado.fiabilidad.value if hasattr(valor_encontrado.fiabilidad, 'value') else valor_encontrado.fiabilidad,
            'sensores_origen': valor_encontrado.sensores,
            'dependencias': valor_encontrado.dependencias,
            'formula': self._obtener_formula(nombre_valor),
            'estado': self._obtener_estado(nombre_valor),
            'alerta': valor_encontrado.alerta
        }
    
    def _extraer_valor(self, datos: Dict[str, Any], clave: str) -> Optional[Dict[str, Any]]:
        """Extrae un valor del contexto con fallback ISA si es None."""
        fallback = obtener_fallback_universal()
        for key, value in datos.items():
            if clave.lower() in key.lower():
                if isinstance(value, dict):
                    valor = value.get('valor', value.get('value'))
                    unidad = value.get('unidad', value.get('unit', ''))
                else:
                    valor = value
                    unidad = ''

                clave_basal = 'temperatura' if 'temp' in clave.lower() else 'humedad_relativa' if 'hum' in clave.lower() else 'presion'
                valor_final, estado = fallback.aplicar_fallback(valor, clave_basal, clave)
                fiabilidad = 'alta' if estado == EstadoFisico.REAL else 'media'

                return {
                    'valor': valor_final,
                    'unidad': unidad,
                    'fiabilidad': fiabilidad
                }
        return None
    
    def _obtener_formula(self, nombre_valor: str) -> str:
        """Obtiene la fórmula utilizada para calcular el valor."""
        # Implementar lógica para obtener fórmulas desde el sistema
        formulas_conocidas = {
            'utci': 'UTCI = f(T, RH, v, Tmrt)',
            'sensacion_termica': 'ST = 13.12 + 0.6215*T - 11.37*v^0.16 + 0.3965*T*v^0.16',
            'punto_rocio': 'Td = T - ((100 - RH)/5)',
        }
        return formulas_conocidas.get(nombre_valor.lower(), 'Fórmula no disponible')
    
    def _obtener_estado(self, nombre_valor: str) -> str:
        """Obtiene el estado descriptivo del valor."""
        # Implementar lógica para estados contextuales
        return 'Operativo'


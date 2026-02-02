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
        """Genera la estructura de cajones desde la jerarquía, garantizando exactamente 5 cajones principales."""
        if not self.jerarquia:
            return
        
        self.cajones = []
        # EXACTAMENTE 5 CAJONES PRINCIPALES (como especificado)
        for grupo in self.jerarquia.grupos[:5]:
            # Determinar cuántos valores mostrar en la portada (tapa del cajón)
            # Si hay espacio (grupo con <4 valores), mostrar todos; si no, solo los 2 más prioritarios
            num_valores_tapa = min(len(grupo.valores), 3) if len(grupo.valores) <= 4 else 2
            valores_tapa = grupo.valores[:num_valores_tapa]
            
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
        """Serializa un ValorSistema para la UI, aplicando Resolución de Diamante y Ley del Entero para UV, y redondeo a 2 decimales para todos los valores."""
        val = valor.valor
        
        # REGLA GLOBAL: Redondear a 2 decimales TODOS los valores numéricos (excepto coordenadas que se gestionan aparte)
        if val is not None and isinstance(val, (int, float)) and 'coordenada' not in valor.nombre.lower() and 'latitud' not in valor.nombre.lower() and 'longitud' not in valor.nombre.lower():
            try:
                val_float = float(val)
                # Resolución de Diamante para UV: 2 decimales si tiene decimales, INT si es 0 o redondo exacto
                if 'uv' in valor.nombre.lower() or 'ultravioleta' in valor.nombre.lower():
                    # Ley del Entero: solo INT si es 0 o un valor redondo exacto (7.00 -> 7)
                    if val_float == 0 or (val_float == int(val_float)):
                        val = int(val_float)
                    else:
                        # Resolución de Diamante: 2 decimales redondeados para ver la curva real
                        val = round(val_float, 2)
                else:
                    # Para todos los demás valores: 2 decimales
                        val = round(val_float, 2)
            except Exception:
                pass
        
        return {
            'nombre': valor.nombre,
            'tipo': valor.tipo,
            'valor': val,
            'unidad': valor.unidad,
            'fiabilidad': valor.fiabilidad.value if hasattr(valor.fiabilidad, 'value') else valor.fiabilidad,
            'icono': valor.icono,
            'prioridad': valor.prioridad,
            'alerta': valor.alerta,
            'tiene_alerta': valor.alerta is not None
        }
    
    def obtener_panel_superior(self, lat: float, lon: float, estacion: str) -> Dict[str, Any]:
        """Genera los datos para el panel superior fijo, mostrando coordenadas con máxima precisión (sin truncar ni redondear)."""
        fecha_actual = datetime.now()
        def format_coord(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        return {
            'nombre_sistema': 'MeteoSer',
            'ubicacion': {
                'latitud': format_coord(lat),
                'longitud': format_coord(lon),
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

        valores_principales = {
            'temperatura': temperatura.get('valor') if isinstance(temperatura, dict) else temperatura,
            'humedad': humedad.get('valor') if isinstance(humedad, dict) else humedad,
            'sensacion': sensacion.get('persona') if isinstance(sensacion, dict) else sensacion,
        }
        valores_secundarios = {
            'presion': presion.get('valor') if isinstance(presion, dict) else presion,
            'viento': viento.get('valor') if isinstance(viento, dict) else viento,
        }

        return {
            'recomendacion': recomendaciones.get('texto') if isinstance(recomendaciones, dict) else recomendaciones,
            'valores_principales': valores_principales,
            'valores_secundarios': valores_secundarios,
            'estado_tiempo': self._detectar_estado_tiempo(sensores, indices),
            # Compatibilidad
            'recomendaciones': recomendaciones,
            'temperatura': temperatura,
            'humedad': humedad,
            'presion': presion,
            'viento': viento,
            'sensacion': sensacion,
        }
    
    def _detectar_estado_tiempo(self, sensores: Dict, indices: Dict) -> Dict[str, Any]:
        """Detecta el estado actual del tiempo para las animaciones. Soporta: lluvia, nieve, granizo, niebla, viento, tormenta, ventisca, etc."""
        # Asegurar valores numéricos: algunos sensores pueden existir pero contener None
        lluvia = sensores.get('lluvia', {})
        lluvia = lluvia.get('valor') if isinstance(lluvia, dict) else lluvia
        if lluvia is None:
            lluvia = 0

        nieve = sensores.get('nieve', {})
        nieve = nieve.get('valor') if isinstance(nieve, dict) else nieve
        if nieve is None:
            nieve = 0
        
        granizo = sensores.get('granizo', {})
        granizo = granizo.get('valor') if isinstance(granizo, dict) else granizo
        if granizo is None:
            granizo = 0

        nubosidad = sensores.get('nubosidad', {})
        nubosidad = nubosidad.get('valor') if isinstance(nubosidad, dict) else nubosidad
        if nubosidad is None:
            nubosidad = 0
        
        visibilidad = sensores.get('visibilidad', {})
        visibilidad = visibilidad.get('valor') if isinstance(visibilidad, dict) else visibilidad
        if visibilidad is None:
            visibilidad = 10  # km (valor por defecto: buena visibilidad)

        viento = sensores.get('viento', {})
        viento = viento.get('valor') if isinstance(viento, dict) else viento
        if viento is None:
            viento = 0

        temp = sensores.get('temperatura', {})
        temp = temp.get('valor') if isinstance(temp, dict) else temp
        if temp is None:
            temp = 15

        rayos = sensores.get('rayos_detectados', {})
        rayos = rayos.get('valor') if isinstance(rayos, dict) else rayos
        if rayos is None:
            rayos = False
        
        estado = {
            'precipitacion': None,
            'nubosidad': nubosidad,
            'viento': viento,
            'tormenta': rayos,
            'visibilidad': visibilidad,
            'niebla': visibilidad < 1.0,  # Niebla si visibilidad < 1km
            'ventisca': False
        }
        
        # Detección de granizo (prioridad alta)
        if granizo > 0:
            estado['precipitacion'] = {
                'tipo': 'granizo',
                'intensidad': 'alta' if granizo > 20 else 'media' if granizo > 10 else 'baja'
            }
        # Detección de nieve
        elif nieve > 0:
            # Ventisca: nieve + viento fuerte
            if viento > 40:
                estado['ventisca'] = True
                estado['precipitacion'] = {
                    'tipo': 'ventisca',
                    'intensidad': 'alta'
                }
            else:
                estado['precipitacion'] = {
                    'tipo': 'nieve',
                    'intensidad': 'alta' if nieve > 5 else 'media' if nieve > 2 else 'baja'
                }
        # Detección de lluvia
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
                
                # Aplicar Resolución de Diamante y Ley del Entero para UV
                if 'uv' in clave.lower() and valor_final is not None:
                    try:
                        val_float = float(valor_final)
                        if val_float == 0 or (val_float == int(val_float)):
                            valor_final = int(val_float)
                        else:
                            valor_final = round(val_float, 2)
                    except Exception:
                        pass

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


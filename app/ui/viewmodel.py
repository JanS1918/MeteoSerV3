import logging
# viewmodel.py
# ViewModel para la nueva interfaz MeteoSer

from typing import Dict, List, Any, Optional
from core.data_model import ValorSistema, GrupoValores, JerarquiaUI
from core.context.fallback_universal import obtener_fallback_universal, EstadoFisico
from core.fiabilidad_manager import FiabilidadManager
from core.arcos_solares import (
    calcular_posicion_sol,
    calcular_fase_lunar,
    calcular_posicion_luna,
    radiacion_teorica,
    determinar_dia_hibrido,
    calcular_ventana_observacion_nocturna,
)
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
        """Genera la estructura de cajones desde la jerarquía, mostrando hasta 10 cajones principales."""
        if not self.jerarquia:
            return
        
        self.cajones = []
        # Mostrar hasta 10 cajones (el panel admite 10 en 2 columnas)
        for grupo in self.jerarquia.grupos[:10]:
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
                logging.exception("Silent except at 77 - revisar contexto")
        
        return {
            'nombre': valor.nombre,
            'tipo': valor.tipo,
            'valor': val,
            'unidad': valor.unidad,
            'fiabilidad': valor.fiabilidad.value if hasattr(valor.fiabilidad, 'value') else valor.fiabilidad,
            'icono': valor.icono,
            'prioridad': valor.prioridad,
            'alerta': valor.alerta,
            'tiene_alerta': valor.alerta is not None,
            'cambios': getattr(valor, 'cambios', 0),
            'estabilizado': getattr(valor, 'estabilizado', True),
            'loop_detectado': getattr(valor, 'loop_detectado', False)
        }
    
    def obtener_panel_superior(self, lat: float, lon: float, estacion: str) -> Dict[str, Any]:
        """Genera los datos para el panel superior fijo, mostrando coordenadas con 8 decimales (alta fidelidad científica)."""
        fecha_actual = datetime.now()
        def format_coord(val):
            try:
                # Forzar string con 8 decimales, sin round ni float puro
                return f"{float(val):.8f}"
            except Exception:
                return "0.00000000"
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
    
    def obtener_arcos_solares(
        self,
        lat: float,
        lon: float,
        nubosidad: Optional[float] = None,
        sensores: Optional[Dict[str, Any]] = None,
        altitud_m: Optional[float] = None,
        perfil_horizonte: Optional[List[Dict[str, float]]] = None,
        zona_horaria: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Genera los datos para los arcos solar y lunar."""
        fecha_actual = datetime.now()

        if zona_horaria is None:
            try:
                offset = datetime.now().astimezone().utcoffset()
                if offset is not None:
                    zona_horaria = int(round(offset.total_seconds() / 3600))
            except Exception:
                zona_horaria = None
        if zona_horaria is None:
            try:
                zona_horaria = int(round(lon / 15.0))
            except Exception:
                zona_horaria = None

        sensores = sensores or {}

        def _v(x):
            return x.get('valor') if isinstance(x, dict) and 'valor' in x else x

        temp_c = _v(sensores.get('temperatura'))
        humedad = _v(sensores.get('humedad'))
        presion = _v(sensores.get('presion')) or _v(sensores.get('presion_barometrica')) or _v(sensores.get('presion_hpa'))
        if presion is not None:
            try:
                presion = float(presion)
                if presion > 2000:
                    presion = presion / 100.0
            except Exception:
                presion = None
        radiacion = _v(sensores.get('radiacion')) or _v(sensores.get('radiacion_global')) or _v(sensores.get('radiacion_solar'))
        uv = _v(sensores.get('uv_index')) or _v(sensores.get('indice_uv'))
        
        # Calcular posición del sol
        datos_sol = calcular_posicion_sol(
            lat,
            lon,
            fecha_actual,
            presion_hpa=presion,
            temperatura_c=temp_c,
            humedad_rel=humedad,
            altitud_m=altitud_m,
            zona_horaria=zona_horaria,
            perfil_horizonte=perfil_horizonte,
        )
        
        # Calcular fase lunar
        datos_luna = calcular_fase_lunar(
            fecha_actual,
            lat=lat,
            lon=lon,
            altitud_m=altitud_m,
            presion_hpa=presion,
            temperatura_c=temp_c,
            humedad_rel=humedad,
        )
        
        # Calcular posición de la luna
        posicion_luna = calcular_posicion_luna(
            fecha_actual,
            datos_sol['amanecer'],
            datos_sol['anochecer'],
            datos_sol['es_de_dia'],
            lat=lat,
            lon=lon,
            altitud_m=altitud_m,
            presion_hpa=presion,
            temperatura_c=temp_c,
            humedad_rel=humedad,
        )

        hora_decimal = fecha_actual.hour + fecha_actual.minute / 60.0 + fecha_actual.second / 3600.0
        elevacion_solar = datos_sol.get('elevacion_solar_deg')
        rad_teorica = radiacion_teorica(
            lat_deg=lat,
            dia_del_ano=fecha_actual.timetuple().tm_yday,
            hora_decimal=hora_decimal,
            elevacion_solar_deg=elevacion_solar,
        )

        hibrido = determinar_dia_hibrido(
            elevacion_solar_deg=elevacion_solar if elevacion_solar is not None else -90.0,
            radiacion_sensor_wm2=float(radiacion) if radiacion is not None else None,
            uv_index=float(uv) if uv is not None else None,
            radiacion_teorica_wm2=rad_teorica,
        )

        ventana_obs = calcular_ventana_observacion_nocturna(lat, lon, fecha_actual, zona_horaria=zona_horaria)
        indice_cielo = 0
        if elevacion_solar is not None:
            if elevacion_solar <= -18:
                indice_cielo = 100
            elif elevacion_solar <= -12:
                indice_cielo = 70
            elif elevacion_solar <= -6:
                indice_cielo = 40

        nivel_cielo = "diurno"
        if indice_cielo >= 80:
            nivel_cielo = "excelente"
        elif indice_cielo >= 60:
            nivel_cielo = "bueno"
        elif indice_cielo >= 30:
            nivel_cielo = "regular"
        
        return {
            'sol': {
                'posicion': datos_sol['posicion_sol'],
                'amanecer': datos_sol['amanecer'],
                'anochecer': datos_sol['anochecer'],
                'duracion_dia': datos_sol['duracion_dia'],
                'es_de_dia': datos_sol['es_de_dia'],
                'elevacion_solar_deg': elevacion_solar,
                'azimut_solar_deg': datos_sol.get('azimut_solar_deg'),
                'radiacion_teorica_wm2': rad_teorica,
                'dia_hibrido': hibrido,
                'nublado': nubosidad is not None and nubosidad > 50
            },
            'luna': {
                'posicion': posicion_luna,
                'fase': datos_luna['fase'],
                'nombre_fase': datos_luna['nombre'],
                'icono': datos_luna['icono'],
                'duracion_noche': datos_sol['duracion_noche'],
                'ventana_observacion_nocturna': ventana_obs,
                'indice_cielo_astronomico': indice_cielo,
                'indice_cielo_astronomico_nivel': nivel_cielo,
            }
        }
    
    def obtener_panel_central(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Genera los datos para el panel central (recomendaciones y sensación)."""
        sensores = contexto.get('sensores', {})
        indices = contexto.get('indices', {})
        ubicacion = contexto.get('ubicacion', {})
        cambios_formulas = contexto.get('cambios_formulas', {})
        
        # Generar recomendaciones
        recomendaciones = self.recomendaciones_motor.generar_recomendaciones(contexto)
        
        # Obtener valores clave
        temperatura = self._extraer_valor(sensores, 'temperatura')
        humedad = self._extraer_valor(sensores, 'humedad')
        presion = self._extraer_valor(sensores, 'presion')
        viento = self._extraer_valor(sensores, 'viento')
        
        # [FAST] LEY DEL ENTERO: Forzar INT si el valor es redondo (sin decimales)
        def _forzar_int_si_redondo(dict_valor):
            if dict_valor and isinstance(dict_valor, dict) and 'valor' in dict_valor:
                val = dict_valor['valor']
                try:
                    if isinstance(val, float) and val == int(val):
                        dict_valor['valor'] = int(val)
                except Exception:
                    logging.exception("Silent except at 171 - revisar contexto")
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

        def _cambio_para(nombre: str) -> Dict[str, Any]:
            if not cambios_formulas:
                return {"cambios": 0, "estabilizado": True, "loop_detectado": False}
            key = str(nombre).strip().lower().replace(" ", "_")
            info = cambios_formulas.get(nombre) or cambios_formulas.get(key) or {}
            return {
                "cambios": int(info.get("cambios", 0) or 0),
                "estabilizado": bool(info.get("estabilizado", True)),
                "loop_detectado": bool(info.get("loop_detectado", False)),
            }

        valores_principales = {
            'temperatura': temperatura.get('valor') if isinstance(temperatura, dict) else temperatura,
            'humedad': humedad.get('valor') if isinstance(humedad, dict) else humedad,
            'sensacion': sensacion.get('persona') if isinstance(sensacion, dict) else sensacion,
        }

        # Determinar si es de día o de noche
        es_de_dia = False
        elevacion_solar = contexto.get('elevacion_solar', {}).get('sol', {}).get('elevacion_solar_deg')
        if elevacion_solar is not None and elevacion_solar > -0.833:
            es_de_dia = True

        # Obtener elevación lunar si es de noche
        elevacion_lunar = None
        if not es_de_dia:
            # Buscar elevación lunar en contexto si está disponible
            elevacion_lunar = contexto.get('elevacion_solar', {}).get('luna', {}).get('elevacion_lunar_deg')
            # Si no está, intentar obtenerla de los arcos
            if elevacion_lunar is None:
                try:
                    from core.arcos_solares import calcular_fase_lunar
                    datos_luna = calcular_fase_lunar(datetime.now(), lat=ubicacion.get('latitud'), lon=ubicacion.get('longitud'))
                    elevacion_lunar = datos_luna.get('elevacion_lunar_deg')
                except Exception:
                    elevacion_lunar = None

        uv_val = contexto.get('uv')
        uv_motor = contexto.get('uv_motor')
        if uv_val is None:
            uv_idx = self._extraer_valor(indices, 'uv')
            uv_val = uv_idx.get('valor') if isinstance(uv_idx, dict) else uv_idx

        direccion_viento = self._extraer_valor(sensores, 'direccion_viento')
        direccion_viento = direccion_viento.get('valor') if isinstance(direccion_viento, dict) else direccion_viento
        direccion_viento_cardinal = self._extraer_valor(sensores, 'direccion_viento_cardinal')
        direccion_viento_cardinal = direccion_viento_cardinal.get('valor') if isinstance(direccion_viento_cardinal, dict) else direccion_viento_cardinal

        valores_secundarios = {
            'presion': presion.get('valor') if isinstance(presion, dict) else presion,
            'viento': viento.get('valor') if isinstance(viento, dict) else viento,
            'direccion_viento': direccion_viento,
            'direccion_viento_cardinal': direccion_viento_cardinal,
            'elevacion_solar': elevacion_solar if es_de_dia else None,
            'elevacion_lunar': elevacion_lunar if not es_de_dia else None,
            'uv': uv_val,
            'uv_motor': uv_motor,
            'es_de_dia': es_de_dia,
        }

        cambios_valores = {
            'temperatura': _cambio_para('Temperatura'),
            'humedad': _cambio_para('Humedad'),
            'sensacion': _cambio_para('Sensación'),
            'presion': _cambio_para('Presión'),
            'viento': _cambio_para('Viento'),
            'elevacion_solar': _cambio_para('Elevación solar'),
            'uv': _cambio_para('Índice UV'),
        }

        return {
            'recomendacion': recomendaciones.get('texto') if isinstance(recomendaciones, dict) else recomendaciones,
            'valores_principales': valores_principales,
            'valores_secundarios': valores_secundarios,
            'cambios_valores': cambios_valores,
            'estado_tiempo': self._detectar_estado_tiempo(sensores, indices),
            'ubicacion': ubicacion,
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
        
        traza = getattr(valor_encontrado, 'traza', None)
        medido_virtual = self._clasificar_medido_virtual(valor_encontrado, traza)
        tipo_estimacion = self._clasificar_estimacion(valor_encontrado, traza)
        mapa_dependencias = self._mapa_dependencias_minimo(valor_encontrado, traza)
        regla_fiabilidad = self._regla_fiabilidad(valor_encontrado, medido_virtual, traza)

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
            'alerta': valor_encontrado.alerta,
            'cambios': getattr(valor_encontrado, 'cambios', 0),
            'estabilizado': getattr(valor_encontrado, 'estabilizado', True),
            'loop_detectado': getattr(valor_encontrado, 'loop_detectado', False),
            'medido_virtual': medido_virtual,
            'tipo_estimacion': tipo_estimacion,
            'regla_fiabilidad': regla_fiabilidad,
            'mapa_dependencias': mapa_dependencias,
            'traza': traza,
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
                        logging.exception("Silent except at 352 - revisar contexto")

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
                'horizonte_orografico_deg': datos_sol.get('horizonte_orografico_deg'),
                'sombra_orografica': datos_sol.get('sombra_orografica'),
        }
        return formulas_conocidas.get(nombre_valor.lower(), 'Fórmula no disponible')
    
    def _obtener_estado(self, nombre_valor: str) -> str:
        """Obtiene el estado descriptivo del valor."""
        # Implementar lógica para estados contextuales
        return 'Operativo'

    def _clasificar_medido_virtual(self, valor: ValorSistema, traza: Optional[Dict[str, Any]]) -> str:
        if valor.tipo == 'sensor':
            return 'medido'
        if isinstance(traza, dict):
            origen = str(traza.get('origen', '')).lower()
            if origen in {'virtual', 'estimado', 'modelo', 'modelado'}:
                return 'virtual'
            virtual_pct = traza.get('virtual_pct')
            try:
                if virtual_pct is not None and float(virtual_pct) > 0:
                    return 'virtual'
            except Exception:
                pass
        return 'virtual'

    def _clasificar_estimacion(self, valor: ValorSistema, traza: Optional[Dict[str, Any]]) -> str:
        if valor.tipo == 'sensor':
            return 'medicion_directa'
        metodo = ''
        if isinstance(traza, dict):
            metodo = str(traza.get('metodo', '')).lower()
        if any(token in metodo for token in ['residual', 'balance', 'qnet - h - g', 'Δs', 'delta s']):
            return 'derivacion_balance'
        return 'estimacion_fisica'

    def _mapa_dependencias_minimo(self, valor: ValorSistema, traza: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        sensores = list(valor.sensores or [])
        dependencias = list(valor.dependencias or [])
        entradas = []
        if isinstance(traza, dict):
            entradas_dict = traza.get('entradas') if isinstance(traza.get('entradas'), dict) else None
            if entradas_dict:
                entradas = list(entradas_dict.keys())
        return {
            'sensores': sensores,
            'indices': dependencias,
            'entradas': entradas,
        }

    def _regla_fiabilidad(
        self,
        valor: ValorSistema,
        medido_virtual: str,
        traza: Optional[Dict[str, Any]],
    ) -> str:
        if medido_virtual == 'medido':
            return 'ALTA (medición directa)'
        if isinstance(traza, dict):
            metodo = traza.get('metodo')
            if metodo:
                return 'MEDIA (modelo físico con trazabilidad)'
        return 'BAJA (virtual sin trazabilidad completa)'


"""
GENERADOR ALERTAS IMPACTO PREDICTIVO v1.0
═════════════════════════════════════════════════════════════════════════════

Monitorea eventos meteorológicos y genera alertas predictivas basadas
en matriz de impacto cruzado. Publicable al bus para reacciones en cascada.

Uso: python core/indices/predictive_alerts_impact.py [--monitor] [--test]

Fecha: 11 de febrero de 2026
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Configurar UTF-8 para salida en Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio padre al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class NivelSeveridad(Enum):
    """Niveles de alerta de severidad."""
    CRÍTICO = 4
    SEVERO = 3
    MODERADO = 2
    LEVE = 1
    NORMAL = 0


@dataclass
class Evento:
    """Evento meteorológico que genera impacto."""
    tipo: str  # lluvia, amplitud_termica, humedad_baja, etc.
    valor: float
    timestamp: str
    descripcion: str = ""


@dataclass
class Alerta:
    """Alerta generada por análisis de impacto."""
    nivel: str  # CRÍTICO, SEVERO, MODERADO, LEVE
    dominio: str
    evento_causa: str
    impacto_magnitud: float
    recomendacion: str
    timestamp: str
    afectacion_secundaria: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        d = asdict(self)
        d['nivel_numerico'] = NivelSeveridad[self.nivel].value
        return d


class GeneradorAlertasImpacto:
    """Genera alertas basadas en matriz de impacto cruzado."""
    
    def __init__(self):
        """Inicializa generador de alertas."""
        try:
            from core.indices.matriz_impacto_cruzado import (
                calcular_impacto_evento,
                calcular_impacto_multiples_eventos,
                MATRIZ_IMPACTO_LLUVIA,
                MATRIZ_IMPACTO_AMPLITUD,
                MATRIZ_IMPACTO_HUMEDAD_BAJA,
            )
            self.calcular_impacto_evento = calcular_impacto_evento
            self.calcular_impacto_multiples_eventos = calcular_impacto_multiples_eventos
            self.matrices_disponibles = True
        except ImportError as e:
            logger.warning(f"No se pudo importar matriz_impacto: {e}")
            self.matrices_disponibles = False
        
        self.alertas_activas = []
        self.historico_alertas = []
        self.umbral_alerta_por_nivel = {
            'CRÍTICO': 80,
            'SEVERO': 60,
            'MODERADO': 40,
            'LEVE': 20,
        }
    
    def obtener_eventos_actuales_simulados(self) -> List[Evento]:
        """
        Obtiene eventos actuales. En producción, se consultaría el bus.
        Simula casos para demostración.
        """
        ahora = datetime.now().isoformat()
        
        eventos = [
            Evento(
                tipo='lluvia',
                valor=15.0,  # mm
                timestamp=ahora,
                descripcion='Lluvia actual: 15mm en 1h'
            ),
            Evento(
                tipo='amplitud_termica',
                valor=12.0,  # °C
                timestamp=ahora,
                descripcion='Amplitud térmica diaria: 12°C'
            ),
            Evento(
                tipo='humedad_baja',
                valor=25.0,  # %
                timestamp=ahora,
                descripcion='Humedad relativa: 25%'
            ),
        ]
        
        return eventos
    
    def calcular_impactos(self, eventos: List[Evento]) -> Dict:
        """
        Calcula impactos de eventos en todos los dominios.
        """
        
        if not self.matrices_disponibles:
            logger.warning("Matrices de impacto no disponibles, usando simulacion")
            return self._simular_impactos(eventos)
        
        # Construir dict de eventos para calcular_impacto_multiples_eventos
        eventos_dict = {e.tipo: e.valor for e in eventos}
        
        try:
            impactos = self.calcular_impacto_multiples_eventos(eventos_dict)
            return impactos
        except Exception as e:
            logger.error(f"Error calculando impactos: {e}")
            return self._simular_impactos(eventos)
    
    def _simular_impactos(self, eventos: List[Evento]) -> Dict:
        """Simula impactos cuando función real no está disponible."""
        
        dominios = [
            'cetreria', 'lluvia', 'confort', 'deporte',
            'riego', 'astronomia', 'salud', 'hidrologia'
        ]
        
        impactos = {}
        
        for evento in eventos:
            # Asignar impactos simulados según tipo de evento
            if evento.tipo == 'lluvia':
                impactos_evento = {
                    'cetreria': -80,
                    'lluvia': 90,
                    'riego': 50,
                    'deporte': -40,
                    'hidrologia': 85,
                }
            elif evento.tipo == 'amplitud_termica':
                impactos_evento = {
                    'salud': 40,
                    'confort': -30,
                    'deporte': -20,
                    'astronomia': 25,
                }
            elif evento.tipo == 'humedad_baja':
                impactos_evento = {
                    'riego': -70,
                    'salud': 30,
                    'hidrologia': -50,
                    'confort': -40,
                }
            else:
                impactos_evento = {d: 0 for d in dominios}
            
            # Acumular
            for dominio in dominios:
                valor = impactos_evento.get(dominio, 0)
                if valor != 0:
                    if dominio not in impactos:
                        impactos[dominio] = []
                    impactos[dominio].append(valor)
        
        # Promediar por dominio
        impactos_promediados = {}
        for dominio, valores in impactos.items():
            impactos_promediados[dominio] = sum(valores) / len(valores)
        
        return impactos_promediados
    
    def clasificar_impacto(self, magnitud: float) -> str:
        """Clasifica magnitud de impacto a nivel de alerta."""
        
        magnitud_abs = abs(magnitud)
        
        if magnitud_abs >= 80:
            return 'CRÍTICO'
        elif magnitud_abs >= 60:
            return 'SEVERO'
        elif magnitud_abs >= 40:
            return 'MODERADO'
        elif magnitud_abs >= 20:
            return 'LEVE'
        else:
            return 'NORMAL'
    
    def generar_alertas(self, eventos: List[Evento], impactos: Dict) -> List[Alerta]:
        """
        Genera alertas basadas en impactos calculados.
        """
        
        alertas = []
        evento_causa_str = ', '.join([f"{e.tipo}({e.valor})" for e in eventos])
        ahora = datetime.now().isoformat()
        
        for dominio, magnitud in impactos.items():
            
            # Clasificar severidad
            nivel = self.clasificar_impacto(magnitud)
            
            if nivel == 'NORMAL':
                continue  # No generar alerta
            
            # Generar recomendación según dominio y evento
            recomendacion = self._generar_recomendacion(dominio, eventos, magnitud)
            
            # Detectar afectaciones secundarias
            afectaciones_secundarias = self._detectar_afectaciones_secundarias(
                dominio, eventos, impactos
            )
            
            alerta = Alerta(
                nivel=nivel,
                dominio=dominio,
                evento_causa=evento_causa_str,
                impacto_magnitud=round(magnitud, 1),
                recomendacion=recomendacion,
                timestamp=ahora,
                afectacion_secundaria=afectaciones_secundarias
            )
            
            alertas.append(alerta)
        
        return alertas
    
    def _generar_recomendacion(self, 
                              dominio: str, 
                              eventos: List[Evento],
                              magnitud: float) -> str:
        """Genera recomendación específica según contexto."""
        
        recomendaciones = {
            'lluvia': {
                'positivo': 'Aprovechar para riego: probabilidad de lluvia alta',
                'negativo': 'Suspender actividades al aire libre'
            },
            'cetreria': {
                'positivo': 'Condiciones mejorando para vuelo',
                'negativo': 'Cancelar entrenamientos: condiciones adversas'
            },
            'riego': {
                'positivo': 'Reducir riego: precipitación esperada',
                'negativo': 'Aumentar riego: estrés hídrico crítico'
            },
            'deporte': {
                'positivo': 'Condiciones aceptables para competencia',
                'negativo': 'Riesgos de seguridad: suspender actividades'
            },
            'salud': {
                'positivo': 'Condiciones favorables para ejercicio',
                'negativo': 'Riesgos de estrés térmico: tomar precauciones'
            },
            'confort': {
                'positivo': 'Condiciones confortables',
                'negativo': 'Malestar esperado: activar sistemas de control'
            },
            'astronomia': {
                'positivo': 'Observabilidad excelente',
                'negativo': 'Observabilidad comprometida'
            },
            'hidrologia': {
                'positivo': 'Recarga de acuíferos esperada',
                'negativo': 'Riesgo de inundación: preparar drenaje'
            }
        }
        
        tipo_recomendacion = 'positivo' if magnitud > 0 else 'negativo'
        
        return recomendaciones.get(dominio, {}).get(tipo_recomendacion, 
                                                    f"Monitorear {dominio}")
    
    def _detectar_afectaciones_secundarias(self,
                                          dominio_primario: str,
                                          eventos: List[Evento],
                                          impactos: Dict) -> Optional[List[str]]:
        """Detecta dominios secundarios afectados."""
        
        afectaciones = []
        
        # Reglas de propagación de impacto
        propagacion = {
            'lluvia': ['hidrologia', 'riego', 'cetreria'],
            'salud': ['confort', 'deporte'],
            'riego': ['hidrologia', 'confort'],
            'astronomia': ['cetreria', 'deporte'],
            'deporte': ['salud', 'confort'],
        }
        
        dominios_secundarios = propagacion.get(dominio_primario, [])
        
        for dominio_sec in dominios_secundarios:
            if dominio_sec in impactos:
                if abs(impactos[dominio_sec]) > 0:
                    afectaciones.append(dominio_sec)
        
        return afectaciones if afectaciones else None
    
    def consolidar_alertas(self, alertas: List[Alerta]) -> Dict:
        """Consolida alertas para evitar duplicados y ordenar por severidad."""
        
        # Agrupar por dominio y tomar la más severa
        alertas_consolidadas = {}
        
        for alerta in alertas:
            if alerta.dominio not in alertas_consolidadas:
                alertas_consolidadas[alerta.dominio] = alerta
            else:
                # Mantener la más severa
                if (NivelSeveridad[alerta.nivel].value > 
                    NivelSeveridad[alertas_consolidadas[alerta.dominio].nivel].value):
                    alertas_consolidadas[alerta.dominio] = alerta
        
        # Ordenar por severidad
        alertas_ordenadas = sorted(
            alertas_consolidadas.values(),
            key=lambda a: NivelSeveridad[a.nivel].value,
            reverse=True
        )
        
        return {
            'total_alertas': len(alertas_ordenadas),
            'criticas': sum(1 for a in alertas_ordenadas if a.nivel == 'CRÍTICO'),
            'severas': sum(1 for a in alertas_ordenadas if a.nivel == 'SEVERO'),
            'alertas': [a.to_dict() for a in alertas_ordenadas]
        }
    
    def generar_reporte_alertas(self, consolidado: Dict) -> str:
        """Genera reporte formateado de alertas."""
        
        lines = [
            "═" * 80,
            "REPORTE ALERTAS PREDICTIVAS - MATRIZ IMPACTO CRUZADO",
            "═" * 80,
            "",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Total de alertas: {consolidado['total_alertas']}",
            f"  ├─ Críticas: {consolidado['criticas']}",
            f"  └─ Severas: {consolidado['severas']}",
            "",
        ]
        
        if consolidado['total_alertas'] == 0:
            lines.append("✓ SIN ALERTAS - Sistema operando normalmente")
        else:
            lines.append("ALERTAS ACTIVAS")
            lines.append("─" * 80)
            
            for alerta_dict in consolidado['alertas']:
                nivel = alerta_dict['nivel']
                emoji = {'CRÍTICO': '🔴', 'SEVERO': '🟠', 'MODERADO': '🟡', 'LEVE': '🔵'}
                
                lines.extend([
                    f"{emoji.get(nivel, '⚪')} [{nivel}] {alerta_dict['dominio'].upper()}",
                    f"    Causa: {alerta_dict['evento_causa']}",
                    f"    Magnitud: {alerta_dict['impacto_magnitud']}",
                    f"    Acción: {alerta_dict['recomendacion']}",
                ])
                
                if alerta_dict.get('afectacion_secundaria'):
                    lines.append(f"    Afecta también: {', '.join(alerta_dict['afectacion_secundaria'])}")
                
                lines.append("")
        
        lines.extend([
            "═" * 80,
        ])
        
        return "\n".join(lines)


def main(modo_test: bool = True, modo_monitor: bool = False):
    """Función principal."""
    
    logger.info("═" * 80)
    logger.info("INICIANDO GENERADOR ALERTAS IMPACTO PREDICTIVO")
    logger.info("═" * 80)
    
    generador = GeneradorAlertasImpacto()
    
    # Obtener eventos actuales
    logger.info("[1/4] Obteniendo eventos meteorológicos...")
    eventos = generador.obtener_eventos_actuales_simulados()
    logger.info(f"  ✓ {len(eventos)} eventos detectados")
    
    for evento in eventos:
        logger.debug(f"    - {evento.tipo}: {evento.valor} ({evento.descripcion})")
    
    # Calcular impactos
    logger.info("[2/4] Calculando impactos cruzados...")
    impactos = generador.calcular_impactos(eventos)
    logger.info(f"  ✓ {len(impactos)} dominios evaluados")
    
    # Generar alertas
    logger.info("[3/4] Generando alertas...")
    alertas = generador.generar_alertas(eventos, impactos)
    logger.info(f"  ✓ {len(alertas)} alertas generadas")
    
    # Consolidar
    logger.info("[4/4] Consolidando alertas...")
    consolidado = generador.consolidar_alertas(alertas)
    
    # Reporte
    reporte = generador.generar_reporte_alertas(consolidado)
    print("\n" + reporte)
    
    # Guardar JSON
    try:
        with open('alertas_impacto_actual.json', 'w', encoding='utf-8') as f:
            json.dump(consolidado, f, indent=2, ensure_ascii=False)
        logger.info("✓ Alertas guardadas: alertas_impacto_actual.json")
    except Exception as e:
        logger.error(f"Error guardando JSON: {e}")
    
    logger.info("═" * 80)
    logger.info("ANÁLISIS COMPLETADO")
    logger.info("═" * 80)
    
    if consolidado['criticas'] > 0:
        logger.warning(f"⚠️  {consolidado['criticas']} ALERTAS CRÍTICAS ACTIVAS")
    
    return consolidado


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generador de alertas predictivas basado en matriz impacto'
    )
    parser.add_argument('--monitor', action='store_true', 
                       help='Modo monitor continuo (cada 30s)')
    parser.add_argument('--test', action='store_true', default=True,
                       help='Modo test con datos simulados')
    
    args = parser.parse_args()
    
    resultado = main(modo_test=args.test, modo_monitor=args.monitor)

"""
═══════════════════════════════════════════════════════════════════════════════
STEP 8: ANÁLISIS HISTÓRICO Y TENDENCIAS
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Análisis temporal de alertas (semana, mes, año)
  - Detección de patrones y anomalías progresivas
  - Generación de reportes automáticos
  - Predicción de próximas anomalías

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional
from statistics import mean, stdev, median

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/analytics")
DATA_PATH.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: ANALIZADOR HISTÓRICO
# ═══════════════════════════════════════════════════════════════════════════

class AnalizadorHistorico:
    """Análisis temporal de alertas, tendencias y predicciones."""
    
    def __init__(self):
        self.ruta_alertas = Path("data/alertas")
        self.ruta_validaciones = Path("data/wh31_validations")
        self.ruta_reportes = DATA_PATH / "reportes"
        self.ruta_tendencias = DATA_PATH / "tendencias"
        
        self.ruta_reportes.mkdir(parents=True, exist_ok=True)
        self.ruta_tendencias.mkdir(parents=True, exist_ok=True)
    
    # ─────────────────────────────────────────────────────────────────────
    # ANÁLISIS DE ALERTAS HISTÓRICAS
    # ─────────────────────────────────────────────────────────────────────
    
    def cargar_alertas_historicas(self, dias: int = 30) -> List[Dict]:
        """Carga todas las alertas históricas del último período."""
        alertas = []
        fecha_limite = datetime.now() - timedelta(days=dias)
        
        if not self.ruta_alertas.exists():
            logger.warning("Directorio de alertas no existe")
            return alertas
        
        for archivo in sorted(self.ruta_alertas.glob("alertas_*.json")):
            try:
                with open(archivo, 'r') as f:
                    contenido = json.load(f)
                    
                    # Cargar alertas individuales
                    if isinstance(contenido, list):
                        alertas.extend(contenido)
                    elif isinstance(contenido, dict) and 'alertas' in contenido:
                        alertas.extend(contenido['alertas'])
                        
            except Exception as e:
                logger.warning(f"Error leyendo {archivo}: {e}")
        
        # Filtrar por fecha
        alertas_filtradas = []
        for alerta in alertas:
            try:
                timestamp = datetime.fromisoformat(
                    alerta.get('timestamp', '').replace('Z', '+00:00')
                )
                if timestamp >= fecha_limite:
                    alertas_filtradas.append(alerta)
            except:
                pass
        
        return alertas_filtradas
    
    def analizar_tendencia_alertas(self, dias: int = 30) -> Dict[str, Any]:
        """Analiza tendencias de alertas por nivel, dominio y hora."""
        alertas = self.cargar_alertas_historicas(dias)
        
        tendencia = {
            'periodo_dias': dias,
            'fecha_analisis': datetime.now().isoformat(),
            'total_alertas': len(alertas),
            'por_nivel': defaultdict(int),
            'por_dominio': defaultdict(int),
            'por_hora': defaultdict(int),
            'alertas_por_dia': defaultdict(int),
            'dominios_criticos': [],
            'patrones_detectados': []
        }
        
        # Análisis por nivel
        for alerta in alertas:
            nivel = alerta.get('nivel', 'DESCONOCIDO')
            tendencia['por_nivel'][nivel] += 1
            
            dominio = alerta.get('dominio', 'GENERAL')
            tendencia['por_dominio'][dominio] += 1
            
            # Análisis por hora
            try:
                timestamp = datetime.fromisoformat(
                    alerta.get('timestamp', '').replace('Z', '+00:00')
                )
                hora = timestamp.hour
                tendencia['por_hora'][hora] += 1
                
                fecha = timestamp.date()
                tendencia['alertas_por_dia'][str(fecha)] += 1
            except:
                pass
        
        # Convertir defaultdicits a dicts
        tendencia['por_nivel'] = dict(tendencia['por_nivel'])
        tendencia['por_dominio'] = dict(tendencia['por_dominio'])
        tendencia['por_hora'] = dict(tendencia['por_hora'])
        tendencia['alertas_por_dia'] = dict(tendencia['alertas_por_dia'])
        
        # Detectar dominios críticos (top 3 con más alertas críticas)
        dominios_criticos = defaultdict(int)
        for alerta in alertas:
            if alerta.get('nivel') == 'CRÍTICO':
                dominio = alerta.get('dominio', 'GENERAL')
                dominios_criticos[dominio] += 1
        
        tendencia['dominios_criticos'] = sorted(
            dominios_criticos.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Detectar patrones
        tendencia['patrones_detectados'] = self._detectar_patrones(
            alertas, tendencia
        )
        
        return tendencia
    
    def _detectar_patrones(self, alertas: List[Dict], 
                          tendencia: Dict) -> List[str]:
        """Detecta patrones en datos históricos."""
        patrones = []
        
        if not alertas:
            return patrones
        
        # Patrón 1: Mayor actividad en horario específico
        por_hora = tendencia['por_hora']
        if por_hora:
            hora_pico = max(por_hora, key=por_hora.get)
            total = sum(por_hora.values())
            pct_pico = (por_hora[hora_pico] / total * 100)
            
            if pct_pico > 20:
                patrones.append(
                    f"Alto volumen {hora_pico}:00-{hora_pico}:59 "
                    f"({pct_pico:.1f}% del total)"
                )
        
        # Patrón 2: Aumento progresivo
        alertas_por_dia = tendencia['alertas_por_dia']
        if len(alertas_por_dia) >= 7:
            dias_sorted = sorted(alertas_por_dia.items())
            primeros_7 = [v for k, v in dias_sorted[:7]]
            ultimos_7 = [v for k, v in dias_sorted[-7:]]
            
            if len(primeros_7) > 0 and len(ultimos_7) > 0:
                promedio_antiguo = mean(primeros_7)
                promedio_reciente = mean(ultimos_7)
                
                if promedio_reciente > promedio_antiguo * 1.5:
                    incremento = (
                        (promedio_reciente - promedio_antiguo) / 
                        promedio_antiguo * 100
                    )
                    patrones.append(
                        f"Tendencia ALCISTA: +{incremento:.1f}% "
                        f"vs últimos 7 días"
                    )
                elif promedio_reciente < promedio_antiguo * 0.5:
                    decremento = (
                        (promedio_antiguo - promedio_reciente) / 
                        promedio_antiguo * 100
                    )
                    patrones.append(
                        f"Tendencia BAJISTA: -{decremento:.1f}% "
                        f"vs últimos 7 días"
                    )
        
        # Patrón 3: Concentración en dominios
        por_dominio = tendencia['por_dominio']
        if por_dominio and len(por_dominio) > 0:
            top_dominio = max(por_dominio.items(), key=lambda x: x[1])
            concentracion = (top_dominio[1] / sum(por_dominio.values()) * 100)
            
            if concentracion > 40:
                patrones.append(
                    f"Concentración en dominio '{top_dominio[0]}': "
                    f"{concentracion:.1f}% del volumen"
                )
        
        return patrones
    
    # ─────────────────────────────────────────────────────────────────────
    # ANÁLISIS DE WH31
    # ─────────────────────────────────────────────────────────────────────
    
    def cargar_validaciones_wh31(self, limites: int = 50) -> List[Dict]:
        """Carga validaciones históricas de WH31."""
        validaciones = []
        
        if not self.ruta_validaciones.exists():
            return validaciones
        
        for archivo in sorted(
            self.ruta_validaciones.glob("validacion_*.json"),
            reverse=True
        )[:limites]:
            try:
                with open(archivo, 'r') as f:
                    validaciones.append(json.load(f))
            except Exception as e:
                logger.warning(f"Error leyendo {archivo}: {e}")
        
        return sorted(validaciones, key=lambda x: x.get('timestamp_ejecucion', ''))
    
    def analizar_tendencia_wh31(self) -> Dict[str, Any]:
        """Analiza tendencias en el sensor WH31 (drifts progresivos)."""
        validaciones = self.cargar_validaciones_wh31(limites=50)
        
        tendencia = {
            'fecha_analisis': datetime.now().isoformat(),
            'total_validaciones': len(validaciones),
            'errores_sistematicos': [],
            'diferenciales': [],
            'recomendaciones': [],
            'alerta_drift_detectado': False
        }
        
        if not validaciones:
            return tendencia
        
        # Extraer errores sistemáticos
        for validacion in validaciones:
            stats = validacion.get('estadisticas', {})
            error_info = stats.get('error_sistematico_wh31', {})
            
            if error_info:
                tendencia['errores_sistematicos'].append({
                    'timestamp': validacion.get('timestamp_ejecucion'),
                    'promedio': error_info.get('promedio', 0),
                    'rms': error_info.get('rms', 0),
                    'maximo': error_info.get('maximo_absoluto', 0)
                })
            
            # Extraer diferenciales
            diferencial = validacion.get('diferencial_promedio_wh31_wh65', 0)
            tendencia['diferenciales'].append({
                'timestamp': validacion.get('timestamp_ejecucion'),
                'valor': diferencial
            })
        
        # Analizar progresión de errores
        if len(tendencia['errores_sistematicos']) >= 5:
            errores = [e['promedio'] for e in tendencia['errores_sistematicos']]
            
            # Detectar incremento progresivo
            primeros = errores[:5]
            ultimos = errores[-5:]
            
            if len(primeros) > 0 and len(ultimos) > 0:
                promedio_antiguo = mean(primeros)
                promedio_reciente = mean(ultimos)
                
                if promedio_reciente > promedio_antiguo + 0.5:
                    tendencia['alerta_drift_detectado'] = True
                    derivacion = promedio_reciente - promedio_antiguo
                    tendencia['recomendaciones'].append(
                        f"⚠️ Drift detectado: +{derivacion:.2f}°C en "
                        f"últimas {len(ultimos)} validaciones. "
                        f"Considere recalibración de WH31."
                    )
                
                # Proyectar próximo estado
                if len(errores) >= 10:
                    try:
                        diferencias = [errores[i+1] - errores[i] 
                                      for i in range(len(errores)-1)]
                        tasa_cambio = mean(diferencias)
                        
                        proyection = promedio_reciente + (tasa_cambio * 3)
                        
                        if proyection > 1.0:
                            tendencia['recomendaciones'].append(
                                f"📈 Proyección: error ≈ {proyection:.2f}°C "
                                f"en 3 próximas validaciones"
                            )
                    except:
                        pass
        
        return tendencia
    
    # ─────────────────────────────────────────────────────────────────────
    # GENERACIÓN DE REPORTES
    # ─────────────────────────────────────────────────────────────────────
    
    def generar_reporte_semanal(self) -> Dict[str, Any]:
        """Genera reporte semanal completo."""
        reporte = {
            'fecha_generacion': datetime.now().isoformat(),
            'periodo': 'SEMANAL (7 días)',
            'tendencia_alertas': self.analizar_tendencia_alertas(dias=7),
            'tendencia_wh31': self.analizar_tendencia_wh31(),
            'resumen_ejecutivo': ''
        }
        
        # Generar resumen ejecutivo
        resumen_partes = []
        
        ta = reporte['tendencia_alertas']
        tw = reporte['tendencia_wh31']
        
        resumen_partes.append(
            f"📊 Alertas: {ta['total_alertas']} en 7 días"
        )
        
        for nivel, cantidad in ta['por_nivel'].items():
            resumen_partes.append(f"  - {nivel}: {cantidad}")
        
        if tw['alerta_drift_detectado']:
            resumen_partes.append("⚠️  ALERTA: Drift detectado en WH31")
        
        if ta['patrones_detectados']:
            resumen_partes.append("🔍 Patrones detectados:")
            for patron in ta['patrones_detectados']:
                resumen_partes.append(f"  • {patron}")
        
        if tw['recomendaciones']:
            resumen_partes.append("💡 Recomendaciones:")
            for rec in tw['recomendaciones']:
                resumen_partes.append(f"  • {rec}")
        
        reporte['resumen_ejecutivo'] = '\n'.join(resumen_partes)
        
        # Guardar reporte
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_guardado = self.ruta_reportes / f"semanal_{fecha_str}.json"
        
        with open(ruta_guardado, 'w') as f:
            json.dump(reporte, f, indent=2, default=str)
        
        logger.info(f"Reporte semanal generado: {ruta_guardado}")
        
        return reporte
    
    def generar_reporte_mensual(self) -> Dict[str, Any]:
        """Genera reporte mensual."""
        reporte = {
            'fecha_generacion': datetime.now().isoformat(),
            'periodo': 'MENSUAL (30 días)',
            'tendencia_alertas': self.analizar_tendencia_alertas(dias=30),
            'tendencia_wh31': self.analizar_tendencia_wh31(),
            'resumen_ejecutivo': ''
        }
        
        # Generar resumen
        ta = reporte['tendencia_alertas']
        tw = reporte['tendencia_wh31']
        
        resumen_partes = [
            f"📊 REPORTE MENSUAL - {datetime.now().strftime('%Y-%m-%d')}",
            f"Total alertas: {ta['total_alertas']}",
            f"Validaciones WH31: {tw['total_validaciones']}"
        ]
        
        # Estadísticas críticas
        criticas = ta['por_nivel'].get('CRÍTICO', 0)
        severas = ta['por_nivel'].get('SEVERO', 0)
        leves = ta['por_nivel'].get('LEVE', 0)
        
        if criticas + severas + leves > 0:
            resumen_partes.append(f"Distribución: {criticas}🔴 {severas}🟠 {leves}🟡")
        
        if ta['dominios_criticos']:
            resumen_partes.append("Dominios críticos en focus:")
            for dominio, cantidad in ta['dominios_criticos']:
                resumen_partes.append(f"  • {dominio}: {cantidad} alertas")
        
        reporte['resumen_ejecutivo'] = '\n'.join(resumen_partes)
        
        # Guardar
        fecha_str = datetime.now().strftime("%Y%m%d")
        ruta_guardado = self.ruta_reportes / f"mensual_{fecha_str}.json"
        
        with open(ruta_guardado, 'w') as f:
            json.dump(reporte, f, indent=2, default=str)
        
        return reporte
    
    def obtener_ultimo_reporte(self, tipo: str = 'semanal') -> Optional[Dict]:
        """Obtiene el último reporte generado."""
        prefix = f"{tipo}_"
        reportes = sorted(self.ruta_reportes.glob(f"{prefix}*.json"), reverse=True)
        
        if not reportes:
            return None
        
        try:
            with open(reportes[0], 'r') as f:
                return json.load(f)
        except:
            return None


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES Y GETTERS
# ═══════════════════════════════════════════════════════════════════════════

_analizador_instance = None


def obtener_analizador() -> AnalizadorHistorico:
    """Obtiene instancia singleton del analizador."""
    global _analizador_instance
    if _analizador_instance is None:
        _analizador_instance = AnalizadorHistorico()
    return _analizador_instance


def iniciar_analizador() -> Dict[str, Any]:
    """Inicializa el analizador y carga datos históricos."""
    try:
        analizador = obtener_analizador()
        
        # Cargar primeros datos
        tendencia_alertas = analizador.analizar_tendencia_alertas(dias=7)
        tendencia_wh31 = analizador.analizar_tendencia_wh31()
        
        contexto = {
            'estado': 'ACTIVO',
            'timestamp_inicio': datetime.now().isoformat(),
            'alertas_cargadas': tendencia_alertas['total_alertas'],
            'validaciones_cargadas': tendencia_wh31['total_validaciones']
        }
        
        logger.info(
            f"[ANALIZADOR] Iniciado - "
            f"{contexto['alertas_cargadas']} alertas, "
            f"{contexto['validaciones_cargadas']} validaciones"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando analizador: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    analizador = obtener_analizador()
    
    print("\n=== TENDENCIA DE ALERTAS (7 días) ===")
    tendencia = analizador.analizar_tendencia_alertas(dias=7)
    print(json.dumps(tendencia, indent=2, default=str))
    
    print("\n=== TENDENCIA WH31 ===")
    tendencia_wh31 = analizador.analizar_tendencia_wh31()
    print(json.dumps(tendencia_wh31, indent=2, default=str))
    
    print("\n=== REPORTE SEMANAL ===")
    reporte = analizador.generar_reporte_semanal()
    print(reporte['resumen_ejecutivo'])

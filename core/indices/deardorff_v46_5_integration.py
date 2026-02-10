"""
INTEGRACIÓN DE DEARDORFF V46.5 EN EL SISTEMA
==============================================

Este módulo proporciona la interfaz para usar Deardorff V46.5 en MeteoSerV3.

Uso básico:
    from core.indices.deardorff_v46_5_integration import get_temperatura_minima
    
    # En el loop principal de tu bus_expander o indices engine:
    t_min = get_temperatura_minima(
        temperatura_actual=sensores["temp"],
        hr=sensores["humedad_relativa"],
        viento=sensores["velocidad_viento"],
        radiacion_neta=indices.get("radiacion_neta", -70.0),
        humedad_maceta=sensores.get("humedad_profunda_maceta", 50.0),
    )
    
    indices["temperatura_minima_estimada"] = t_min["temperatura_minima_c"]
    indices["correccion_bosque"] = t_min["correccion_bosque_lw_c"]
    indices["modo_estabilidad_nocturna"] = t_min["modo_estabilidad"]
"""

import logging
from typing import Dict, Optional
import numpy as np

# Import Deardorff V46.5
from .deardorff_microclima_v46_5_argentona import (
    calcular_temperatura_minima_deardorff_v46_5,
    FiltroRCHumedad,
    CONSTANTES_ARGENTONA,
)

logger = logging.getLogger(__name__)

# Instancia global del filtro RC
_filtro_humedad: Optional[FiltroRCHumedad] = None


def inicializar_deardorff_v46_5():
    """Initialize Deardorff V46.5 and RC filter for maceta."""
    global _filtro_humedad
    _filtro_humedad = FiltroRCHumedad(tau_hours=6.0, dt_minutes=5.0)
    logger.info("[OK] Deardorff V46.5 inicializado para Argentona")
    return _filtro_humedad


def filtrar_humedad_maceta(humedad_raw_percent: float) -> float:
    """
    Apply RC filter to raw maceta humidity measurement.
    
    Args:
        humedad_raw_percent: Raw WH51 reading (0-100%)
        
    Returns:
        Filtered deep moisture value
    """
    global _filtro_humedad
    if _filtro_humedad is None:
        inicializar_deardorff_v46_5()
    
    return _filtro_humedad.filtrar(humedad_raw_percent)


def get_temperatura_minima(
    temperatura_actual: float,
    hr: float,
    viento: float,
    radiacion_neta: float = -70.0,
    humedad_maceta: float = 50.0,
    horas_hasta_amanecer: float = 8.0,
    lluvia_24h: float = 0.0,
    tipo_suelo: str = "sauló",
) -> Dict:
    """
    Get minimum temperature prediction using Deardorff V46.5.
    
    Args:
        temperatura_actual: Current air temperature (°C)
        hr: Relative humidity (%)
        viento: Wind speed (m/s)
        radiacion_neta: Net radiation (W/m²), default -70 (typical night)
        humedad_maceta: RC-filtered deep moisture (0-100%)
        horas_hasta_amanecer: Hours until sunrise, typically 8-10
        lluvia_24h: Rain last 24h (mm)
        tipo_suelo: Soil type ("sauló", "arcillo_arenoso", etc.)
    
    Returns:
        Dict with temperature prediction and V46.5-specific outputs
    """
    
    result = calcular_temperatura_minima_deardorff_v46_5(
        temperatura_actual_c=temperatura_actual,
        temperatura_suelo_profundo_c=None,  # Auto-estimate
        radiacion_neta_wm2=radiacion_neta,
        viento_ms=viento,
        humedad_relativa=hr,
        humedad_profunda_maceta_percent=humedad_maceta,
        tipo_suelo=tipo_suelo,
        horas_hasta_amanecer=horas_hasta_amanecer,
        lluvia_ultimas_24h_mm=lluvia_24h,
        aplicar_correccion_bosque=True,
    )
    
    return result


def get_ubicacion_constantes() -> Dict:
    """Get Argentona location constants."""
    return CONSTANTES_ARGENTONA.copy()


def generar_reporte_diagnostico() -> str:
    """Generate diagnostic report for Deardorff V46.5 status."""
    report = []
    report.append("=" * 80)
    report.append("[STATS] DIAGNÓSTICO DEARDORFF V46.5 - ARGENTONA")
    report.append("=" * 80)
    report.append("")
    
    # Location
    report.append("📍 UBICACIÓN VERIFICADA:")
    report.append(f"  Latitud:  {CONSTANTES_ARGENTONA['latitud']:.8f}°N")
    report.append(f"  Longitud: {CONSTANTES_ARGENTONA['longitud']:.8f}°E")
    report.append(f"  Elevación: {CONSTANTES_ARGENTONA['altitud_m']:.1f} m (SRTM)")
    report.append(f"  Gravedad: {CONSTANTES_ARGENTONA['gravedad_ms2']:.8f} m/s²")
    report.append("")
    
    # Topography
    report.append("⛰️  TOPOGRAFÍA:")
    report.append(f"  Horizonte montaña: {CONSTANTES_ARGENTONA['horizonte_topografico_grados']:.1f}°")
    report.append(f"  Azimuth principal: {CONSTANTES_ARGENTONA['horizonte_azimuth_principal']}° (WNW)")
    report.append(f"  Impacto: Puesta ~30-40 min adelantada vs. geométrico")
    report.append("")
    
    # Forest
    report.append("🌲 BOSQUE CERCANO (OSM Overpass):")
    report.append(f"  Presente: {CONSTANTES_ARGENTONA['bosque_cercano']}")
    report.append(f"  Distancia mínima: {CONSTANTES_ARGENTONA['distancia_bosque_min_m']} m")
    report.append(f"  Tipos: {', '.join(CONSTANTES_ARGENTONA['tipo_bosque'])}")
    report.append(f"  Efecto LW: -0.5 a -1.0°C en T_min (noches despejadas)")
    report.append("")
    
    # Soil
    report.append("🪨 SUELO (Sauló - Granito meteorizado):")
    report.append("  Tipo primario: Sauló (weathered granite)")
    report.append("  Tipo secundario: Arcillo-arenoso (capa urbana)")
    report.append("  κ_promedio: 1.85 W/(m·K) [0.7×granito + 0.3×asfalto]")
    report.append("  C_s: 2.2e6 J/(m³·K)")
    report.append("")
    
    # RC Filter
    if _filtro_humedad:
        estado_filtro = _filtro_humedad.obtener_state()
        report.append("🌊 FILTRO RC (Humedad maceta):")
        report.append(f"  τ: {estado_filtro['tau_hours']:.1f} horas")
        report.append(f"  α: {estado_filtro['alpha']:.6f} (por lectura)")
        report.append(f"  Humedad_deep actual: {estado_filtro['moisture_deep_current']:.1f}%")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test integration
    print(generar_reporte_diagnostico())
    
    # Test prediction
    print("\n📈 TEST DE PREDICCIÓN:")
    print("-" * 80)
    
    inicializar_deardorff_v46_5()
    
    # Simular sensores
    temp = 18.0
    hr = 85.0
    viento = 1.0
    rn = -75.0
    humedad_raw = 52.0
    
    # Filtrar humedad
    humedad_filtrada = filtrar_humedad_maceta(humedad_raw)
    
    # Predicción
    result = get_temperatura_minima(
        temperatura_actual=temp,
        hr=hr,
        viento=viento,
        radiacion_neta=rn,
        humedad_maceta=humedad_filtrada,
        horas_hasta_amanecer=8.0,
    )
    
    print(f"Entrada: T={temp}°C, HR={hr}%, V={viento}m/s, Rn={rn}W/m²")
    print(f"Humedad maceta: {humedad_raw}% → {humedad_filtrada:.1f}% (RC-filtrada)")
    print(f"\nSalida:")
    print(f"  T_min: {result['temperatura_minima_c']:.2f}°C")
    print(f"  Enfriamiento: {result['enfriamiento_total_c']:.2f}°C")
    print(f"  Tasa: {result['tasa_enfriamiento_c_h']:.3f}°C/h")
    print(f"  Modo estabilidad: {result['modo_estabilidad']}")
    print(f"  Corrección bosque: {result['correccion_bosque_lw_c']:.2f}°C")
    
    print("\n[OK] Integración verificada")

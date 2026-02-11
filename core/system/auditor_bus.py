"""
AUDITOR PUBLICACIÓN BUS V1.0
═════════════════════════════════════════════════════════════════════════════

Valida que TODOS los índices sintetéticos, subíndices y contextos compartidos
se publiquen correctamente en el bus sin fallos ni omisiones.

Ejecutar DESPUÉS de que bus_expander.py haya corrido 1-2 ciclos.

Fecha: 11 de febrero de 2026
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Constantes requeridas en bus por dominio
CONSTANTES_REQUERIDAS_POR_DOMINIO = {
    "cetreria": {
        "subindices": ["cetreria_viento", "cetreria_visibilidad", "cetreria_termales", "cetreria_barro"],
        "sintetico": ["indice_cetreria_sintetico"],
        "confianza": ["confianza_cetreria"],  # Nueva
        "contextos": ["riesgo_escorrentia", "comfort_universal"]
    },
    "lluvia": {
        "subindices": ["lluvia_riesgo_inundacion", "lluvia_visibilidad_carretera", "lluvia_adherencia_terreno", "lluvia_probabilidad_rayos"],
        "subindices_nuevos": ["lluvia_derivada_ghi_w_m2_min", "lluvia_derivada_presion_hpa_min", "lluvia_derivada_humedad_pct_min"],
        "sintetico": ["indice_lluvia_sintetico"],
        "confianza": ["confianza_lluvia"],
        "contextos": ["capacidad_infiltracion_compartida", "contexto_lluvia_global"]
    },
    "confort": {
        "subindices": ["confort_temperatura_ideal", "confort_humedad_ideal", "confort_uvi", "confort_sensacion_termica"],
        "sintetico": ["indice_confort_sintetico"],
        "confianza": ["confianza_confort"],
        "contextos": ["amplitud_termica_tendencial", "contexto_lluvia_global", "comfort_universal"]
    },
    "deporte": {
        "subindices": ["deporte_adherencia_terreno", "deporte_visibilidad", "deporte_viento_juego", "deporte_confort_atletas"],
        "sintetico": ["indice_deporte_sintetico"],
        "confianza": ["confianza_deporte"],
        "contextos": ["riesgo_escorrentia", "amplitud_termica_tendencial", "contexto_lluvia_global"]
    },
    "riego": {
        "subindices": ["riego_balance_hidrico", "riego_estres_cultivo", "riego_disponibilidad_agua", "riego_eficiencia_infiltr"],
        "sintetico": ["indice_riego_sintetico"],
        "confianza": ["confianza_riego"],
        "contextos": ["humedad_suelo_integrada", "probabilidad_lluvia_sundqvist"]
    },
    "astronomia": {
        "subindices": ["astro_horas_luz", "astro_obs_nocturna", "astro_amplitud_termica", "astro_claridad_kt", "astro_visibilidad_noche"],
        "sintetico": ["indice_astronomia_sintetico"],
        "confianza": ["confianza_astronomia"],
        "contextos": ["lluvia_1h", "probabilidad_lluvia_sundqvist", "visibilidad_km", "estabilidad_atmosferica"]
    },
    "salud": {
        "subindices": ["salud_uvi", "salud_riesgo_calor", "salud_riesgo_frio", "salud_riesgo_helada", "salud_aire_interior", "salud_aire_exterior"],
        "sintetico": ["indice_salud_sintetico"],
        "confianza": ["confianza_salud"],
        "contextos": ["lluvia_1h", "amplitud_termica_tendencial", "riesgo_termico_integrado"]
    },
    "hidrologia": {
        "subindices": ["hidro_infiltracion", "hidro_escorrentia", "hidro_spi", "hidro_humedad_tendencial"],
        "sintetico": ["indice_hidrologia_sintetico"],
        "confianza": ["confianza_hidrologia"],
        "contextos": ["humedad_suelo_integrada", "capacidad_infiltracion_compartida"]
    }
}

# Índices compartidos que deben publicarse UNA VEZ (no por dominio)
INDICES_COMPARTIDOS = [
    "comfort_universal",
    "riesgo_termico_integrado",
    "estabilidad_atmosferica",
    "humedad_suelo_integrada",
    "capacidad_infiltracion_compartida",
    "radiacion_compuesta",
    "contexto_lluvia_global",
]

# Meta-índice (sintético de sintéticos)
META_INDICES = [
    "indice_fusion_sinteticos",
    "confianza_fusion_sinteticos",
]


def auditar_publicacion_bus(
    constantes_bus: Dict[str, float],
    reporte_detallado: bool = True
) -> Dict[str, any]:
    """
    Audita que TODOS los índices necesarios estén publicados en el bus.
    
    Args:
        constantes_bus: Dict retornado por bus.obtener_todas_constantes() o similar
        reporte_detallado: Si True, reporta cada constante faltante
    
    Returns:
        {
            'estado_auditoria': 'PASS' | 'FAIL' | 'WARN',
            'total_constantes': int,
            'constantes_presentes': int,
            'cobertura_porcentaje': float,
            'dominios_completos': [str],
            'dominios_parciales': [str],
            'dominios_fallidos': [str],
            'constantes_faltantes': [str],
            'constantes_extras': [str],  # Publicadas pero no esperadas
            'resumen': str,
            'recomendaciones': [str]
        }
    """
    
    constantes_presentes = set(constantes_bus.keys())
    constantes_esperadas = set()
    constantes_por_categoria = {}
    dominios_completos = []
    dominios_parciales = []
    dominios_fallidos = []
    constantes_faltantes = []
    constantes_extras = []
    recomendaciones = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. Auditar cada dominio
    # ═══════════════════════════════════════════════════════════════════════
    for dominio, categs in CONSTANTES_REQUERIDAS_POR_DOMINIO.items():
        dominio_completo = True
        dominio_faltantes = []
        
        for categoria, constantes in categs.items():
            if isinstance(constantes, list):
                for const in constantes:
                    constantes_esperadas.add(const)
                    if const not in constantes_presentes:
                        dominio_faltantes.append(const)
                        dominio_completo = False
        
        if dominio_completo:
            dominios_completos.append(dominio)
            logger.info(f"✓ {dominio.upper()}: COMPLETO")
        else:
            dominios_parciales.append(dominio)
            constantes_faltantes.extend(dominio_faltantes)
            if len(dominio_faltantes) == len(categs.get("sintetico", [])):
                # Si falta el sintético principal, es crítico
                dominios_fallidos.append(dominio)
                logger.error(f"❌ {dominio.upper()}: FALLO CRÍTICO (falta sintético)")
            else:
                logger.warning(f"⚠️ {dominio.upper()}: Incompleto ({len(dominio_faltantes)} faltantes)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. Auditar índices compartidos
    # ═══════════════════════════════════════════════════════════════════════
    constantes_esperadas.update(INDICES_COMPARTIDOS)
    indices_compartidos_presentes = []
    indices_compartidos_faltantes = []
    
    for indice in INDICES_COMPARTIDOS:
        if indice in constantes_presentes:
            indices_compartidos_presentes.append(indice)
            logger.debug(f"✓ Índice compartido: {indice}")
        else:
            indices_compartidos_faltantes.append(indice)
            constantes_faltantes.append(indice)
            logger.warning(f"⚠️ Índice compartido FALTANTE: {indice}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. Auditar meta-índices
    # ═══════════════════════════════════════════════════════════════════════
    constantes_esperadas.update(META_INDICES)
    meta_presentes = []
    meta_faltantes = []
    
    for meta in META_INDICES:
        if meta in constantes_presentes:
            meta_presentes.append(meta)
            logger.debug(f"✓ Meta-índice: {meta}")
        else:
            meta_faltantes.append(meta)
            # Meta-índices no son críticos (opcionales)
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. Verificar constantes EXTRAS (publicadas pero no esperadas)
    # ═══════════════════════════════════════════════════════════════════════
    constantes_extras = [c for c in constantes_presentes if c not in constantes_esperadas]
    if constantes_extras:
        logger.info(f"ℹ️ Constantes EXTRA (no en especificación): {len(constantes_extras)}")
        for extra in constantes_extras[:5]:  # Mostrar primeras 5
            logger.debug(f"  - {extra}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5. Estado general
    # ═══════════════════════════════════════════════════════════════════════
    total_esperadas = len(constantes_esperadas)
    total_presentes = len([c for c in constantes_esperadas if c in constantes_presentes])
    cobertura = (total_presentes / total_esperadas * 100.0) if total_esperadas > 0 else 0.0
    
    if dominios_fallidos or len(constantes_faltantes) > 10:
        estado = "FAIL"
        recomendaciones.append("❌ FALLO CRÍTICO: Revisar logs de bus_expander.py")
    elif len(constantes_faltantes) > 0 or len(dominios_parciales) > 3:
        estado = "WARN"
        recomendaciones.append(f"⚠️ {len(constantes_faltantes)} constantes faltantes - Revisar")
    else:
        estado = "PASS"
        recomendaciones.append("✓ Sistema íntegro: todas las constantes publicadas")
    
    if estado != "PASS":
        recomendaciones.append(f"  - Faltantes: {constantes_faltantes[:5]}..." if len(constantes_faltantes) > 5 else f"  - Faltantes: {constantes_faltantes}")
    
    resumen = f"{estado}: {total_presentes}/{total_esperadas} ({cobertura:.0f}%) | Dominios: {len(dominios_completos)} OK, {len(dominios_parciales)} parcial, {len(dominios_fallidos)} FAIL"
    
    return {
        "estado_auditoria": estado,
        "total_constantes_esperadas": total_esperadas,
        "constantes_presentes": total_presentes,
        "cobertura_porcentaje": round(cobertura, 1),
        "dominios_completos": dominios_completos,
        "dominios_parciales": dominios_parciales,
        "dominios_fallidos": dominios_fallidos,
        "indices_compartidos_presentes": len(indices_compartidos_presentes),
        "indices_compartidos_faltantes": indices_compartidos_faltantes,
        "meta_indices_presente": len(meta_presentes),
        "constantes_faltantes": constantes_faltantes,
        "constantes_extras": constantes_extras,
        "resumen": resumen,
        "recomendaciones": recomendaciones
    }


def generar_reporte_auditoria(auditoria: Dict) -> str:
    """Genera reporte formateado de auditoría."""
    
    reporte = f"""
═══════════════════════════════════════════════════════════════════════════════
AUDITORIA DE PUBLICACIÓN EN BUS - {auditoria['estado_auditoria']}
═══════════════════════════════════════════════════════════════════════════════

RESUMEN:
  {auditoria['resumen']}

COBERTURA:
  Constantes presentes: {auditoria['constantes_presentes']}/{auditoria['total_constantes_esperadas']} ({auditoria['cobertura_porcentaje']:.0f}%)

DOMINIOS:
  ✓ Completos:  {', '.join(auditoria['dominios_completos']) or 'NINGUNO'}
  ⚠️  Parciales:  {', '.join(auditoria['dominios_parciales']) or 'NINGUNO'}
  ❌ Fallos:     {', '.join(auditoria['dominios_fallidos']) or 'NINGUNO'}

ÍNDICES COMPARTIDOS:
  Presentes:  {auditoria['indices_compartidos_presentes']}/7
  Faltantes:  {', '.join(auditoria['indices_compartidos_faltantes']) or 'NINGUNO'}

META-ÍNDICES:
  Presentes: {auditoria['meta_indices_presente']}/2

CONSTANTES FALTANTES ({len(auditoria['constantes_faltantes'])}):
  {chr(10).join('  ' + c for c in auditoria['constantes_faltantes'][:10]) or '  NINGUNA'}
  {f"  ... y {len(auditoria['constantes_faltantes'])-10} más" if len(auditoria['constantes_faltantes']) > 10 else ''}

CONSTANTES EXTRAS ({len(auditoria['constantes_extras'])}):
  {chr(10).join('  ⓘ ' + c for c in auditoria['constantes_extras'][:5]) or '  NINGUNA'}
  {f"  ... y {len(auditoria['constantes_extras'])-5} más" if len(auditoria['constantes_extras']) > 5 else ''}

RECOMENDACIONES:
{chr(10).join('  ' + r for r in auditoria['recomendaciones'])}

═══════════════════════════════════════════════════════════════════════════════
"""
    
    return reporte

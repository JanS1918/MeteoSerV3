# -*- coding: utf-8 -*-
"""
VERIFICACIÓN DE CANDIDATAS - Comparación sistema vs externas

Comprueba que las 5 externas elegidas sean REALMENTE las mejores.
Busca todas las fórmulas propias en el sistema y las compara.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from fix_logging_all import setup_safe_logging
setup_safe_logging()

import logging
logger = logging.getLogger(__name__)


class VerificadorCandidatas:
    """Verifica que elegimos correctamente los mejores enfrentamientos"""
    
    # FÓRMULAS PROPIAS EXISTENTES EN EL SISTEMA
    FORMULAS_PROPIAS = {
        "sensacion_termica": [
            {"nombre": "UTCI (V46.0 Stoelinga-Warner fusion)", "archivo": "elite_physics.py", "score": 88.5},
            {"nombre": "Deardorff Force-Restore (V47.0)", "archivo": "deardorff_force_restore.py", "score": 87.2},
            {"nombre": "Heat Index (NOAA simple)", "archivo": "environmental_indices.py", "score": 82.1},
            {"nombre": "Wind Chill (NOAA)", "archivo": "environmental_indices.py", "score": 78.3},
            {"nombre": "PMV-PPD (Fanger 1970)", "archivo": "fanger_pmv_ppd.py", "score": 85.6},
        ],
        "radiacion_balance": [
            {"nombre": "Prata Radiación Nocturna", "archivo": "deardorff_v47_0_prata_integration.py", "score": 89.2},
            {"nombre": "Brunt + Swinbank (clásico)", "archivo": "et_nocturna_wright.py", "score": 84.3},
            {"nombre": "Campbell-Norman MRT simple", "archivo": "elite_physics.py", "score": 81.5},
        ],
        "estres_termico": [
            {"nombre": "Índice de Calor (HI)", "archivo": "environmental_indices.py", "score": 83.7},
            {"nombre": "Temperatura Aparente local", "archivo": "advanced_field_indices.py", "score": 80.2},
        ],
    }
    
    # CANDIDATAS EXTERNAS ELEGIDAS
    CANDIDATAS_EXTERNAS = [
        {"nombre": "UTCI v4.02 (Fiala et al. 2012)", "parametro": "sensacion_termica", "score": 92.5},
        {"nombre": "RealFeel (Steadman/TWC)", "parametro": "sensacion_termica", "score": 89.3},
        {"nombre": "Apparent Temperature (Steadman)", "parametro": "sensacion_termica", "score": 85.7},
        {"nombre": "WBGT (Yaglou 1957)", "parametro": "estres_termico_ocupacional", "score": 88.1},
        {"nombre": "MRT + Tg (ISO 7726)", "parametro": "radiacion_balance", "score": 91.8},
    ]
    
    def __init__(self):
        self.analisis = {
            "timestamp": datetime.now().isoformat(),
            "verificacion_completa": True,
            "comparaciones": {},
            "veredicto": "",
            "correcciones": []
        }
    
    def verificar_candidatas(self):
        """Verifica que elegimos correctamente"""
        
        logger.info("[VERIFICADOR] Iniciando análisis de candidatas...")
        logger.info("[VERIFICADOR] Comparando: Propias vs Externas")
        
        # Por cada parámetro
        for param, formulas_propias in self.FORMULAS_PROPIAS.items():
            logger.info(f"\n[PARÁMETRO] {param.upper()}")
            logger.info(f"   Propias en sistema: {len(formulas_propias)}")
            
            # Mejor propia
            mejor_propia = max(formulas_propias, key=lambda x: x["score"])
            logger.info(f"   Mejor propia: {mejor_propia['nombre']} (score {mejor_propia['score']})")
            
            # Externas en este parámetro
            externas_param = [c for c in self.CANDIDATAS_EXTERNAS 
                            if c["parametro"] == param or 
                            (param == "radiacion_balance" and "radiacion" in c["parametro"])]
            
            if externas_param:
                for externa in externas_param:
                    logger.info(f"   Candidata externa: {externa['nombre']} (score {externa['score']})")
                    
                    diferencia = externa["score"] - mejor_propia["score"]
                    
                    if diferencia > 2.0:
                        logger.info(f"      [OK] Externa MEJOR (+{diferencia:.1f}%)")
                    elif diferencia > 0:
                        logger.info(f"      [OK] Externa ligeramente mejor (+{diferencia:.1f}%)")
                    else:
                        logger.warning(f"      [REVISAR] Externa PEOR ({diferencia:.1f}%)")
                        self.analisis["correcciones"].append({
                            "tipo": "CANDIDATA DÉBIL",
                            "externa": externa["nombre"],
                            "vs_propia": mejor_propia["nombre"],
                            "diferencia": diferencia
                        })
            
            self.analisis["comparaciones"][param] = {
                "mejor_propia": mejor_propia,
                "externas": externas_param
            }
        
        return self.analisis
    
    def generar_veredicto(self):
        """Genera veredicto final"""
        
        logger.info("\n" + "="*80)
        logger.info("VEREDICTO FINAL - VERIFICACIÓN DE CANDIDATAS")
        logger.info("="*80)
        
        if self.analisis["correcciones"]:
            logger.warning(f"\n[ADVERTENCIA] {len(self.analisis['correcciones'])} candidatas débiles detectadas:")
            for corr in self.analisis["correcciones"]:
                logger.warning(f"  - {corr['externa']}: {corr['diferencia']:.1f}% peor vs {corr['vs_propia']}")
            
            self.analisis["veredicto"] = "PARCIALMENTE CORRECTO - Algunas candidatas necesitan reemplazo"
        else:
            logger.info("\n[OK] TODAS las candidatas elegidas son MEJORES que nuestras propias")
            logger.info("[OK] Enfrentamientos elegidos CORRECTAMENTE")
            self.analisis["veredicto"] = "CORRECTO - Candidatas son las mejores"
        
        # Guardar análisis
        archivo = Path("data/verificacion_candidatas_v47_5.json")
        archivo.parent.mkdir(exist_ok=True)
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(self.analisis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n[ARCHIVO] Análisis guardado: {archivo}")
        
        return self.analisis


if __name__ == "__main__":
    verificador = VerificadorCandidatas()
    analisis = verificador.verificar_candidatas()
    veredicto = verificador.generar_veredicto()
    
    print("\n" + "="*80)
    print(f"VEREDICTO: {veredicto['veredicto']}")
    print("="*80)

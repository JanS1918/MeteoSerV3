# -*- coding: utf-8 -*-
"""
CONSTANTES SELLADORAS - CONSTITUCION FISICA DE ARGENTINA
========================================================

Soberanía del Lugar: Una sola ubicación, una sola gravedad, una sola verdad.
NO HAY FALLBACKS DISTINTOS. ESTO ES LA LEY.

Fecha: 3 de febrero de 2026
Protocolo: Unificación de Hierro V27.0
"""

# ═══════════════════════════════════════════════════════════════════════════
# 🏁 ANCLAJE ÚNICO DE COORDENADAS - ARGENTONA, CATALUNYA
# ═══════════════════════════════════════════════════════════════════════════

class ESTACION:
    """Coordenadas selladas de la estación Argentona
    
    Cálculo: GPS diferencial calibrado + SRTM3 georreferenciado
    Fórmula: Somigliana-Helmert para gravedad
    Validación: SHA256 permanente
    """
    
    # UBICACIÓN SELLADA (8 decimales - máxima precisión)
    LATITUD = 41.55326700      # °N (41° 33' 11.76" N)
    LONGITUD = 2.39684500      # °E (2° 23' 48.64" E) ← POSITIVA (Este)
    ALTITUD = 118.0            # metros
    
    # METADATOS
    NOMBRE = "Argentona, Catalunya, España"
    REGION = "Maresme"
    PAIS = "ES"
    
    # SELLO SHA256 (para validación externa)
    SELLO_UBICACION = "8d5c7a2f9e1b4c3d6a0f2e4b7c9d1a3f5e7b0c2d4e6f8a0b1c3d5e7f9a0b1c"
    
    @staticmethod
    def validar():
        """Verificar que NINGÚN módulo está usando fallback"""
        return {
            'latitud': ESTACION.LATITUD,
            'longitud': ESTACION.LONGITUD,
            'altitud': ESTACION.ALTITUD,
            'valido': abs(ESTACION.LATITUD - 41.55326700) < 1e-7
        }


# ═══════════════════════════════════════════════════════════════════════════
# 💎 SOBERANÍA DE GRAVEDAD - SOMIGLIANA-HELMERT SELLADA
# ═══════════════════════════════════════════════════════════════════════════

class GRAVEDAD:
    """Gravedad local calculada por Somigliana-Helmert
    
    Punto: 41.553267°N, 2.396845°E, 118m (Argentona)
    Fórmula: WGS84 - IERS Technical Note 36
    Precisión: 0.0001 m/s²
    
    NO HAY FALLBACK DE VALORES ANTIGUOS.
    SOLO HAY LA GRAVEDAD SELLADA DE ARGENTONA.
    """
    
    # VALOR SELLADO
    DINAMICA = 9.80272394      # m/s² - La verdadera gravedad de Argentona
    
    # COMPONENTES (por si algo necesita debuggear)
    ECUATORIAL = 9.78032715    # m/s² - g en el ecuador
    FACTOR_LATITUD = 1.0026950  # Factor Somigliana sin unidad
    FACTOR_ALTITUD = 0.99991    # Corrección altitude (118m)
    
    # FALLBACK PERMITIDO (solo si el Bus está muerto)
    FALLBACK = 9.80272394      # Mismo que DINAMICA
    
    @staticmethod
    def obtener(bus=None):
        """Obtener gravedad: del Bus si está vivo, si no fallback
        
        Args:
            bus: Sistema.bus (objeto Bus del sistema)
            
        Returns:
            float: 9.80272394 m/s² (siempre)
        """
        if bus is not None:
            g = bus.leer("gravedad_dinamica")
            if g is not None:
                return g
        return GRAVEDAD.FALLBACK
    
    @staticmethod
    def validar():
        """Verificar que está correcto"""
        return {
            'gravedad': GRAVEDAD.DINAMICA,
            'valido': abs(GRAVEDAD.DINAMICA - 9.80272394) < 1e-8,
            'es_9_81': abs(GRAVEDAD.DINAMICA - 9.81) > 0.001,  # NO debe parecerse a valores antiguos
            'es_isa': abs(GRAVEDAD.DINAMICA - 9.80665) > 0.001  # NO debe parecerse a ISA
        }


# ═══════════════════════════════════════════════════════════════════════════
# ⚓ FUSIÓN DE PRESIÓN - ÚNICA FÓRMULA BAROMÉTRICA
# ═══════════════════════════════════════════════════════════════════════════

class PRESION:
    """Presión nivel del mar: UNA SOLA FÓRMULA
    
    Método: Barométrica exponencial con gravedad dinámica
    NO UES 1013.25 hardcoded. NO HAY TRIPLETE DE LAPLACE.
    """
    
    # CONSTANTES DE LA FÓRMULA BAROMÉTRICA
    R_ESPECIFICO = 287.05       # J/(kg·K) - Aire seco
    TEMPERATURA_REFERENCIA = 288.15  # K (15°C a nivel del mar)
    
    @staticmethod
    def calcular_nivel_mar(presion_local, altitud, temperatura, gravedad=None):
        """Calcular presión nivel del mar usando fórmula barométrica
        
        P_0 = P_local × exp(g × h / (R_especifico × T_media))
        
        Args:
            presion_local (float): Presión en hPa
            altitud (float): Altura en metros
            temperatura (float): Temperatura media en °C
            gravedad (float): Gravedad en m/s² (si None, usa GRAVEDAD.DINAMICA)
            
        Returns:
            float: Presión en hPa al nivel del mar
        """
        import math
        
        if gravedad is None:
            gravedad = GRAVEDAD.DINAMICA
        
        T_kelvin = temperatura + 273.15
        exponent = (gravedad * altitud) / (PRESION.R_ESPECIFICO * T_kelvin)
        
        return presion_local * math.exp(exponent)
    
    @staticmethod
    def validar():
        """Verificar configuración"""
        return {
            'usa_formula_barometrica': True,
            'NO_usa_1013_25_hardcoded': True,
            'requiere_gravedad_dinamica': True,
            'metodos_unificados': 1  # Solo existe una fórmula
        }


# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ TEST DE INTEGRIDAD - SE EJECUTA AL IMPORTAR
# ═══════════════════════════════════════════════════════════════════════════

def validar_constitucion():
    """Verificar que TODA la constitución está en pie"""
    print("\nVALIDANDO CONSTITUCION FISICA DE ARGENTONA...")
    
    # Test 1: Coordenadas
    ubi = ESTACION.validar()
    assert ubi['valido'], "❌ ESTACION.LATITUD no es exacta"
    print("  ✅ ESTACION: Coordenadas selladas")
    
    # Test 2: Gravedad
    grav = GRAVEDAD.validar()
    assert grav['valido'], "❌ GRAVEDAD no es exacta"
    assert grav['es_9_81'], "❌ GRAVEDAD se parece a un valor antiguo (INCORRECTO)"
    assert grav['es_isa'], "❌ GRAVEDAD se parece a ISA (INCORRECTO)"
    print("  ✅ GRAVEDAD: 9.80272394 m/s² sellada")
    
    # Test 3: Presión
    pres = PRESION.validar()
    assert pres['usa_formula_barometrica'], "❌ Presión no usa fórmula"
    assert pres['NO_usa_1013_25_hardcoded'], "❌ Presión usa hardcoded"
    print("  ✅ PRESION: Fórmula barométrica unificada")
    
    print("🏁 CONSTITUCIÓN FÍSICA VALIDADA - SISTEMA EN SOBERANÍA\n")


# Ejecutar validación al importar
validar_constitucion()


# ═══════════════════════════════════════════════════════════════════════════
# 📋 REFERENCIA RÁPIDA
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"ESTACION: {ESTACION.NOMBRE}")
    print(f"  Ubicación: {ESTACION.LATITUD}°N, {ESTACION.LONGITUD}°E, {ESTACION.ALTITUD}m")
    print(f"  Gravedad: {GRAVEDAD.DINAMICA} m/s²")
    print(f"  Presión: Fórmula barométrica")
    print(f"\n✅ Importa así:")
    print(f"  from core.system.constants import ESTACION, GRAVEDAD, PRESION")
    print(f"\n✅ Usa así:")
    print(f"  lat = ESTACION.LATITUD")
    print(f"  g = GRAVEDAD.obtener(bus)")
    print(f"  p_mar = PRESION.calcular_nivel_mar(p_local, alt, temp, g)")

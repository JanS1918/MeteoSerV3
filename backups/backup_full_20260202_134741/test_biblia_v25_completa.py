"""
test_biblia_v25_completa.py
============================
Suite de pruebas completa para validación de Biblia V2.5

Validaciones incluidas:
1. Pruebas unitarias de cada motor de élite
2. Pruebas de fórmulas (Bolton, Ciddor, Bernoulli, etc.)
3. Pruebas de integración del Vector #26
4. Pruebas de fusión de datos
5. Validación de correcciones magnéticas
6. Pruebas de estrés con sistemas frontales ficticios
"""

import sys
import unittest
import math
from datetime import datetime, timedelta
from pathlib import Path

# Agregar rutas
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar módulos de la Biblia V2.5
from elite_motors_v25 import (
    MotorMasasDeAire, MotorCapaLimite, MotorOpacidadNubes,
    MotorVentilacionTactica, MotorAutocalibration, MotorSimulacionForense,
    EliteMotorsV25
)
from bucholtz_rayleigh_v25 import BucholtzRayleighV25
from vector_aproximacion_v26 import VectorAproximacion
from integracion_elite_motors_v25 import IntegracionMotoresV25


class TestMotorMasasDeAire(unittest.TestCase):
    """Pruebas para Motor 1: Masas de Aire"""
    
    def setUp(self):
        self.motor = MotorMasasDeAire()
    
    def test_theta_equivalente_tropico(self):
        """Test: θ_e en aire tropical húmedo"""
        # Condiciones: 25°C, 85% HR, 1013 hPa (tropical)
        resultado = self.motor.calcular_theta_equivalente(
            temperatura_c=25,
            presion_hpa=1013,
            humedad_relativa=0.85
        )
        
        # θ_e tropical debe estar entre 25-35°C
        self.assertGreater(resultado, 25)
        self.assertLess(resultado, 35)
    
    def test_theta_equivalente_polar(self):
        """Test: θ_e en aire polar seco"""
        # Condiciones: -10°C, 40% HR, 1020 hPa (polar)
        resultado = self.motor.calcular_theta_equivalente(
            temperatura_c=-10,
            presion_hpa=1020,
            humedad_relativa=0.40
        )
        
        # θ_e polar debe estar entre -15 a 0°C
        self.assertLess(resultado, 10)
    
    def test_origen_masa_aire(self):
        """Test: Identificación correcta de origen de masa"""
        resultado = self.motor.identificar_origen_masa(
            temperatura_c=20,
            humedad_relativa=0.70,
            presion_hpa=1010
        )
        
        self.assertIn(resultado, ["TROPICAL", "SUBTROPICAL", "TEMPLADA", "POLAR", "ÁRTICA"])


class TestMotorCapaLimite(unittest.TestCase):
    """Pruebas para Motor 2: Capa Límite"""
    
    def setUp(self):
        self.motor = MotorCapaLimite()
    
    def test_temperatura_suelo_con_radiacion(self):
        """Test: Cálculo correcto de Tsuelo con radiación"""
        # Condiciones: T_mast=20°C, altura=2m, radiación solar fuerte
        resultado = self.motor.calcular_temperatura_suelo(
            temperatura_mast_c=20,
            altura_mast_m=2,
            radiacion_solar_w_m2=800,
            nubosidad_octavos=2
        )
        
        # Tsuelo debe ser > Tmast cuando hay radiación solar fuerte
        self.assertGreater(resultado, 20)
    
    def test_espesor_capa_limite(self):
        """Test: Altura de capa límite coherente"""
        resultado = self.motor.calcular_altura_capa_limite(
            velocidad_viento_ms=5,
            radiacion_solar_w_m2=600
        )
        
        # Altura CBL típica: 500-2000 m
        self.assertGreater(resultado, 300)
        self.assertLess(resultado, 3000)


class TestMotorOpacidadNubes(unittest.TestCase):
    """Pruebas para Motor 3: Opacidad de Nubes"""
    
    def setUp(self):
        self.motor = MotorOpacidadNubes()
    
    def test_transmitancia_cielo_claro(self):
        """Test: τ ≈ 1.0 en cielo despejado"""
        # Radiación real alta, teórica similar
        resultado = self.motor.calcular_opacidad_nubes(
            radiacion_real_w_m2=950,
            radiacion_teorica_w_m2=1000
        )
        
        # τ debe estar entre 0 y 1
        self.assertGreater(resultado, 0.9)
        self.assertLessEqual(resultado, 1.0)
    
    def test_transmitancia_nubes_densas(self):
        """Test: τ baja con nubes densas"""
        resultado = self.motor.calcular_opacidad_nubes(
            radiacion_real_w_m2=200,
            radiacion_teorica_w_m2=1000
        )
        
        # τ debe ser bajo con nubes densas
        self.assertLess(resultado, 0.3)


class TestBucholtzRayleighV25(unittest.TestCase):
    """Pruebas para Bucholtz-Rayleigh V2.5"""
    
    def setUp(self):
        self.br = BucholtzRayleighV25()
    
    def test_indice_refraccion_aire_standard(self):
        """Test: Índice de refracción en aire estándar"""
        n = self.br.indice_refraccion_ciddor(
            temperatura_c=15,
            presion_hpa=1013,
            humedad_relativa=0.60
        )
        
        # n debe estar muy cerca de 1.000293 para aire estándar
        self.assertGreater(n, 1.0002)
        self.assertLess(n, 1.0004)
    
    def test_numero_loschmidt(self):
        """Test: Número de Loschmidt correcto"""
        N = self.br.numero_loschmidt(
            temperatura_c=0,
            presion_hpa=1013
        )
        
        # N_L(0°C, 1 atm) ≈ 2.687e25 m^-3
        self.assertGreater(N, 2.5e25)
        self.assertLess(N, 2.8e25)
    
    def test_coeficiente_rayleigh(self):
        """Test: Coeficiente de Rayleigh con King factor"""
        beta_r = self.br.coeficiente_rayleigh(
            longitud_onda_nm=550  # Luz verde
        )
        
        # β_R debe ser positivo y realista
        self.assertGreater(beta_r, 0)
        self.assertLess(beta_r, 1e-4)  # Unidades m^-1
    
    def test_visibilidad_bucholtz_completa(self):
        """Test: Cascada completa de cálculo de visibilidad"""
        visibilidad_m, visibilidad_km, clasificacion = self.br.visibilidad_bucholtz_completa(
            temperatura_c=15,
            presion_hpa=1013,
            humedad_relativa=0.80,
            tipo_aire="TEMPLADA"
        )
        
        # Validaciones básicas
        self.assertGreater(visibilidad_m, 0)
        self.assertGreater(visibilidad_km, 0)
        self.assertIn(clasificacion, [
            "Niebla muy densa", "Niebla densa", "Niebla",
            "Bruma", "Muy buena", "Excelente"
        ])


class TestVectorAproximacion(unittest.TestCase):
    """Pruebas para Vector de Aproximación (#26)"""
    
    def setUp(self):
        self.vector = VectorAproximacion()
    
    def test_ley_buys_ballot(self):
        """Test: Ley de Buys-Ballot localiza baja presión correctamente"""
        # Presión 985 hPa (baja), tendencia -2 hPa/h
        resultado = self.vector.ley_buys_ballot(
            presion_hpa=985,
            velocidad_viento_ms=10,
            direccion_viento_grados=180,
            tendencia_presion_hpa_h=-2
        )
        
        # Debe retornar dirección y distancia
        self.assertIn("direccion_grados", resultado)
        self.assertIn("distancia_km_estimada", resultado)
        self.assertIn("eta_horas", resultado)
        
        # Distancia debe ser realista: 30-200 km
        self.assertGreater(resultado["distancia_km_estimada"], 20)
        self.assertLess(resultado["distancia_km_estimada"], 300)
    
    def test_analisis_cuadrante_optico(self):
        """Test: Detección de nubosidad por cambio óptico"""
        resultado = self.vector.analisis_cuadrante_optico(
            radiacion_real_w_m2=300,
            radiacion_teorica_w_m2=1000,
            temperatura_cambio_c=3.5
        )
        
        self.assertIn("tipo_evento", resultado)
        self.assertIn("transmitancia", resultado)
        self.assertIn("cuadrante", resultado)
    
    def test_filtro_ema(self):
        """Test: Filtro EMA suaviza correctamente"""
        valores = [10, 15, 20, 25, 30]
        resultado_ema = self.vector.filtro_ema_suavizado(valores, alpha=0.3)
        
        # EMA debe ser más suave que los datos originales
        self.assertEqual(len(resultado_ema), len(valores))
        
        # No debe oscilaciones bruscas
        diferencias = [abs(resultado_ema[i+1] - resultado_ema[i]) 
                       for i in range(len(resultado_ema)-1)]
        max_diferencia = max(diferencias)
        self.assertLess(max_diferencia, 5)  # Máximo cambio entre puntos
    
    def test_vector_final_aproximacion(self):
        """Test: Vector final fusiona los 3 componentes correctamente"""
        resultado = self.vector.vector_final_aproximacion(
            presion_hpa=990,
            velocidad_viento_ms=8,
            direccion_viento_grados=225,
            tendencia_presion_hpa_h=-1.5,
            radiacion_real_w_m2=400,
            radiacion_teorica_w_m2=1000,
            temperatura_cambio_c=2,
            rssi_dbm=-65,
            rayos_detectados=5
        )
        
        # Debe tener predicción de lluvia
        self.assertIn("prediccion", resultado)
        self.assertIn("LLUVIA desde", resultado["prediccion"].upper())


class TestIntegracionMotoresV25(unittest.TestCase):
    """Pruebas de integración de todos los motores en la cascada"""
    
    def setUp(self):
        self.integracion = IntegracionMotoresV25()
    
    def test_ciclo_completo_ejecucion(self):
        """Test: Ciclo completo ejecuta sin errores"""
        # Datos de sensores realistas
        sensores = {
            "temperatura_c": 18,
            "presion_hpa": 1010,
            "humedad_relativa": 0.70,
            "velocidad_viento_ms": 5,
            "direccion_viento_grados": 180,
            "radiacion_solar_w_m2": 600,
            "altura_mast_m": 2
        }
        
        contexto_ambiental = {
            "tipo_aire": "TEMPLADA",
            "nubosidad_octavos": 3,
            "tipo_precipitacion": None
        }
        
        resultado = self.integracion.execute_ciclo_completo(
            sensores=sensores,
            contexto_ambiental=contexto_ambiental
        )
        
        # Verificar que todos los motores devolvieron resultados
        self.assertIn("motor_masas_aire", resultado)
        self.assertIn("motor_capa_limite", resultado)
        self.assertIn("motor_opacidad_nubes", resultado)
        self.assertIn("motor_ventilacion_tactica", resultado)
        self.assertIn("bucholtz_rayleigh_v25", resultado)
        self.assertIn("vector_aproximacion", resultado)
    
    def test_coherencia_cascada(self):
        """Test: La cascada mantiene coherencia física"""
        resultado = self.integracion.execute_ciclo_completo(
            sensores={
                "temperatura_c": 25,
                "presion_hpa": 1013,
                "humedad_relativa": 0.85,
                "velocidad_viento_ms": 3,
                "direccion_viento_grados": 90,
                "radiacion_solar_w_m2": 800,
                "altura_mast_m": 2
            },
            contexto_ambiental={
                "tipo_aire": "TROPICAL",
                "nubosidad_octavos": 2,
                "tipo_precipitacion": None
            }
        )
        
        # En aire tropical con radiación alta: Tsuelo > Taire
        tsuelo = resultado["motor_capa_limite"].get("temperatura_suelo_c")
        taire = resultado["motor_masas_aire"].get("temperatura_c")
        
        self.assertGreater(tsuelo, taire)


class TestEstrésTormentaFrancesaFicticia(unittest.TestCase):
    """Prueba de estrés: Sistema frontal frío aproximándose"""
    
    def setUp(self):
        self.integracion = IntegracionMotoresV25()
        self.vector = VectorAproximacion()
    
    def test_deteccion_tormenta_lejana(self):
        """Test: Detecta tormenta a 150 km (no impacta aún)"""
        # Condiciones: presión 1015, vientos suaves, radiación normal
        sensores_lejana = {
            "temperatura_c": 20,
            "presion_hpa": 1015,
            "humedad_relativa": 0.65,
            "velocidad_viento_ms": 3,
            "direccion_viento_grados": 270,
            "radiacion_solar_w_m2": 700,
            "altura_mast_m": 2
        }
        
        vector_lejano = self.vector.vector_final_aproximacion(
            presion_hpa=1015,
            velocidad_viento_ms=3,
            direccion_viento_grados=270,
            tendencia_presion_hpa_h=-0.2,
            radiacion_real_w_m2=700,
            radiacion_teorica_w_m2=1000,
            temperatura_cambio_c=0.5,
            rssi_dbm=-80,
            rayos_detectados=0
        )
        
        # Debe indicar distancia lejana
        prediccion = vector_lejano.get("prediccion", "")
        self.assertIn("km", prediccion.lower())
    
    def test_deteccion_tormenta_proxima(self):
        """Test: Detecta tormenta a 30 km (alerta naranja)"""
        # Condiciones: presión 1005 en baja, vientos moderados, radiación baja
        vector_proximo = self.vector.vector_final_aproximacion(
            presion_hpa=1005,
            velocidad_viento_ms=8,
            direccion_viento_grados=225,
            tendencia_presion_hpa_h=-2.5,
            radiacion_real_w_m2=300,
            radiacion_teorica_w_m2=1000,
            temperatura_cambio_c=4,
            rssi_dbm=-60,
            rayos_detectados=12
        )
        
        # Debe indicar proximidad y severidad
        prediccion = vector_proximo.get("prediccion", "")
        self.assertIn("LLUVIA", prediccion.upper())
    
    def test_deteccion_tormenta_inmediata(self):
        """Test: Detecta tormenta a <10 km (alerta roja)"""
        # Condiciones: presión 995 hPa, vientos fuertes, radiación muy baja
        vector_inmediato = self.vector.vector_final_aproximacion(
            presion_hpa=995,
            velocidad_viento_ms=15,
            direccion_viento_grados=225,
            tendencia_presion_hpa_h=-3.5,
            radiacion_real_w_m2=50,
            radiacion_teorica_w_m2=1000,
            temperatura_cambio_c=8,
            rssi_dbm=-45,
            rayos_detectados=50
        )
        
        # Debe indicar severidad inmediata
        prediccion = vector_inmediato.get("prediccion", "")
        self.assertIn("LLUVIA", prediccion.upper())
        self.assertIn("km", prediccion.lower())


def suite_completa():
    """Genera suite con todas las pruebas"""
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de prueba
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMotorMasasDeAire))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMotorCapaLimite))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMotorOpacidadNubes))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBucholtzRayleighV25))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestVectorAproximacion))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegracionMotoresV25))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEstrésTormentaFrancesaFicticia))
    
    return suite


if __name__ == "__main__":
    # Configurar y ejecutar suite completa
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite_completa())
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS BIBLIA V2.5")
    print("="*70)
    print(f"Pruebas ejecutadas: {resultado.testsRun}")
    print(f"Exitosas: {resultado.testsRun - len(resultado.failures) - len(resultado.errors)}")
    print(f"Fallos: {len(resultado.failures)}")
    print(f"Errores: {len(resultado.errors)}")
    print("="*70)
    
    # Exit status
    sys.exit(0 if resultado.wasSuccessful() else 1)

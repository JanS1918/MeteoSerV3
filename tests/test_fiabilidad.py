# Tests unitarios para el sistema de fiabilidad
import unittest
from core.fiabilidad_manager import FiabilidadManager
from core.data_model import Fiabilidad

class TestFiabilidadManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = FiabilidadManager()
    
    def test_registrar_sensor(self):
        """Test: registrar un nuevo sensor"""
        self.manager.registrar_sensor('temp_test', 'sensor', Fiabilidad.ALTA)
        self.assertIn('temp_test', self.manager.estado_sensores)
        self.assertEqual(self.manager.estado_sensores['temp_test']['fiabilidad'], 'alta')
    
    def test_actualizar_lectura_exitosa(self):
        """Test: actualizar lectura exitosa mejora fiabilidad"""
        self.manager.registrar_sensor('temp_test', 'sensor', Fiabilidad.MEDIA)
        
        for _ in range(60):
            self.manager.actualizar_lectura('temp_test', True, 21.5)
        
        self.assertEqual(self.manager.obtener_fiabilidad('temp_test'), 'alta')
        self.assertEqual(len(self.manager.obtener_alertas_activas()), 0)
    
    def test_actualizar_lectura_fallida(self):
        """Test: lecturas fallidas generan alertas"""
        self.manager.registrar_sensor('temp_test', 'sensor', Fiabilidad.ALTA)
        
        for _ in range(5):
            self.manager.actualizar_lectura('temp_test', False, error='Timeout')
        
        self.assertEqual(self.manager.obtener_fiabilidad('temp_test'), 'baja')
        self.assertGreater(len(self.manager.obtener_alertas_activas()), 0)
    
    def test_cerrar_alerta_manual(self):
        """Test: cerrar alerta manualmente"""
        self.manager.registrar_sensor('temp_test', 'sensor')
        self.manager.actualizar_lectura('temp_test', False, error='Error')
        
        self.assertEqual(len(self.manager.obtener_alertas_activas()), 1)
        
        exito = self.manager.cerrar_alerta_manual('temp_test')
        self.assertTrue(exito)
        self.assertEqual(len(self.manager.obtener_alertas_activas()), 0)
    
    def test_estado_completo(self):
        """Test: obtener estado completo del sistema"""
        self.manager.registrar_sensor('temp1', 'sensor')
        self.manager.registrar_sensor('temp2', 'sensor')
        self.manager.actualizar_lectura('temp2', False, error='Error')
        
        estado = self.manager.obtener_estado_completo()
        
        self.assertEqual(estado['total_sensores'], 2)
        self.assertEqual(estado['total_alertas'], 1)
        self.assertIn('temp1', estado['sensores'])
        self.assertIn('temp2', estado['sensores'])

if __name__ == '__main__':
    unittest.main()

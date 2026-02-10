# Tests unitarios para el sistema de auditoría
import unittest
import os
from pathlib import Path
from core.auditoria_manager import AuditoriaManager

class TestAuditoriaManager(unittest.TestCase):
    
    def setUp(self):
        self.test_path = "data/test_auditoria.jsonl"
        if Path(self.test_path).exists():
            os.remove(self.test_path)
        self.manager = AuditoriaManager(log_path=self.test_path)
    
    def tearDown(self):
        if Path(self.test_path).exists():
            os.remove(self.test_path)
    
    def test_registrar_movimiento(self):
        """Test: registrar movimiento de valor"""
        self.manager.registrar_movimiento(
            valor='temp_exterior',
            origen='cajon_temp',
            destino='cajon_meteo',
            usuario='test_user'
        )
        
        historial = self.manager.obtener_historial(tipo='movimiento')
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0]['tipo'], 'movimiento')
        self.assertEqual(historial[0]['entidad'], 'temp_exterior')
    
    def test_registrar_edicion(self):
        """Test: registrar edición de nombre"""
        self.manager.registrar_edicion(
            entidad='cajon_temp',
            campo='nombre',
            valor_anterior='Temperatura',
            valor_nuevo='Temperatura & Clima',
            usuario='test_user'
        )
        
        historial = self.manager.obtener_historial(tipo='edicion')
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0]['cambio']['campo'], 'nombre')
    
    def test_restaurar_movimientos(self):
        """Test: restaurar movimientos realizados"""
        # Registrar varios movimientos
        movimientos = [
            ('valor1', 'origen1', 'destino1'),
            ('valor2', 'origen2', 'destino2'),
            ('valor3', 'origen3', 'destino3'),
        ]
        
        for valor, origen, destino in movimientos:
            self.manager.registrar_movimiento(valor, origen, destino)
        
        # Restaurar los últimos 2 movimientos
        acciones = self.manager.restaurar_movimientos(2)
        
        self.assertEqual(len(acciones), 2)
        # Verificar que se invirtieron
        self.assertEqual(acciones[0]['origen'], 'destino3')
        self.assertEqual(acciones[0]['destino'], 'origen3')
    
    def test_filtrar_historial(self):
        """Test: filtrar historial por tipo y entidad"""
        self.manager.registrar_movimiento('valor1', 'a', 'b')
        self.manager.registrar_movimiento('valor2', 'c', 'd')
        self.manager.registrar_edicion('valor1', 'nombre', 'old', 'new')
        
        # Filtrar por tipo
        movimientos = self.manager.obtener_historial(tipo='movimiento')
        self.assertEqual(len(movimientos), 2)
        
        # Filtrar por entidad
        valor1_cambios = self.manager.obtener_historial(entidad='valor1')
        self.assertEqual(len(valor1_cambios), 2)
    
    def test_estadisticas(self):
        """Test: obtener estadísticas de auditoría"""
        self.manager.registrar_movimiento('v1', 'a', 'b')
        self.manager.registrar_movimiento('v2', 'c', 'd')
        self.manager.registrar_edicion('v1', 'nombre', 'old', 'new')
        self.manager.registrar_feedback_log('indice1', {'correcto': True})
        
        stats = self.manager.obtener_estadisticas()
        
        self.assertEqual(stats['total_cambios'], 4)
        self.assertEqual(stats['por_tipo']['movimiento'], 2)
        self.assertEqual(stats['por_tipo']['edicion'], 1)
        self.assertEqual(stats['por_tipo']['feedback'], 1)

if __name__ == '__main__':
    unittest.main()

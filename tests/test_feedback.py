# Tests unitarios para el sistema de feedback
import unittest
import os
from pathlib import Path
from core.feedback_manager import FeedbackManager

class TestFeedbackManager(unittest.TestCase):
    
    def setUp(self):
        self.test_path = "data/test_feedback.jsonl"
        if Path(self.test_path).exists():
            os.remove(self.test_path)
        self.manager = FeedbackManager(historial_path=self.test_path)
    
    def tearDown(self):
        if Path(self.test_path).exists():
            os.remove(self.test_path)
    
    def test_registrar_feedback_correcto(self):
        """Test: registrar feedback correcto aumenta confianza"""
        registro = self.manager.registrar_feedback(
            nombre_indice='temp_max',
            valor_predicho=25.0,
            valor_real=25.5,
            es_correcto=True
        )
        
        self.assertIsNotNone(registro)
        self.assertGreater(registro['confianza_nueva'], registro['confianza_anterior'])
        self.assertLess(registro['error'], 1.0)
    
    def test_registrar_feedback_incorrecto(self):
        """Test: registrar feedback incorrecto disminuye confianza"""
        registro = self.manager.registrar_feedback(
            nombre_indice='temp_max',
            valor_predicho=25.0,
            valor_real=20.0,
            es_correcto=False,
            comentario='Predicción muy alta'
        )
        
        self.assertIsNotNone(registro)
        self.assertLess(registro['confianza_nueva'], registro['confianza_anterior'])
        self.assertGreater(registro['error'], 1.0)
    
    def test_obtener_confianza(self):
        """Test: obtener factor de confianza"""
        self.manager.registrar_feedback('temp_max', 25.0, 25.5, True)
        confianza = self.manager.obtener_confianza('temp_max')
        
        self.assertIsInstance(confianza, float)
        self.assertGreater(confianza, 0.0)
        self.assertLessEqual(confianza, 1.0)
    
    def test_estadisticas(self):
        """Test: obtener estadísticas de feedback"""
        for i in range(10):
            es_correcto = i < 7  # 70% correcto
            self.manager.registrar_feedback(
                'temp_max', 
                25.0 + i, 
                25.0 + i + (0.5 if es_correcto else 5.0), 
                es_correcto
            )
        
        stats = self.manager.obtener_estadisticas('temp_max')
        
        self.assertEqual(stats['total'], 10)
        self.assertEqual(stats['correctos'], 7)
        self.assertEqual(stats['incorrectos'], 3)
        self.assertEqual(stats['precision'], 0.7)
    
    def test_feedback_reciente(self):
        """Test: obtener feedback reciente"""
        for i in range(25):
            self.manager.registrar_feedback(
                f'indice_{i}', 
                float(i), 
                float(i + 0.5), 
                True
            )
        
        reciente = self.manager.obtener_feedback_reciente(limite=10)
        
        self.assertEqual(len(reciente), 10)
        # El más reciente debe ser el último registrado
        self.assertEqual(reciente[-1]['nombre_indice'], 'indice_24')

if __name__ == '__main__':
    unittest.main()

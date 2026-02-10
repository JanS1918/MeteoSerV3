"""
conftest.py - Configuración de pytest para MeteoSer

Implementa hook pytest_pyfunc_call para ejecutar tests async
sin necesidad del plugin pytest-asyncio
"""

import asyncio
import inspect
import pytest
import sys


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """
    Hook que permite ejecutar funciones async como tests sin pytest-asyncio.
    
    Si la función de test es una corrutina, crea un event loop
    y ejecuta la corrutina de forma síncrona.
    """
    # Obtener la función de test
    testfunction = pyfuncitem.obj
    
    # Verificar si es una función async (usar inspect en lugar de asyncio)
    if inspect.iscoroutinefunction(testfunction):
        # Obtener los fixtures necesarios
        funcargs = pyfuncitem.funcargs
        
        # Crear un event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Ejecutar la corrutina
            loop.run_until_complete(testfunction(**funcargs))
        except Exception as e:
            raise
        finally:
            loop.close()
        
        # Retornar True para indicar que pytest ha manejado el test
        return True
    
    # Retornar None para que pytest maneje el test normalmente
    return None


@pytest.fixture
def event_loop():
    """
    Fixture que proporciona un event loop para tests async.
    Reemplaza la del plugin pytest-asyncio.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_bus():
    """
    Mock del Bus para tests que necesitan el evento del Bus.
    """
    class MockBus:
        def __init__(self):
            self.published_events = []
            self.subscribers = {}
        
        def publicar(self, topic: str, value, event_type: str = "data"):
            """Simula publicación en el Bus"""
            self.published_events.append({
                "topic": topic,
                "value": value,
                "event_type": event_type
            })
        
        def suscribir(self, topic: str, callback):
            """Simula suscripción al Bus"""
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)
        
        def get_published_count(self, topic: str = None):
            """Retorna cantidad de eventos publicados"""
            if topic:
                return sum(1 for e in self.published_events if e["topic"] == topic)
            return len(self.published_events)
        
        def clear(self):
            """Limpia el historial de eventos"""
            self.published_events.clear()
            self.subscribers.clear()
    
    return MockBus()

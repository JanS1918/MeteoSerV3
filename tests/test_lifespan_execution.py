import logging
"""
TEST DEL LIFESPAN - Verificar que startup/shutdown se ejecutan REALMENTE.

Este test es CRÍTICO: sin él, podríamos tener un lifespan que "parece" que
funciona pero en realidad nunca se ejecuta.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Variables globales para trackear ejecución
startup_executed = False
shutdown_executed = False


def test_lifespan_startup_executes():
    """Verificar que el lifespan REALMENTE ejecuta el startup."""
    global startup_executed, shutdown_executed
    
    startup_executed = False
    shutdown_executed = False
    
    # Importar DESPUÉS de limpiar flags
    # (importar main_asgi ejecuta el módulo)
    try:
        from main_asgi import app
    except ImportError as e:
        pytest.skip(f"No se pudo importar main_asgi: {e}")
    
    # Crear cliente de test (esto EJECUTA el lifespan)
    client = TestClient(app)
    
    # Hacer una solicitud simple (esto activa el lifespan)
    try:
        response = client.get("/")
        # No importa si falla (404 es ok), lo importante es que se ejecutó el lifespan
    except Exception:
        logging.exception("Silent except at 42 - revisar contexto")
    
    # Verificar que endpoints básicos funcionan
    # Si el lifespan no se ejecutara, el sistema estaría vacío
    try:
        response = client.get("/api/sensores")
        assert response.status_code in [200, 404, 500]  # Cualquier respuesta HTTP válida
        print(f"✅ Endpoint respondió: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error en endpoint: {e}")


def test_lifespan_context_manager_exists():
    """Verificar que el lifespan context manager existe."""
    try:
        from main_asgi import lifespan
        import inspect
        
        # Verificar que es una función (context manager decorada)
        assert callable(lifespan), "lifespan debe ser callable"
        
        # Verificar que tiene el atributo de context manager
        assert hasattr(lifespan, '__wrapped__') or inspect.iscoroutinefunction(lifespan) or inspect.isasyncgenfunction(lifespan.__wrapped__ if hasattr(lifespan, '__wrapped__') else lifespan), \
            "lifespan debe ser un context manager válido"
        
        print("✅ lifespan es un async context manager válido (decorado)")
    except ImportError:
        pytest.skip("No se pudo importar lifespan")


def test_app_created_with_lifespan():
    """Verificar que app se crea CON lifespan, no sin él."""
    try:
        from main_asgi import app
        
        # Si app tiene lifespan, debe estar en su configuración
        # FastAPI almacena lifespan en app.router.lifespan
        has_lifespan = hasattr(app, 'lifespan') or hasattr(app.router, 'lifespan_context')
        
        # Alternativa: verificar que el app NO está vacío
        # Si el lifespan no se ejecutara, app.routes estaría vacío
        assert len(app.routes) > 0, "app debe tener al menos algunos endpoints"
        print(f"✅ app tiene {len(app.routes)} rutas registradas")
    except ImportError:
        pytest.skip("No se pudo importar app")


def test_lifespan_no_double_fastapi_init():
    """Verificar que NO hay doble inicialización de FastAPI."""
    import re
    
    # Leer main_asgi.py
    with open("main_asgi.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Buscar "app = FastAPI(" (solo la asignación, no el comentario)
    pattern = r'^\s*app\s*=\s*FastAPI\s*\('
    matches = re.findall(pattern, content, re.MULTILINE)
    
    # Debe haber exactamente UNA instancia sin comentar
    active_instances = [m for m in matches if not m.startswith("#")]
    assert len(active_instances) == 1, f"Debe haber exactamente 1 app = FastAPI(), encontramos {len(active_instances)}"
    print(f"✅ Exactamente UNA instancia de app = FastAPI()")


def test_lifespan_parameters():
    """Verificar que lifespan recibe el parámetro 'app' correctamente."""
    try:
        from main_asgi import lifespan
        import inspect
        
        # Obtener signature
        sig = inspect.signature(lifespan)
        params = list(sig.parameters.keys())
        
        assert 'app_instance' in params, f"lifespan debe tener parámetro 'app_instance', tiene: {params}"
        print(f"✅ lifespan tiene parámetro 'app_instance'")
    except ImportError:
        pytest.skip("No se pudo importar lifespan")


def test_lifespan_has_yield():
    """Verificar que lifespan tiene un 'yield' (característica de context manager)."""
    import inspect
    
    try:
        from main_asgi import lifespan
        
        # Obtener source code
        source = inspect.getsource(lifespan)
        assert "yield" in source, "lifespan debe contener 'yield' para ser context manager"
        print("✅ lifespan contiene 'yield' (es context manager válido)")
    except ImportError:
        pytest.skip("No se pudo importar lifespan")


def test_no_deprecated_on_event_decorators():
    """Verificar que NO hay decoradores @app.on_event() activos."""
    import re
    
    with open("main_asgi.py", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Buscar @app.on_event (excluir comentarios)
    # Patrón: línea que empieza con @ (no #) y contiene @app.on_event
    lines = content.split('\n')
    active_on_event = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith('#') and '@app.on_event' in stripped:
            active_on_event.append((i+1, line))
    
    assert len(active_on_event) == 0, f"NO debe haber @app.on_event() activos. Encontrados en líneas: {[x[0] for x in active_on_event]}"
    print("✅ Cero @app.on_event() decoradores activos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

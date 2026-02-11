# test_boot.py
# Test mínimo para verificar que MeteoSer arranca sin errores.


def test_boot():
    import main_asgi
    assert hasattr(main_asgi, "app")


# Ejecutar directamente si se llama como script
if __name__ == "__main__":
    test_boot()

#!/usr/bin/env python3
"""Inyectar integrador always-on en main_asgi.py"""

import re

with open('main_asgi.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar el patrón exacto después de auditoría
pattern = r'(    except Exception as e:\n        logger\.warning\(f"⚠️ No se pudo ejecutar auditoría: \{e\}"\))'

replacement = r'''\1
    
    # 🔄 INTEGRADOR ALWAYS-ON: Recuperación automática de datos del gap histórico
    try:
        from core.integration.integrador_always_on import ejecutar_integrador_automatico
        resultado_integrador = await ejecutar_integrador_automatico()
        logger.info(f"🔄 Integrador Always-On: {resultado_integrador.get('status', 'completado')}")
        if resultado_integrador.get('status') == 'exito':
            logger.info(f"   ✅ {resultado_integrador.get('eventos_procesados', 0)} eventos recuperados e integrados")
    except Exception as e:
        logger.warning(f"⚠️ Integrador Always-On no disponible: {e}")'''

if re.search(pattern, content):
    new_content = re.sub(pattern, replacement, content)
    with open('main_asgi.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('✅ Integrador inyectado correctamente en main_asgi.py')
    print(f'   Ubicación: después del bloque de auditoría, antes de Omnipotencia')
else:
    print('❌ Patrón no encontrado - el archivo puede tener cambios')
    # Intentar patrón alternativo sin emoji
    pattern2 = r'(    except Exception as e:\n        logger\.warning\(f".*No se pudo ejecutar auditoría.*"\))'
    if re.search(pattern2, content):
        print('   ⚠️ Encontré patrón similar sin emoji exacto - usando alternativa...')
        new_content = re.sub(pattern2, replacement, content)
        with open('main_asgi.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('   ✅ Inyectado usando patrón alternativo')

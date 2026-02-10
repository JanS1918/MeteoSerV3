import json

# Leer archivo con encoding UTF-8
with open('INDICE_RAPIDO_BUSQUEDAS_REFERENCIAS_20260205.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Remover markdown fences
content = content.replace('```json', '')
content = content.replace('```', '')
content = content.replace('````', '')

# Validar que es JSON válido
data = json.loads(content)

# Escribir de vuelta formateado
with open('INDICE_RAPIDO_BUSQUEDAS_REFERENCIAS_20260205.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('✓ JSON limpio y validado')

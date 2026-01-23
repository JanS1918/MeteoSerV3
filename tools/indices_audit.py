"""Genera un informe de auditoría de índices definidos en `core/indices/environmental_indices.py`.

Produce `data/indices_audit.md` con una lista de funciones `indice_` encontradas
y sugerencias automáticas básicas.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'core' / 'indices' / 'environmental_indices.py'
OUT = ROOT / 'data' / 'indices_audit.md'


def analyze() -> None:
    src = SRC.read_text(encoding='utf-8')
    mod = ast.parse(src)
    funcs = [n for n in mod.body if isinstance(n, ast.FunctionDef)]
    indice_funcs = [f for f in funcs if f.name.startswith('indice_')]

    lines = []
    lines.append('# Índices auditados')
    lines.append('Fecha: auto-generado')
    lines.append('')
    for f in indice_funcs:
        name = f.name
        sig = ', '.join([a.arg for a in f.args.args])
        doc = ast.get_docstring(f) or ''
        lines.append(f'## {name}')
        lines.append(f'- Firma: ({sig})')
        if doc:
            lines.append(f'- Doc: {doc.splitlines()[0]}')
        else:
            lines.append('- Doc: (sin docstring)')
        # Sugerencias heurísticas
        sugg = []
        if 'pmv' in name or 'ppd' in name:
            sugg.append('Usar `pythermalcomfort` para PMV/PPD si está disponible.')
        if 'wbgt' in name or 'bulbo' in name:
            sugg.append('Considerar `pythermalcomfort` para WBGT/globo.')
        if 'evapotranspiracion' in name or 'penman' in name:
            sugg.append('Penman-Monteith completo ya disponible; verificar parámetros (presión, altura).')
        if 'radiacion' in name or 'solar' in name:
            sugg.append('Comparar con modelos teóricos (`pvlib`, `pysolar`) para radiación directa/difusa.')
        if not sugg:
            sugg.append('Revisar precisión; considerar librerías científicas o validación con datos.')
        for s in sugg:
            lines.append(f'- Sugerencia: {s}')
        lines.append('')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    analyze()
    print('Audit generated at', OUT)

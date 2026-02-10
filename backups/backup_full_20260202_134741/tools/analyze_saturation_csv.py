"""
Analiza `data/saturation_comparison_20260131.csv` y muestra estadísticas básicas.
"""
import math
import csv

path = "data/saturation_comparison_20260131.csv"
rows = []
with open(path, newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for r in reader:
        rows.append({k: float(v) for k, v in r.items()})

# compute stats
import statistics

pct_v = [r['pct_diff_virial'] for r in rows if not math.isnan(r['pct_diff_virial'])]
pct_m = [r['pct_diff_magnus'] for r in rows if not math.isnan(r['pct_diff_magnus'])]

print(f"Rows: {len(rows)}")
print(f"Virial vs Hyland: mean={statistics.mean(pct_v):.4f}%, max={max(pct_v):.4f}%, min={min(pct_v):.4f}%")
print(f"Magnus vs Hyland: mean={statistics.mean(pct_m):.4f}%, max={max(pct_m):.4f}%, min={min(pct_m):.4f}%")

# Show top 5 absolute differences for magnus and virial
rows_sorted_v = sorted(rows, key=lambda r: abs(r['pct_diff_virial']), reverse=True)
rows_sorted_m = sorted(rows, key=lambda r: abs(r['pct_diff_magnus']), reverse=True)

print('\nTop 5 Virial diffs (T, pct, hyland, virial):')
for r in rows_sorted_v[:5]:
    print(r['T_C'], f"{r['pct_diff_virial']:.4f}%", f"{r['hyland_Pa']:.3f}", f"{r['virial_greenspan_Pa']:.3f}")

print('\nTop 5 Magnus diffs (T, pct, hyland, magnus):')
for r in rows_sorted_m[:5]:
    print(r['T_C'], f"{r['pct_diff_magnus']:.4f}%", f"{r['hyland_Pa']:.3f}", f"{r['magnus_Pa']:.3f}")

# Diagrama conceptual MeteoSer – Techo absoluto

## Sensores físicos y virtuales (visión general)

```
                   ┌──────────────────────┐
                   │      HP2550A         │
                   │  (hub central)       │
                   │  T, HR, P, Radiación │
                   └─────────┬───────────┘
                             │ centraliza datos de todos sensores
                             │
   ┌─────────────────────────┴─────────────────────────┐
   │                                                   │
┌───────────┐                                     ┌───────────┐
│  WH65     │                                     │  WH31     │
│ exterior  │                                     │ exterior  │
│ T, HR,    │                                     │ T, HR     │
│ viento    │                                     │ gradiente │
└─────┬─────┘                                     └─────┬─────┘
      │                                                 │
      │                                                 │
      │                                                 │
      │                 ┌───────────────────────────────┴─────────────────────────────┐
      │                 │          QC multifuente: deltas, coherencia térmica          │
      │                 │     (WH65 vs WH31, WH57, WH51, HP2550A, etc.)               │
      │                 └───────────────────────────────┬─────────────────────────────┘
      │                                                 │
      │                                                 │
      │                     ┌───────────────────────────┴─────────────────────────┐
      │                     │       Sensores virtuales / índices derivados        │
      │                     ├────────────────────────────┬────────────────────────┤
      │                     │ Fórmula / Método          │ Entradas               │
      │                     ├────────────────────────────┼────────────────────────┤
      │                     │ UV virtual (uv_spectral_diamond) │ REST2, SPA, P, T, HR, nubosidad implícita │
      │                     │ Nubosidad implícita (Kasten-Czeplak) │ REST2 medida / teórica │
      │                     │ Radiación LW neta (Prata) │ REST2, T superficie, nubosidad │
      │                     │ Tmrt refinado             │ Radiación directa+difusa, LW neta, viento │
      │                     │ Estabilidad nocturna (Monin-Obukhov) │ WH31 exterior, gradientes, viento │
      │                     │ Índice enfriamiento radiativo │ Qnet = REST2 + LW neta │
      │                     │ Gradientes nocturnos ΔT    │ WH31 exterior - HP2550A │
      │                     │ Fiabilidad multivariable   │ Todos sensores + QC + alertas │
      │                     └────────────────────────────┴────────────────────────┘
      │
      │                     ┌───────────────────────────────┐
      │                     │ Selección dinámica sensor     │
      │                     │ Prioridad / fiabilidad / icono│
      │                     │ Según QC, sobrecalentamiento  │
      │                     └─────────────┬─────────────────┘
      │                                   │
      │                                   │
      │                     ┌─────────────┴─────────────┐
      │                     │ Publicación final          │
      │                     │ *_raw + corregidos         │
      │                     │ Índices: Tmin, heladas,    │
      │                     │ Tmrt, UV, LW, confort,     │
      │                     │ alertas multilevel         │
      │                     └────────────────────────────┘
```

## Resumen de flujo (operativo)

1. Recolección de datos brutos
   - HP2550A centraliza todos los sensores: WH65, WH57, WH51, WH31 (exterior).
   - Cada sensor tiene perfil de prioridad y fiabilidad fijo, con icono correspondiente.

2. Control de calidad multifuente
   - Comparación de deltas entre sensores.
   - Flags de anomalía y degradación de fiabilidad.

3. Cálculo de sensores virtuales / índices
   - UV virtual → degradado por nubosidad implícita.
   - Nubosidad implícita → Kasten-Czeplak, fallback en índices si no hay sensor.
   - LW neta → Prata + emisividad, alimenta Tmrt y enfriamiento radiativo.
   - Tmrt refinado → directa+difusa+LW+viento.
   - Estabilidad nocturna → Monin-Obukhov con gradientes nocturnos.
   - Enfriamiento radiativo → Tmin / heladas.
   - Gradientes nocturnos WH31 → corrección nocturna.

4. Fiabilidad multilevel
   - Flag ALTA / MEDIA / BAJA según QC, alertas, estabilidad y sensor principal.
   - Permite selección dinámica del sensor más fiable según situación.

5. Publicación final
   - *_raw + corregidos, índices completos y alertas inteligentes.
   - Adaptable a sensores nuevos automáticamente gracias a metadatos y alias dinámicos.

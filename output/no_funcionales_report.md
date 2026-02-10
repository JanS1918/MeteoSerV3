# Informe: subfactores no funcionales

## actividad_rayos_proxima

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1233):

```
            alerta_rayos = min(100, rayos * 5) if rayos > 0 else 0
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1233):

```
            alerta_rayos = min(100, rayos * 5) if rayos > 0 else 0
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
            
```



## alerta_calor_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1175):

```
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
            self.bus.publicar("alerta_calor_activa", alerta_calor >= 50, "bool")
            
            # 3. ALERTA FRÍO EXTREMO
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1175):

```
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
            self.bus.publicar("alerta_calor_activa", alerta_calor >= 50, "bool")
            
            # 3. ALERTA FRÍO EXTREMO
```



## alerta_calor_componente_humedad

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1172):

```
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1172):

```
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
```



## alerta_calor_componente_temperatura

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1171):

```
            alerta_calor = min(100, score_temp_calor + score_humedad_calor + score_uv_calor)
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1171):

```
            alerta_calor = min(100, score_temp_calor + score_humedad_calor + score_uv_calor)
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
```



## alerta_calor_componente_uv

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1173):

```
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
            self.bus.publicar("alerta_calor_activa", alerta_calor >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1173):

```
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_uv", score_uv_calor, "0-100")
            self.bus.publicar("umbral_calor_extremo", umbral_calor_extremo, "°C")
            self.bus.publicar("alerta_calor_activa", alerta_calor >= 50, "bool")
```



## alerta_calor_extremo_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1170):

```
            score_uv_calor = min(20, uv * 2)
            alerta_calor = min(100, score_temp_calor + score_humedad_calor + score_uv_calor)
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1170):

```
            score_uv_calor = min(20, uv * 2)
            alerta_calor = min(100, score_temp_calor + score_humedad_calor + score_uv_calor)
            self.bus.publicar("alerta_calor_extremo_score", alerta_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_temperatura", score_temp_calor, "0-100")
            self.bus.publicar("alerta_calor_componente_humedad", score_humedad_calor, "0-100")
```



## alerta_frio_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1186):

```
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
            self.bus.publicar("alerta_frio_activa", alerta_frio >= 50, "bool")
            
            # 4. ALERTA POLVO/PM
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1186):

```
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
            self.bus.publicar("alerta_frio_activa", alerta_frio >= 50, "bool")
            
            # 4. ALERTA POLVO/PM
```



## alerta_frio_componente_temperatura

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1183):

```
            alerta_frio = min(100, score_temp_frio + score_viento_frio)
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1183):

```
            alerta_frio = min(100, score_temp_frio + score_viento_frio)
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
```



## alerta_frio_componente_viento

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1184):

```
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
            self.bus.publicar("alerta_frio_activa", alerta_frio >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1184):

```
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
            self.bus.publicar("umbral_frio_extremo", umbral_frio_extremo, "°C")
            self.bus.publicar("alerta_frio_activa", alerta_frio >= 50, "bool")
```



## alerta_frio_extremo_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1182):

```
            score_viento_frio = viento * 0.5
            alerta_frio = min(100, score_temp_frio + score_viento_frio)
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1182):

```
            score_viento_frio = viento * 0.5
            alerta_frio = min(100, score_temp_frio + score_viento_frio)
            self.bus.publicar("alerta_frio_extremo_score", alerta_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_temperatura", score_temp_frio, "0-100")
            self.bus.publicar("alerta_frio_componente_viento", score_viento_frio, "0-100")
```



## alerta_helada_radiativa_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1227):

```
                alerta_helada_rad = 0.0
            self.bus.publicar("alerta_helada_radiativa_score", alerta_helada_rad, "0-100")
            self.bus.publicar("alerta_helada_radiativa_activa", alerta_helada_rad >= 50, "bool")
            
            # 8. ALERTA DESCARGAS ELÉCTRICAS (simulado)
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1227):

```
                alerta_helada_rad = 0.0
            self.bus.publicar("alerta_helada_radiativa_score", alerta_helada_rad, "0-100")
            self.bus.publicar("alerta_helada_radiativa_activa", alerta_helada_rad >= 50, "bool")
            
            # 8. ALERTA DESCARGAS ELÉCTRICAS (simulado)
```



## alerta_helada_radiativa_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1226):

```
            else:
                alerta_helada_rad = 0.0
            self.bus.publicar("alerta_helada_radiativa_score", alerta_helada_rad, "0-100")
            self.bus.publicar("alerta_helada_radiativa_activa", alerta_helada_rad >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1226):

```
            else:
                alerta_helada_rad = 0.0
            self.bus.publicar("alerta_helada_radiativa_score", alerta_helada_rad, "0-100")
            self.bus.publicar("alerta_helada_radiativa_activa", alerta_helada_rad >= 50, "bool")
            
```



## alerta_niebla_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1208):

```
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
            
            # 6. ALERTA RACHAS PELIGROSAS
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1208):

```
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
            
            # 6. ALERTA RACHAS PELIGROSAS
```



## alerta_niebla_diferencial_td

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1207):

```
            score_niebla = max(0, 100 - (diferencial_td * 20)) if diferencial_td < 5 else 0
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1207):

```
            score_niebla = max(0, 100 - (diferencial_td * 20)) if diferencial_td < 5 else 0
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
            
```



## alerta_niebla_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1206):

```
            diferencial_td = abs(temp_c - td)
            score_niebla = max(0, 100 - (diferencial_td * 20)) if diferencial_td < 5 else 0
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1206):

```
            diferencial_td = abs(temp_c - td)
            score_niebla = max(0, 100 - (diferencial_td * 20)) if diferencial_td < 5 else 0
            self.bus.publicar("alerta_niebla_score", score_niebla, "0-100")
            self.bus.publicar("alerta_niebla_diferencial_td", diferencial_td, "°C")
            self.bus.publicar("alerta_niebla_activa", score_niebla >= 50, "bool")
```



## alerta_polvo_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1199):

```
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
            
            # 5. ALERTA NIEBLA
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1199):

```
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
            
            # 5. ALERTA NIEBLA
```



## alerta_polvo_componente_pm10

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1197):

```
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1197):

```
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
```



## alerta_polvo_componente_pm25

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1196):

```
            alerta_polvo = min(100, score_pm25 + score_pm10 + score_viento_polvo)
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1196):

```
            alerta_polvo = min(100, score_pm25 + score_pm10 + score_viento_polvo)
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
```



## alerta_polvo_componente_viento

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1198):

```
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1198):

```
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
            self.bus.publicar("alerta_polvo_componente_viento", score_viento_polvo, "0-100")
            self.bus.publicar("alerta_polvo_activa", alerta_polvo >= 50, "bool")
            
```



## alerta_polvo_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1195):

```
            score_viento_polvo = (viento - 15) * 2 if viento > 15 else 0
            alerta_polvo = min(100, score_pm25 + score_pm10 + score_viento_polvo)
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1195):

```
            score_viento_polvo = (viento - 15) * 2 if viento > 15 else 0
            alerta_polvo = min(100, score_pm25 + score_pm10 + score_viento_polvo)
            self.bus.publicar("alerta_polvo_score", alerta_polvo, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm25", score_pm25, "0-100")
            self.bus.publicar("alerta_polvo_componente_pm10", score_pm10, "0-100")
```



## alerta_rachas_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1218):

```
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
            
            # 7. ALERTA HELADA RADIATIVA
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1218):

```
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
            
            # 7. ALERTA HELADA RADIATIVA
```



## alerta_rachas_peligrosas_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1215):

```
            score_rachas = (rachas - umbral_rachas) * 1.5 if rachas > umbral_rachas else 0
            alerta_rachas = min(100, score_rachas)
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1215):

```
            score_rachas = (rachas - umbral_rachas) * 1.5 if rachas > umbral_rachas else 0
            alerta_rachas = min(100, score_rachas)
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
```



## alerta_rayos_activa

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1234):

```
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
            
            logger.info(f"[OK] Alertas meteorológicas publicadas (Tormenta:{alerta_tormenta:.0f}, Calor:{alerta_calor:.0f}, Frío:{alerta_frio:.0f}, Polvo:{alerta_polvo:.0f})")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1234):

```
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
            
            logger.info(f"[OK] Alertas meteorológicas publicadas (Tormenta:{alerta_tormenta:.0f}, Calor:{alerta_calor:.0f}, Frío:{alerta_frio:.0f}, Polvo:{alerta_polvo:.0f})")
```



## alerta_rayos_score

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1232):

```
            rayos = self.system.data.get("actividad_rayos", 0.0)
            alerta_rayos = min(100, rayos * 5) if rayos > 0 else 0
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1232):

```
            rayos = self.system.data.get("actividad_rayos", 0.0)
            alerta_rayos = min(100, rayos * 5) if rayos > 0 else 0
            self.bus.publicar("alerta_rayos_score", alerta_rayos, "0-100")
            self.bus.publicar("actividad_rayos_proxima", rayos, "eventos/km2")
            self.bus.publicar("alerta_rayos_activa", alerta_rayos >= 50, "bool")
```



## alerta_tormenta_componente_humedad

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1159):

```
            self.bus.publicar("alerta_tormenta_score", alerta_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1159):

```
            self.bus.publicar("alerta_tormenta_score", alerta_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
```



## alerta_tormenta_componente_presion

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1158):

```
            alerta_tormenta = min(100, score_presion_tormenta + score_humedad_tormenta + score_radiacion_tormenta)
            self.bus.publicar("alerta_tormenta_score", alerta_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1158):

```
            alerta_tormenta = min(100, score_presion_tormenta + score_humedad_tormenta + score_radiacion_tormenta)
            self.bus.publicar("alerta_tormenta_score", alerta_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
```



## alerta_tormenta_componente_radiacion

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1160):

```
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
            self.bus.publicar("alerta_tormenta_activa", alerta_tormenta >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1160):

```
            self.bus.publicar("alerta_tormenta_componente_presion", score_presion_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
            self.bus.publicar("alerta_tormenta_activa", alerta_tormenta >= 50, "bool")
```



## angulo_horario_amanecer

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 835):

```
                
                # Cálculo simplificado si no existe el módulo
                from tools.arco_solar import declinacion_solar, angulo_horario_amanecer
                
                dia_ano = fecha_utc.timetuple().tm_yday
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 835):

```
                
                # Cálculo simplificado si no existe el módulo
                from tools.arco_solar import declinacion_solar, angulo_horario_amanecer
                
                dia_ano = fecha_utc.timetuple().tm_yday
```



## angulo_horario_solar

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 826):

```
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
                self.bus.publicar("angulo_horario_solar", resultado.get("angulo_horario", 0.0), "grados")
                self.bus.publicar("refraccion_atmosferica", resultado.get("refraccion", 0.0), "grados")
                
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 826):

```
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
                self.bus.publicar("angulo_horario_solar", resultado.get("angulo_horario", 0.0), "grados")
                self.bus.publicar("refraccion_atmosferica", resultado.get("refraccion", 0.0), "grados")
                
```



## ascension_recta_solar

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 823):

```
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 823):

```
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
```



## año

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Año actual (valor numérico del año).



## declinacion_solar

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 822):

```
                self.bus.publicar("dia_juliano", resultado.get("jd", 0.0), "días")
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 822):

```
                self.bus.publicar("dia_juliano", resultado.get("jd", 0.0), "días")
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
                self.bus.publicar("oblicuidad_ecliptica", resultado.get("oblicuidad", 23.4), "grados")
```



## declinacion_solar_simple

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 842):

```
                # Subfactores simplificados
                self.bus.publicar("dia_del_ano", dia_ano, "día")
                self.bus.publicar("declinacion_solar_simple", math.degrees(decl_rad), "grados")
                
                # Arco solar
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 842):

```
                # Subfactores simplificados
                self.bus.publicar("dia_del_ano", dia_ano, "día")
                self.bus.publicar("declinacion_solar_simple", math.degrees(decl_rad), "grados")
                
                # Arco solar
```



## delta_t_atomico

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 821):

```
                # SUBFACTORES ASTRONÓMICOS CRÍTICOS:
                self.bus.publicar("dia_juliano", resultado.get("jd", 0.0), "días")
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 821):

```
                # SUBFACTORES ASTRONÓMICOS CRÍTICOS:
                self.bus.publicar("dia_juliano", resultado.get("jd", 0.0), "días")
                self.bus.publicar("delta_t_atomico", resultado.get("delta_t", 0.0), "segundos")
                self.bus.publicar("declinacion_solar", resultado.get("declinacion", 0.0), "grados")
                self.bus.publicar("ascension_recta_solar", resultado.get("ascension_recta", 0.0), "grados")
```



## dias_desde_luna_nueva

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 869):

```
                # Subfactores edad luna
                dias_desde_nueva = fase_lunar["fase"] * 29.53
                self.bus.publicar("dias_desde_luna_nueva", dias_desde_nueva, "días")
                
                logger.debug(f"  → fase_lunar={fase_lunar['nombre_fase']} ({fase_lunar['fase']:.2f})")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 869):

```
                # Subfactores edad luna
                dias_desde_nueva = fase_lunar["fase"] * 29.53
                self.bus.publicar("dias_desde_luna_nueva", dias_desde_nueva, "días")
                
                logger.debug(f"  → fase_lunar={fase_lunar['nombre_fase']} ({fase_lunar['fase']:.2f})")
```



## dias_helada_acumulados_año

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Contador de días con helada acumulados durante el año.



## diferencia_presion_altitud

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py` (línea 3958):

```
            p0 = presion_pa * math.exp(exponent)
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
            
```

- Snippet desde `backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py` (línea 3791):

```
            p0 = presion_pa * math.exp(exponent)
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
            
```



## elevacion_solar_estimada

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\backup_V47_3_20260205_153751\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\backup_V47_2_20260205_151017\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\backup_V47_2_20260205_151000\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 468):

```
                # Elevación solar (placeholder - debería venir de astronomía)
                elevacion_solar = 45.0
                self.bus.publicar("elevacion_solar_estimada", elevacion_solar, "grados")
                
                # Subfactor: seno elevación
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 468):

```
                # Elevación solar (placeholder - debería venir de astronomía)
                elevacion_solar = 45.0
                self.bus.publicar("elevacion_solar_estimada", elevacion_solar, "grados")
                
                # Subfactor: seno elevación
```



## emis ividad_cuerpo_humano

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Probable "emisividad_cuerpo_humano" -> emisividad térmica del cuerpo humano (para cálculos radiativos).



## emis ividad_cuerpo_negro

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Probable "emisividad_cuerpo_negro" -> emisividad del cuerpo negro (constante para calibración radiativa).



## es_año_bisiesto

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Booleano que indica si el año actual es bisiesto.



## exponente_barometrico

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py` (línea 3952):

```
            exponent = (g_gravedad * M_aire_seco * altitud) / (R_universal * T_v)
            
            self.bus.publicar("exponente_barometrico", exponent, "adimensional")
            self.bus.publicar("temperatura_virtual_laplace", T_v, "K")
            
```

- Snippet desde `backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py` (línea 3785):

```
            exponent = (g_gravedad * M_aire_seco * altitud) / (R_universal * T_v)
            
            self.bus.publicar("exponente_barometrico", exponent, "adimensional")
            self.bus.publicar("temperatura_virtual_laplace", T_v, "K")
            
```



## factor_multiplicador_presion

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py` (línea 3959):

```
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
            
            # ═══════════════════════════════════════════════════════════════════
```

- Snippet desde `backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py` (línea 3792):

```
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
            
            # ═══════════════════════════════════════════════════════════════════
```



## k_index

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1484):

```
            
            # 4. K-INDEX (Estabilidad Atmosférica para Tormentas)
            k_index = (temp_c - 273.15) + (humedad * 0.1) - ((15.0 - temp_c) * 0.5) if temp_c > 0 else 0
            k_index = max(0, min(100, k_index))
            self.bus.publicar("k_index", k_index, "0-100")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1484):

```
            
            # 4. K-INDEX (Estabilidad Atmosférica para Tormentas)
            k_index = (temp_c - 273.15) + (humedad * 0.1) - ((15.0 - temp_c) * 0.5) if temp_c > 0 else 0
            k_index = max(0, min(100, k_index))
            self.bus.publicar("k_index", k_index, "0-100")
```



## k_index_categoria

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1488):

```
            self.bus.publicar("k_index", k_index, "0-100")
            k_categoria = "Baja convección" if k_index < 15 else "Riesgo moderado" if k_index < 25 else "Riesgo moderado-alto" if k_index < 30 else "Riesgo alto" if k_index < 35 else "Riesgo muy alto"
            self.bus.publicar("k_index_categoria", k_categoria, "string")
            
            # 5. LIFTED INDEX (Estabilidad Térmica)
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1488):

```
            self.bus.publicar("k_index", k_index, "0-100")
            k_categoria = "Baja convección" if k_index < 15 else "Riesgo moderado" if k_index < 25 else "Riesgo moderado-alto" if k_index < 30 else "Riesgo alto" if k_index < 35 else "Riesgo muy alto"
            self.bus.publicar("k_index_categoria", k_categoria, "string")
            
            # 5. LIFTED INDEX (Estabilidad Térmica)
```



## presion_critica_agua

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 332):

```
            self.bus.publicar("temperatura_kelvin", T_k, "K")
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 332):

```
            self.bus.publicar("temperatura_kelvin", T_k, "K")
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
            
```



## presion_nivel_mar_calculada

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py` (línea 3957):

```
            # Presión nivel mar
            p0 = presion_pa * math.exp(exponent)
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
```

- Snippet desde `backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py` (línea 3790):

```
            # Presión nivel mar
            p0 = presion_pa * math.exp(exponent)
            self.bus.publicar("presion_nivel_mar_calculada", p0 / 100.0, "hPa")
            self.bus.publicar("diferencia_presion_altitud", (p0 - presion_pa) / 100.0, "hPa")
            self.bus.publicar("factor_multiplicador_presion", math.exp(exponent), "adimensional")
```



## refraccion_atmosferica

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 827):

```
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
                self.bus.publicar("angulo_horario_solar", resultado.get("angulo_horario", 0.0), "grados")
                self.bus.publicar("refraccion_atmosferica", resultado.get("refraccion", 0.0), "grados")
                
                logger.debug(f"  → elevacion_solar={resultado['elevacion_solar']:.2f}°, azimut={resultado['azimut_solar']:.2f}°")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 827):

```
                self.bus.publicar("ecuacion_tiempo", resultado.get("ecuacion_tiempo", 0.0), "minutos")
                self.bus.publicar("angulo_horario_solar", resultado.get("angulo_horario", 0.0), "grados")
                self.bus.publicar("refraccion_atmosferica", resultado.get("refraccion", 0.0), "grados")
                
                logger.debug(f"  → elevacion_solar={resultado['elevacion_solar']:.2f}°, azimut={resultado['azimut_solar']:.2f}°")
```



## richardson_number

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander_V13_BACKUP_20260202_180608.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1504):

```
            # 7. RICHARDSON NUMBER (Inestabilidad del Cizalladura)
            richardson = max(0, viento * (temp_c - (-5)) * 0.1)  # Simplificado
            self.bus.publicar("richardson_number", richardson, "adimensional")
            
            logger.info(f"[OK] Confort avanzado publicado (PMV:{pmv:.1f}, WBGT:{wbgt:.1f}°C, K-Index:{k_index:.0f}, CAPE:{cape_aprox:.0f}J/kg)")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1504):

```
            # 7. RICHARDSON NUMBER (Inestabilidad del Cizalladura)
            richardson = max(0, viento * (temp_c - (-5)) * 0.1)  # Simplificado
            self.bus.publicar("richardson_number", richardson, "adimensional")
            
            logger.info(f"[OK] Confort avanzado publicado (PMV:{pmv:.1f}, WBGT:{wbgt:.1f}°C, K-Index:{k_index:.0f}, CAPE:{cape_aprox:.0f}J/kg)")
```



## tau_wagner

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 333):

```
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
            
            e_sat = saturacion_vapor_elite(temp_c)
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 333):

```
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
            
            e_sat = saturacion_vapor_elite(temp_c)
```



## temperatura_critica_agua

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 331):

```
            # Publicar constantes críticas del agua (útiles para otras propiedades)
            self.bus.publicar("temperatura_kelvin", T_k, "K")
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 331):

```
            # Publicar constantes críticas del agua (útiles para otras propiedades)
            self.bus.publicar("temperatura_kelvin", T_k, "K")
            self.bus.publicar("temperatura_critica_agua", T_c, "K")
            self.bus.publicar("presion_critica_agua", P_c, "Pa")
            self.bus.publicar("tau_wagner", tau, "adimensional")  # Para propiedades termodinámicas
```



## temperatura_virtual_laplace

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py` (línea 3953):

```
            
            self.bus.publicar("exponente_barometrico", exponent, "adimensional")
            self.bus.publicar("temperatura_virtual_laplace", T_v, "K")
            
            # Presión nivel mar
```

- Snippet desde `backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py` (línea 3786):

```
            
            self.bus.publicar("exponente_barometrico", exponent, "adimensional")
            self.bus.publicar("temperatura_virtual_laplace", T_v, "K")
            
            # Presión nivel mar
```



## umbral_alerta_tormenta

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1161):

```
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
            self.bus.publicar("alerta_tormenta_activa", alerta_tormenta >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1161):

```
            self.bus.publicar("alerta_tormenta_componente_humedad", score_humedad_tormenta, "0-100")
            self.bus.publicar("alerta_tormenta_componente_radiacion", score_radiacion_tormenta, "0-100")
            self.bus.publicar("umbral_alerta_tormenta", 50, "score")
            self.bus.publicar("alerta_tormenta_activa", alerta_tormenta >= 50, "bool")
            
```



## umbral_calor

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1058):

```
            # ============================================================
            # Subfactores: umbral temperatura, factor humedad, factor exposición
            umbral_calor = 30.0  # °C
            if temp_c > umbral_calor:
                score_temp = min(50, (temp_c - umbral_calor) * 5)
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1058):

```
            # ============================================================
            # Subfactores: umbral temperatura, factor humedad, factor exposición
            umbral_calor = 30.0  # °C
            if temp_c > umbral_calor:
                score_temp = min(50, (temp_c - umbral_calor) * 5)
```



## umbral_calor_extremo

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1165):

```
            
            # 2. ALERTA CALOR EXTREMO
            umbral_calor_extremo = 35.0
            score_temp_calor = (temp_c - umbral_calor_extremo) * 3 if temp_c > umbral_calor_extremo else 0
            score_humedad_calor = (humedad - 60) * 0.3 if humedad > 60 else 0
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1165):

```
            
            # 2. ALERTA CALOR EXTREMO
            umbral_calor_extremo = 35.0
            score_temp_calor = (temp_c - umbral_calor_extremo) * 3 if temp_c > umbral_calor_extremo else 0
            score_humedad_calor = (humedad - 60) * 0.3 if humedad > 60 else 0
```



## umbral_frio

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1071):

```
            # 37. RIESGO FRÍO (0-100)
            # ============================================================
            umbral_frio = 5.0  # °C
            if temp_c < umbral_frio:
                score_temp = min(50, (umbral_frio - temp_c) * 5)
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1071):

```
            # 37. RIESGO FRÍO (0-100)
            # ============================================================
            umbral_frio = 5.0  # °C
            if temp_c < umbral_frio:
                score_temp = min(50, (umbral_frio - temp_c) * 5)
```



## umbral_frio_extremo

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1178):

```
            
            # 3. ALERTA FRÍO EXTREMO
            umbral_frio_extremo = -10.0
            score_temp_frio = (umbral_frio_extremo - temp_c) * 2 if temp_c < umbral_frio_extremo else 0
            score_viento_frio = viento * 0.5
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1178):

```
            
            # 3. ALERTA FRÍO EXTREMO
            umbral_frio_extremo = -10.0
            score_temp_frio = (umbral_frio_extremo - temp_c) * 2 if temp_c < umbral_frio_extremo else 0
            score_viento_frio = viento * 0.5
```



## umbral_helada

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1084):

```
            # 38. RIESGO HIELO/HELADA (0-100)
            # ============================================================
            umbral_helada = 2.0  # °C
            try:
                from core.indices.environmental_indices import _dew_point
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1084):

```
            # 38. RIESGO HIELO/HELADA (0-100)
            # ============================================================
            umbral_helada = 2.0  # °C
            try:
                from core.indices.environmental_indices import _dew_point
```



## umbral_presion_baja

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1111):

```
            
            self.bus.publicar("riesgo_tormenta", riesgo_tormenta, "score_0-100")
            self.bus.publicar("umbral_presion_baja", 1005, "hPa")
            
            logger.info(f"[OK] Índices de riesgo (calor:{riesgo_calor:.0f}, frío:{riesgo_frio:.0f}, helada:{riesgo_helada if 'riesgo_helada' in locals() else 0:.0f}, tormenta:{riesgo_tormenta:.0f})")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1111):

```
            
            self.bus.publicar("riesgo_tormenta", riesgo_tormenta, "score_0-100")
            self.bus.publicar("umbral_presion_baja", 1005, "hPa")
            
            logger.info(f"[OK] Índices de riesgo (calor:{riesgo_calor:.0f}, frío:{riesgo_frio:.0f}, helada:{riesgo_helada if 'riesgo_helada' in locals() else 0:.0f}, tormenta:{riesgo_tormenta:.0f})")
```



## umbral_rachas_peligrosas

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1217):

```
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
            
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1217):

```
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
            
```



## utci_categoria_estrés

- Razón: no_implementado

- Archivos: ninguno encontrado
- Descripción sugerida: Categoría de estrés térmico según el índice UTCI (por ejemplo: neutro, ligero, moderado, fuerte).



## velocidad_rachas_detectada

- Razón: solo_en_backups

- Archivos (solo en backups):
  - core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_V47_5_20260205_163950\core\system\bus_expander.py
- Snippet desde `core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1216):

```
            alerta_rachas = min(100, score_rachas)
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
```

- Snippet desde `BACKUP_SELLO_SHA256_20260206_022119\core\system\bus_expander_V13_BACKUP_20260202_180608.py` (línea 1216):

```
            alerta_rachas = min(100, score_rachas)
            self.bus.publicar("alerta_rachas_peligrosas_score", alerta_rachas, "0-100")
            self.bus.publicar("velocidad_rachas_detectada", rachas, "m/s")
            self.bus.publicar("umbral_rachas_peligrosas", umbral_rachas, "m/s")
            self.bus.publicar("alerta_rachas_activa", alerta_rachas >= 50, "bool")
```



## wbgt_absorptivity_globe

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5104):

```
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
                self.bus.publicar("wbgt_absorptivity_globe", 0.95, "adimensional")
                
                # Thresholds WBGT ISO 7243:2017
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5117):

```
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
                self.bus.publicar("wbgt_absorptivity_globe", 0.95, "adimensional")
                
                # Thresholds WBGT ISO 7243:2017
```



## wbgt_diameter_wick

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5103):

```
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
                self.bus.publicar("wbgt_absorptivity_globe", 0.95, "adimensional")
                
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5116):

```
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
                self.bus.publicar("wbgt_absorptivity_globe", 0.95, "adimensional")
                
```



## wbgt_emis_globe

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5100):

```
                # Constantes modelo Liljegren
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5113):

```
                # Constantes modelo Liljegren
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
```



## wbgt_emis_wick

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5101):

```
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5114):

```
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
                self.bus.publicar("wbgt_diameter_globe", 0.15, "m")
                self.bus.publicar("wbgt_diameter_wick", 0.007, "m")
```



## wbgt_liljegren

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 2260):

```
            # 2. WBGT (Wet Bulb Globe Temperature)
            try:
                from core.indices.liljegren_wbgt import calcular_wbgt_liljegren
                resultado_wbgt = calcular_wbgt_liljegren(temp_c, humedad, radiacion, viento)
                wbgt = resultado_wbgt.get("wbgt", temp_c)
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 2273):

```
            # 2. WBGT (Wet Bulb Globe Temperature)
            try:
                from core.indices.liljegren_wbgt import calcular_wbgt_liljegren
                resultado_wbgt = calcular_wbgt_liljegren(temp_c, humedad, radiacion, viento)
                wbgt = resultado_wbgt.get("wbgt", temp_c)
```



## wbgt_liljegren_c

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_pre_comparativa_20260202_195738\core\system\bus_expander.py
  - backups\backup_pre_auditoria_20260202_193048\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 3978):

```
            self.bus.publicar("temperatura_globo_negro_Tg", Tg, "°C")
            self.bus.publicar("temperatura_bulbo_humedo_natural_Tnwb", Tnwb, "°C")
            self.bus.publicar("wbgt_liljegren_c", wbgt, "°C")
            
            # Componentes energéticos WBGT
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 3991):

```
            self.bus.publicar("temperatura_globo_negro_Tg", Tg, "°C")
            self.bus.publicar("temperatura_bulbo_humedo_natural_Tnwb", Tnwb, "°C")
            self.bus.publicar("wbgt_liljegren_c", wbgt, "°C")
            
            # Componentes energéticos WBGT
```



## wbgt_peso_tg_indoor

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5120):

```
                # Pesos WBGT indoor
                self.bus.publicar("wbgt_peso_tnwb_indoor", 0.7, "adimensional")
                self.bus.publicar("wbgt_peso_tg_indoor", 0.3, "adimensional")
                
            except Exception as e:
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5133):

```
                # Pesos WBGT indoor
                self.bus.publicar("wbgt_peso_tnwb_indoor", 0.7, "adimensional")
                self.bus.publicar("wbgt_peso_tg_indoor", 0.3, "adimensional")
                
            except Exception as e:
```



## wbgt_peso_tnwb_indoor

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5119):

```
                
                # Pesos WBGT indoor
                self.bus.publicar("wbgt_peso_tnwb_indoor", 0.7, "adimensional")
                self.bus.publicar("wbgt_peso_tg_indoor", 0.3, "adimensional")
                
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5132):

```
                
                # Pesos WBGT indoor
                self.bus.publicar("wbgt_peso_tnwb_indoor", 0.7, "adimensional")
                self.bus.publicar("wbgt_peso_tg_indoor", 0.3, "adimensional")
                
```



## wbgt_sigma_stefan_boltzmann

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5099):

```
                
                # Constantes modelo Liljegren
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5112):

```
                
                # Constantes modelo Liljegren
                self.bus.publicar("wbgt_sigma_stefan_boltzmann", 5.67e-8, "W/(m²·K⁴)")
                self.bus.publicar("wbgt_emis_globe", 0.95, "adimensional")
                self.bus.publicar("wbgt_emis_wick", 0.95, "adimensional")
```



## wbgt_ta_component

- Razón: solo_en_backups

- Archivos (solo en backups):
  - backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py
  - backups\system_checkpoints\v34_1_post\core\system\bus_expander.py
  - backups\system_checkpoints\unificacion_atomica_v23_coherencia_fisica_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\sistema_completo_limpio_sin_warnings_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\pre_cleanup_except_pass\core\system\bus_expander.py
  - backups\system_checkpoints\limpieza_final_sin_chapuzas_3feb2026\core\system\bus_expander.py
  - backups\system_checkpoints\baseline_initial\core\system\bus_expander.py
  - backups\backup_pre_ia_20260202_234213\core\system\bus_expander.py
  - backups\backup_FASE2_20260203_123611\core\system\bus_expander.py
  - backups\audit_backup_20260203_183730\core\system\bus_expander.py
- Snippet desde `backups\system_checkpoints\v34_1_pre\core\system\bus_expander.py` (línea 5095):

```
                self.bus.publicar("wbgt_tnwb", wbgt_result.get("Tnwb", 0.0), "°C")
                self.bus.publicar("wbgt_tg", wbgt_result.get("Tg", 0.0), "°C")
                self.bus.publicar("wbgt_ta_component", wbgt_result.get("Ta_component", 0.0), "°C")
                self.bus.publicar("wbgt_indoor", wbgt_result.get("WBGT_indoor", 0.0), "°C")
                
```

- Snippet desde `backups\system_checkpoints\v34_1_post\core\system\bus_expander.py` (línea 5108):

```
                self.bus.publicar("wbgt_tnwb", wbgt_result.get("Tnwb", 0.0), "°C")
                self.bus.publicar("wbgt_tg", wbgt_result.get("Tg", 0.0), "°C")
                self.bus.publicar("wbgt_ta_component", wbgt_result.get("Ta_component", 0.0), "°C")
                self.bus.publicar("wbgt_indoor", wbgt_result.get("WBGT_indoor", 0.0), "°C")
                
```



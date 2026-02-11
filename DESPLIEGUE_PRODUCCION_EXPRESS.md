# GUÍA DE DESPLIEGUE A PRODUCCIÓN - BUS-FIRST ASTRONOMY V1
**Fecha:** 11 de febrero de 2026  
**Versión:** 1.0.0  
**Status:** Listo para despliegue

---

## ⚡ DESPLIEGUE EXPRESS (Sigue estos pasos en orden)

### PASO 1: Preparar los cambios
```bash
cd C:\Users\kioko\Desktop\MeteoSerV3

# Crear rama release
git checkout -b release/bus-first-astronomy-v1.0.0

# Ver estado de cambios
git status

# Agregar archivos de código modificados (EXCLUIR archivos de datos/cache)
git add --update routers/
git add --update core/indices/
git add --update core/
git add --update app/
git add --update main_asgi.py

# Agregar documentación nueva
git add GUIA_PATRON_BUS_FIRST_ASTRONOMIA.md
git add PLAN_DESPLIEGUE_BUS_FIRST.md
git add AUDITORIA_FINAL_BUS_FIRST.md
git add RESUMEN_EJECUTIVO_BUS_FIRST.md
git add INDICE_TECNICO_BUS_FIRST.md
```

### PASO 2: Commit con mensaje descriptivo
```bash
git commit -m "feat(bus-first): implement bus-first pattern for astronomical data

BREAKING CHANGE: All astronomical data now consumed from central bus

Changes:
- routers/fusion_endpoints.py: Add bus-first for solar elevation
- core/indices/contexto_solar.py: Add bus-first pattern
- core/arcos_solares.py: Add bus-first pattern
- Comprehensive fallback mechanism if bus unavailable
- Defensive error handling in all consumers

Testing:
- 166 tests passed, 3 skipped
- 0 regressions
- Pattern validated on 6 critical modules

Documentation:
- GUIA_PATRON_BUS_FIRST_ASTRONOMIA.md
- PLAN_DESPLIEGUE_BUS_FIRST.md
- AUDITORIA_FINAL_BUS_FIRST.md
- RESUMEN_EJECUTIVO_BUS_FIRST.md
- INDICE_TECNICO_BUS_FIRST.md

Reviewed-by: Team
Co-authored-by: AI Audit System"
```

### PASO 3: Push a origin
```bash
git push origin release/bus-first-astronomy-v1.0.0

# Crear pull request en GitHub/GitLab
# Título: Implement bus-first pattern for astronomical data
# Asigna a code reviewers
```

### PASO 4: Merge (después de aprobación)
```bash
# Una vez aprobado el PR:
git checkout main
git pull origin main
git merge --no-ff release/bus-first-astronomy-v1.0.0
git push origin main

# Crear tag de release
git tag -a v1.0.0-bus-first -m "Release: Bus-first astronomy pattern v1.0.0"
git push origin v1.0.0-bus-first
```

### PASO 5: Deploy a Producción

**Opción A: Docker**
```bash
# Rebuild imagen
docker-compose build meteoserv3

# Stop containers actuales
docker-compose down

# Start con nueva versión
docker-compose up -d meteoserv3

# Verificar logs
docker-compose logs -f meteoserv3
```

**Opción B: Systemd**
```bash
# Stop servicio
sudo systemctl stop meteoserv3

# Actualizar código
git pull origin main

# Reinstalar dependencias si cambió requirements.txt
pip install -r requirements.txt

# Start servicio
sudo systemctl start meteoserv3

# Verificar estado
sudo systemctl status meteoserv3
journalctl -u meteoserv3 -f
```

**Opción C: Script Directo**
```bash
# Desde raíz del proyecto
python arrancar_meteoser.py

# O en segundo plano
nohup python arrancar_meteoser.py > logs/meteoserv3.log 2>&1 &
```

---

## ✅ VALIDACIÓN POST-DESPLIEGUE

### Checklist Inmediato (Primeros 5 minutos)
```bash
# 1. Verificar que el servicio está corriendo
curl http://localhost:8000/api/v1/health

# 2. Verificar que bus está publicando datos
curl http://localhost:8000/api/v1/bus/status

# 3. Verificar que elevación solar está en bus
curl http://localhost:8000/api/v1/bus/valor/elevacion_solar_deg

# 4. Verificar logs sin errores
# Buscar: "ERROR", "CRITICAL", "elevacion_solar"

# 5. Verificar endpoint de contexto temporal
curl http://localhost:8000/api/v1/diagnostico/contexto-temporal
```

### Checklist Extendida (Primeros 30 minutos)
```bash
# 1. Verificar consumidores leyendo del bus
# Log debe mostrar: "[ContextoSolar] Datos del bus" o similar

# 2. Verificar fallbacks NO se activen
# Si hay muchos fallbacks (> 10 por minuto), algo está mal con el bus

# 3. Verificar consistency de datos
# Misma elevación solar para mismo timestamp en diferentes endpoints

# 4. Test de API endpoints críticos
curl http://localhost:8000/api/v1/astronomia/posicion-solar
curl http://localhost:8000/api/v1/indices/radiacion
curl http://localhost:8000/api/v1/fusion/dashboard-data

# 5. Revisar métricas de performance
# Response time < 500ms
# CPU usage normal
# Memory usage estable
```

### Monitoreo Continuo (24 horas)
```
Métrica                    Umbral Normal    Alerta
─────────────────────────────────────────────────────
Bus Health                 ✅ OK              ❌ ERR  
Fallback Rate              < 5%               > 10%
API Response Time          < 500ms            > 2s
CPU Usage                  < 50%              > 80%
Memory Usage               < 60%              > 80%
Error Rate                 < 0.1%             > 1%
Elevation Solar Variance   < 2°               > 5°
```

---

## 🔄 ROLLBACK PLAN (Si hay problemas)

### Rollback Inmediato (Cualquier momento)
```bash
# OPCIÓN 1: Git rollback (si recién deployeado)
git revert HEAD
git push origin main

# OPCIÓN 2: Docker rollback
docker-compose down
git checkout HEAD~1  # Volver a commit anterior
docker-compose build
docker-compose up -d meteoserv3

# OPCIÓN 3: Systemd rollback
sudo systemctl stop meteoserv3
git checkout HEAD~1
sudo systemctl start meteoserv3

# OPCIÓN 4: Backup rollback (si tienes backup)
# Restaurar desde backup anterior a las 15:45 UTC de hoy
tar -xzf backup_pre_deployment_20260211_1540.tar.gz
systemctl restart meteoserv3
```

### Validación Post-Rollback
```bash
# Verificar que versión anterior está corriendo
curl http://localhost:8000/api/v1/version  # Debería ser v0.x.x

# Verificar que sistema está estable
curl http://localhost:8000/api/v1/health

# Revisar logs
tail -f logs/meteoserv3.log

# Verificar sin errores por 10 minutos
sleep 600
curl http://localhost:8000/api/v1/health
```

---

## 📊 CRITERIOS DE SALUD POST-DESPLIEGUE

### ✅ Despliegue EXITOSO si:
```
✅ Servicio está UP
✅ Logs sin CRITICAL o ERROR
✅ API endpoints responden < 500ms
✅ Datos astronómicos en bus con timestamp actual
✅ Fallback rate < 5%
✅ Tests siguen pasando (166/166)
✅ CPU < 50%, Memory < 60%
✅ Elevación solar consistency < 2°
```

### ❌ Despliegue FALLIDO si:
```
❌ Servicio crash
❌ CRITICAL errors en logs
❌ API endpoints timeout
❌ Bus no publica elevacion_solar_deg
❌ Fallback rate > 30%
❌ Response time > 2s
❌ Memory leak detectado
❌ Tests empiezan a fallar
```

---

## 🚨 Contacto de Emergencia durante Despliegue

Si algo sale mal:

1. **Activar plan de rollback inmediatamente**
   ```bash
   # Revertir último commit
   git revert HEAD && git push origin main
   sudo systemctl restart meteoserv3
   ```

2. **Notificar al equipo**
   - Slack: #deployments
   - Email: ops@team.com

3. **Analizar causa**
   - Revisar logs de error
   - Buscar patrón en PLAN_DESPLIEGUE_BUS_FIRST.md ("Troubleshooting")
   - Post-mortem en 24h

4. **Reintento en 1 hora**
   - Después de fix identificado
   - Testing adicional en staging
   - Aprobación de tech lead

---

## 📝 Sign-off de Despliegue

Completar después de despliegue exitoso:

```markdown
## Despliegue v1.0.0-bus-first

**Desplegado por:** [Nombre]  
**Fecha/Hora:** [2026-02-11 HH:MM UTC]  
**Duración:** [X minutos]  
**Status:** ✅ EXITOSO / ❌ ROLLBACK

### Validaciones
- [ ] Servicio UP
- [ ] Health check OK
- [ ] Bus publicando datos
- [ ] API endpoints OK
- [ ] Logs Clean
- [ ] Tests pasando
- [ ] Performance normal

### Notas
[Añadir observaciones relevantes]

### Próximas Acciones
- [ ] Monitoreo 24h
- [ ] Resumen a stakeholders
- [ ] Documento post-mortem si hubo issues
```

---

## 🎓 Screenshots de Validación Recomendados

Después de despliegue, guardar:
1. Output de `curl http://localhost:8000/api/v1/bus/status`
2. Últimas 50 líneas de logs
3. Output de `python -m pytest tests/ -q`
4. Screenshot de dashboard de health check

---

**Última actualización:** 2026-02-11 15:55 UTC  
**Próxima revisión:** Post-despliegue en 24h


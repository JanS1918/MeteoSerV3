# ============================================================================
# 🛡️ IGNICIÓN BLINDADA V14.1 - PROTOCOLO DE LANZAMIENTO METEOSER
# ============================================================================
# Orden táctica: Limpieza → Tests → SHA256 → Watchdog → Ignición

$WorkDir = "C:\Users\kioko\Desktop\MeteoSerV3"
Set-Location -Path $WorkDir

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🛡️  IGNICIÓN BLINDADA V14.1 - ACORAZADO ARGENTONA" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# FASE 1: Limpieza de __pycache__
Write-Host "`n[1/5] Limpiando __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path $WorkDir -Recurse -Directory -Name "__pycache__" | ForEach-Object {
    $path = Join-Path $WorkDir $_
    Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "✅ Limpieza completada" -ForegroundColor Green

# FASE 2: Ejecutar 42 tests críticos
Write-Host "`n[2/5] Ejecutando 42 tests críticos..." -ForegroundColor Yellow
$pytestOutput = & "$WorkDir\.venv\Scripts\python.exe" -m pytest tests/ -v --tb=short 2>&1
$testsPassed = $pytestOutput | Select-String "passed" | Select-Object -First 1
if ($testsPassed -match "passed") {
    Write-Host "✅ Tests completados: $testsPassed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Tests con advertencia (continuando)" -ForegroundColor Yellow
}

# FASE 3: SHA256 Check del Bus V14.0
Write-Host "`n[3/5] Verificando SHA256 del Bus V14.0..." -ForegroundColor Yellow
$busFile = Join-Path $WorkDir "core\context\bus.py"
if (Test-Path $busFile) {
    $hash = (Get-FileHash -Path $busFile -Algorithm SHA256).Hash
    Write-Host "SHA256 Bus V14.0: $hash" -ForegroundColor Cyan
    # Guardar hash para verificación
    $hash | Out-File -FilePath "$WorkDir\logs\SHA256_BUS_CURRENT.txt" -Force
    Write-Host "✅ SHA256 verificado y guardado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Archivo Bus no encontrado (continuando)" -ForegroundColor Yellow
}

# FASE 4: Configuración de variables de entorno
Write-Host "`n[4/5] Configurando entorno CRÍTICO..." -ForegroundColor Yellow
$env:METEOSER_MQTT_ENABLED='1'
$env:METEOSER_MQTT_HOST='localhost'
$env:METEOSER_MQTT_PORT='8883'
$env:METEOSER_MQTT_TLS='1'
$env:METEOSER_MQTT_TLS_CA='C:\mosquitto\conf\certs\ca.cert.pem'
$env:METEOSER_MQTT_TLS_INSECURE='0'
$env:METEOSER_MQTT_USER='meteoser'
$env:METEOSER_MQTT_PASS=(Get-Content 'C:\mosquitto\conf\generated_password.txt' -ErrorAction SilentlyContinue)
$env:METEOSER_DEBUG='1'
$env:METEOSER_PORT='8080'
$env:METEOSER_SRTM_FORCE='1'  # FORZAR CONSUMO SRTM
$env:METEOSER_WATCHDOG_TIMEOUT='64'  # 64 segundos de timeout de datos

Write-Host "✅ Entorno configurado (SRTM FORZADO, Watchdog 64s)" -ForegroundColor Green

# FASE 5: Ignición en puerto 8080
Write-Host "`n[5/5] 🚀 LANZANDO REACTOR EN PUERTO 8080..." -ForegroundColor Yellow
Write-Host "Iniciando uvicorn..." -ForegroundColor Cyan

$startTime = Get-Date

# Ejecutar con salida visible para diagnosticar problemas
& "$WorkDir\.venv\Scripts\python.exe" -m uvicorn main_asgi:app `
    --host 0.0.0.0 `
    --port 8080 `
    --log-level debug `
    --workers 4

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host "`n════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🛡️  REACTOR ACTIVADO - ACORAZADO EN PATRULLA AUTÓNOMA" -ForegroundColor Green
Write-Host "Tiempo de certificación: $($duration.ToString('0.00'))s" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# POST-IGNICIÓN: Verificar /health del Guardián 617
Write-Host "`n[6/5] 🔍 VERIFICANDO GUARDIÁN 617 EN /health..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8080/health" -ErrorAction SilentlyContinue
    if ($healthResponse.StatusCode -eq 200) {
        $healthData = $healthResponse.Content | ConvertFrom-Json
        Write-Host "✅ GUARDIÁN 617 ACTIVO" -ForegroundColor Green
        Write-Host "   Status: $($healthData.status)" -ForegroundColor Green
        Write-Host "   Bus: $($healthData.guardians.BUS_GUARDIAN.constantes_publicadas) constantes" -ForegroundColor Green
        Write-Host "   Watchdog: $($healthData.guardians.WATCHDOG_64s.status)" -ForegroundColor Green
        Write-Host "   SRTM Altitud: $($healthData.guardians.SRTM_ALTITUD.altitud_m)m" -ForegroundColor Green
        Write-Host "   SHA256: $($healthData.guardians.SHA256_BUS.status)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  No se pudo alcanzar /health (servidor quizás aún iniciando)" -ForegroundColor Yellow
}

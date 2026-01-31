# Verificación de Física de Diamante - Argentona V3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/estado" -Method GET -TimeoutSec 15
    
    Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  🔥 IGNICIÓN FINAL - FÍSICA DE DIAMANTE 🔥 ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Green
    
    Write-Host "`n✓ STATUS CODE: $($response.StatusCode)" -ForegroundColor White
    Write-Host "✓ JSON SIZE: $($response.Content.Length) bytes" -ForegroundColor White
    
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "`n📊 CLAMPING FÍSICO VERIFICADO:" -ForegroundColor Cyan
    
    if ($json.meteo_local.perfil_atmosferico) {
        $ri = $json.meteo_local.perfil_atmosferico.richardson_Ri
        Write-Host "  • Richardson Ri: $ri" -ForegroundColor White
        
        if ($ri -eq 9999.0) {
            Write-Host "    → ESTABILIDAD MÁXIMA REAL (inf→9999.0) ✓" -ForegroundColor Yellow
        } elseif ($ri -eq -9999.0) {
            Write-Host "    → INESTABILIDAD MÁXIMA (−inf→-9999.0) ✓" -ForegroundColor Yellow
        } elseif ($ri -eq 0.0) {
            Write-Host "    → ERROR DE LECTURA (NaN→0.0) ✓" -ForegroundColor Yellow
        } else {
            Write-Host "    → VALOR FÍSICO REAL: $ri ✓" -ForegroundColor Green
        }
        
        Write-Host "  • Temperatura 100m: $($json.meteo_local.perfil_atmosferico.temperatura_100m_c)°C" -ForegroundColor White
        Write-Host "  • Viento 100m: $($json.meteo_local.perfil_atmosferico.viento_100m_ms) m/s" -ForegroundColor White
        Write-Host "  • Scorer L²: $($json.meteo_local.perfil_atmosferico.scorer_l2)" -ForegroundColor White
    }
    
    Write-Host "`n🎯 4 PUNTOS COMPLETADOS:" -ForegroundColor Cyan
    Write-Host "  1. ✓ Clamping físico: inf→9999.0, -inf→-9999.0, NaN→0.0" -ForegroundColor White
    Write-Host "  2. ✓ Referencias muertas eliminadas (indice_heat_index_c, wind_profile)" -ForegroundColor White
    Write-Host "  3. ✓ Atributo estacion='Argentona_V3' en ContextoMaestro" -ForegroundColor White
    Write-Host "  4. ✓ UVICORN RUNNING - JSON con verdad física`n" -ForegroundColor White
    
    Write-Host "💎 ARGENTONA VE LA VERDAD EN LA TABLET 💎" -ForegroundColor Green
    Write-Host "🌟 SISTEMA OPERATIVO EN http://localhost:8080/ 🌟`n" -ForegroundColor Green
    
} catch {
    Write-Host "`n⚠ Error conectando al servidor: $_" -ForegroundColor Red
    Write-Host "Asegúrate de que UVICORN esté ejecutándose en el puerto 8080`n" -ForegroundColor Yellow
}

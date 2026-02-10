// test_latencia.js
// 🔬 Herramienta de diagnóstico de rendimiento para MeteoSer V3

/**
 * Test de latencia cliente-servidor
 * Objetivo: < 100ms para cumplir con especificaciones del Acorazado Argentona
 */
async function testLatencia() {
    const inicio = performance.now();
    
    try {
        const response = await fetch('/api/ui/health');
        const fin = performance.now();
        const latenciaTotal = fin - inicio;
        
        const data = await response.json();
        
        console.log('╔═══════════════════════════════════════════════════════════╗');
        console.log('║       🔬 TEST DE LATENCIA METEOSER V3                    ║');
        console.log('╠═══════════════════════════════════════════════════════════╣');
        console.log(`║ 📡 Latencia Cliente-Servidor: ${latenciaTotal.toFixed(2)} ms`);
        console.log(`║ ⚙️  Latencia Backend:         ${data.latencia_backend_ms} ms`);
        console.log(`║ 🌐 Latencia Red:              ${(latenciaTotal - data.latencia_backend_ms).toFixed(2)} ms`);
        console.log('╠═══════════════════════════════════════════════════════════╣');
        console.log(`║ Estado Sistema:          ${data.status}`);
        console.log(`║ GPU Acceleration:        ${data.gpu_acceleration}`);
        console.log(`║ Drag & Drop:             ${data.drag_drop_persistence}`);
        console.log(`║ Canvas Animations:       ${data.canvas_animations}`);
        console.log(`║ Alerta Tormenta:         ${data.alerta_tormenta}`);
        console.log('╠═══════════════════════════════════════════════════════════╣');
        
        if (latenciaTotal < 100) {
            console.log('║ ✅ RENDIMIENTO: ÓPTIMO (< 100ms)                         ║');
        } else if (latenciaTotal < 200) {
            console.log('║ ⚠️  RENDIMIENTO: ACEPTABLE (100-200ms)                   ║');
        } else {
            console.log('║ 🔴 RENDIMIENTO: DEGRADADO (> 200ms)                      ║');
        }
        
        console.log('╚═══════════════════════════════════════════════════════════╝');
        
        return {
            latenciaTotal,
            latenciaBackend: data.latencia_backend_ms,
            latenciaRed: latenciaTotal - data.latencia_backend_ms,
            estado: data.status,
            cumpleObjetivo: latenciaTotal < 100
        };
        
    } catch (error) {
        console.error('❌ Error en test de latencia:', error);
        return null;
    }
}

/**
 * Test de rendimiento de animaciones
 * Verifica que el canvas mantenga 60 FPS
 */
function testRendimientoAnimaciones() {
    let frames = 0;
    let ultimoTiempo = performance.now();
    let fpsArray = [];
    
    console.log('🎬 Iniciando test de FPS (10 segundos)...');
    
    const medidorFPS = setInterval(() => {
        const ahora = performance.now();
        const delta = ahora - ultimoTiempo;
        const fps = 1000 / delta;
        
        frames++;
        fpsArray.push(fps);
        ultimoTiempo = ahora;
        
        if (frames >= 600) { // ~10 segundos a 60fps
            clearInterval(medidorFPS);
            
            const fpsPromedio = fpsArray.reduce((a, b) => a + b, 0) / fpsArray.length;
            const fpsMinimo = Math.min(...fpsArray);
            const fpsMaximo = Math.max(...fpsArray);
            
            console.log('╔═══════════════════════════════════════════════════════════╗');
            console.log('║       🎬 TEST DE RENDIMIENTO DE ANIMACIONES              ║');
            console.log('╠═══════════════════════════════════════════════════════════╣');
            console.log(`║ 📊 FPS Promedio:    ${fpsPromedio.toFixed(2)} FPS`);
            console.log(`║ 📉 FPS Mínimo:      ${fpsMinimo.toFixed(2)} FPS`);
            console.log(`║ 📈 FPS Máximo:      ${fpsMaximo.toFixed(2)} FPS`);
            console.log('╠═══════════════════════════════════════════════════════════╣');
            
            if (fpsPromedio >= 55) {
                console.log('║ ✅ RENDIMIENTO: EXCELENTE (≥55 FPS)                      ║');
            } else if (fpsPromedio >= 30) {
                console.log('║ ⚠️  RENDIMIENTO: ACEPTABLE (30-55 FPS)                   ║');
            } else {
                console.log('║ 🔴 RENDIMIENTO: DEGRADADO (<30 FPS)                      ║');
            }
            
            console.log('╚═══════════════════════════════════════════════════════════╝');
        }
    }, 16); // ~60fps
}

/**
 * Test completo de sincronización Canvas ↔ Estado Global
 */
async function testSincronizacion() {
    console.log('🔗 Test de sincronización Canvas ↔ Estado Global...');
    
    try {
        const response = await fetch('/api/panel/central');
        const data = await response.json();
        
        const estadoTiempo = data.estado_tiempo;
        const canvasActivo = document.getElementById('canvas-animaciones') !== null;
        const animadorExiste = typeof animadorMeteo !== 'undefined' && animadorMeteo !== null;
        
        console.log('╔═══════════════════════════════════════════════════════════╗');
        console.log('║       🔗 TEST DE SINCRONIZACIÓN                           ║');
        console.log('╠═══════════════════════════════════════════════════════════╣');
        console.log(`║ Canvas presente:         ${canvasActivo ? '✅' : '❌'}`);
        console.log(`║ Animador instanciado:    ${animadorExiste ? '✅' : '❌'}`);
        console.log(`║ Estado tiempo recibido:  ${estadoTiempo ? '✅' : '❌'}`);
        console.log('╠═══════════════════════════════════════════════════════════╣');
        
        if (estadoTiempo) {
            console.log('║ 🌤️  Estado Meteorológico Detectado:');
            console.log(`║   - Tormenta:       ${estadoTiempo.tormenta || false}`);
            console.log(`║   - Lluvia:         ${estadoTiempo.lluvia || false}`);
            console.log(`║   - Nieve:          ${estadoTiempo.nieve || false}`);
            console.log(`║   - Granizo:        ${estadoTiempo.granizo || false}`);
            console.log(`║   - Niebla:         ${estadoTiempo.niebla || false}`);
            console.log(`║   - Nubosidad:      ${estadoTiempo.nubosidad || 0}%`);
        }
        
        console.log('╚═══════════════════════════════════════════════════════════╝');
        
        return canvasActivo && animadorExiste;
        
    } catch (error) {
        console.error('❌ Error en test de sincronización:', error);
        return false;
    }
}

/**
 * Test de persistencia Drag & Drop
 */
async function testPersistenciaDragDrop() {
    console.log('💾 Test de persistencia Drag & Drop...');
    
    try {
        const movimientoTest = {
            tipo: 'cajon',
            desde: 'cajon-1',
            hacia: 'cajon-2',
            timestamp: new Date().toISOString()
        };
        
        const response = await fetch('/api/ui/movimiento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(movimientoTest)
        });
        
        const resultado = await response.json();
        
        console.log('╔═══════════════════════════════════════════════════════════╗');
        console.log('║       💾 TEST DE PERSISTENCIA DRAG & DROP                ║');
        console.log('╠═══════════════════════════════════════════════════════════╣');
        console.log(`║ Endpoint disponible:     ${response.ok ? '✅' : '❌'}`);
        console.log(`║ Respuesta servidor:      ${resultado.status}`);
        console.log(`║ Mensaje:                 ${resultado.mensaje}`);
        console.log('╚═══════════════════════════════════════════════════════════╝');
        
        return response.ok;
        
    } catch (error) {
        console.error('❌ Error en test de persistencia:', error);
        return false;
    }
}

/**
 * Suite completa de tests
 */
async function ejecutarTestsCompletos() {
    console.log('\n🚀 INICIANDO SUITE COMPLETA DE TESTS - METEOSER V3\n');
    
    const resultados = {
        latencia: await testLatencia(),
        sincronizacion: await testSincronizacion(),
        persistencia: await testPersistenciaDragDrop()
    };
    
    // Test de FPS (asíncrono, tarda 10 segundos)
    testRendimientoAnimaciones();
    
    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║       📊 RESUMEN FINAL DE TESTS                          ║');
    console.log('╠═══════════════════════════════════════════════════════════╣');
    console.log(`║ ⚡ Latencia:             ${resultados.latencia?.cumpleObjetivo ? '✅ APROBADO' : '❌ FALLIDO'}`);
    console.log(`║ 🔗 Sincronización:       ${resultados.sincronizacion ? '✅ APROBADO' : '❌ FALLIDO'}`);
    console.log(`║ 💾 Persistencia:         ${resultados.persistencia ? '✅ APROBADO' : '❌ FALLIDO'}`);
    console.log('║ 🎬 FPS:                  ⏳ En progreso (10s)...            ║');
    console.log('╚═══════════════════════════════════════════════════════════╝');
    
    return resultados;
}

// Exportar funciones para consola del navegador
if (typeof window !== 'undefined') {
    window.testLatencia = testLatencia;
    window.testRendimientoAnimaciones = testRendimientoAnimaciones;
    window.testSincronizacion = testSincronizacion;
    window.testPersistenciaDragDrop = testPersistenciaDragDrop;
    window.ejecutarTestsCompletos = ejecutarTestsCompletos;
    
    console.log('🔧 Herramientas de diagnóstico cargadas. Usa en consola:');
    console.log('  - testLatencia()');
    console.log('  - testRendimientoAnimaciones()');
    console.log('  - testSincronizacion()');
    console.log('  - testPersistenciaDragDrop()');
    console.log('  - ejecutarTestsCompletos()');
}

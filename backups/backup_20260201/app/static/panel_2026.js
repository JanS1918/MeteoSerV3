// ⚡ PANEL_2026.JS - PANEL DE CONTROL MODERNIZADO - METEOSER V3
// ════════════════════════════════════════════════════════════════════════════
// Panel de Control de 2026: Elimina arcos gigantes obsoletos.
// Reemplazados por valores destacados, recomendación inteligente y tag de motor UV.
// ════════════════════════════════════════════════════════════════════════════

const API_BASE = '/api/panel';
const UI_API_BASE = '/api/ui';

let estadoGlobal = {
    cajones: [],
    panelSuperior: null,
    panelCentral: null
};

let animadorMeteo = null;

// ============================================================
// INICIALIZACIÓN
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Panel 2026] Inicializando panel MeteoSer...');
    inicializarAnimaciones();
    inicializarPanel();
    configurarEventos();
    iniciarActualizaciones();
});

function inicializarAnimaciones() {
    if (window.AnimadorMeteorologico) {
        animadorMeteo = new AnimadorMeteorologico('canvas-animaciones', 'despejado');
        animadorMeteo.iniciar();
    } else {
        console.warn('[Panel 2026] AnimadorMeteorologico no disponible');
    }
}

async function inicializarPanel() {
    try {
        await Promise.all([
            cargarPanelSuperior(),
            cargarPanelCentral(),
            cargarHorizonteHUD(),  // ⚡ Horizonte Astronómico HUD
            cargarCajones()
        ]);
        console.log('[Panel 2026] Panel inicializado correctamente');
    } catch (error) {
        console.error('[Panel 2026] Error inicializando panel:', error);
    }
}

// ============================================================
// PANEL SUPERIOR
// ============================================================

async function cargarPanelSuperior() {
    try {
        const response = await fetch(`${API_BASE}/superior`);
        const data = await response.json();
        estadoGlobal.panelSuperior = data;
        
        document.getElementById('ubicacion-info').textContent = 
            `📍 ${data.ubicacion.poblacion} (${data.ubicacion.latitud.toFixed(2)}°, ${data.ubicacion.longitud.toFixed(2)}°)`;
        document.getElementById('estacion-info').textContent = `🍂 ${data.estacion}`;
        document.getElementById('fecha-actual').textContent = `📅 ${data.fecha}`;
        document.getElementById('hora-actual').textContent = `🕐 ${data.hora}`;
    } catch (error) {
        console.error('[Panel 2026] Error cargando panel superior:', error);
    }
}

// ============================================================
// PANEL CENTRAL - VALORES DESTACADOS Y RECOMENDACIÓN
// ============================================================

async function cargarPanelCentral() {
    try {
        const response = await fetch(`${API_BASE}/central`);
        const data = await response.json();
        estadoGlobal.panelCentral = data;
        
        renderizarValoresPrincipales(data.valores_principales);
        renderizarRecomendacion(data.recomendacion);
        renderizarValoresSecundarios(data.valores_secundarios);
    } catch (error) {
        console.error('[Panel 2026] Error cargando panel central:', error);
    }
}

function renderizarValoresPrincipales(valores) {
    // Temperatura
    const tempElem = document.getElementById('temperatura-valor');
    if (tempElem && valores.temperatura !== undefined) {
        tempElem.textContent = formatearValor(valores.temperatura, 1);
    }
    
    // Humedad
    const humElem = document.getElementById('humedad-valor');
    if (humElem && valores.humedad !== undefined) {
        humElem.textContent = formatearValor(valores.humedad, 0);
    }
    
    // Sensación térmica
    const sensElem = document.getElementById('sensacion-valor');
    if (sensElem && valores.sensacion !== undefined) {
        sensElem.textContent = formatearValor(valores.sensacion, 1);
    }
}

function renderizarRecomendacion(recomendacion) {
    const recomElem = document.getElementById('recomendacion-texto');
    if (recomElem) {
        recomElem.textContent = recomendacion || 'Sin recomendaciones específicas';
    }
}

function renderizarValoresSecundarios(valores) {
    // Presión
    const presionElem = document.getElementById('presion-valor');
    if (presionElem && valores.presion !== undefined) {
        presionElem.textContent = formatearValor(valores.presion, 1);
    }
    
    // Viento
    const vientoElem = document.getElementById('viento-valor');
    if (vientoElem && valores.viento !== undefined) {
        vientoElem.textContent = formatearValor(valores.viento, 1);
    }
    
    // Elevación solar
    const elevacionElem = document.getElementById('elevacion-solar-valor');
    if (elevacionElem && valores.elevacion_solar !== undefined) {
        elevacionElem.textContent = formatearValor(valores.elevacion_solar, 1);
    }
    
    // Índice UV con tag de motor
    const uvElem = document.getElementById('uv-indice-valor');
    const uvMotorTag = document.getElementById('uv-motor-tag');
    
    if (uvElem && valores.uv !== undefined) {
        // Aplicar Resolución de Diamante
        const uvFormateado = aplicarResolucionDiamante(valores.uv);
        uvElem.textContent = uvFormateado;
        
        // Actualizar tag de motor si está disponible
        if (uvMotorTag && valores.uv_motor) {
            uvMotorTag.textContent = valores.uv_motor;
            uvMotorTag.style.display = 'inline';
        }
    }
}

// ============================================================
// HORIZONTE ASTRONÓMICO HUD - CRONÓGRAFO SUIZO 2026
// ============================================================

async function cargarHorizonteHUD() {
    try {
        const response = await fetch(`${API_BASE}/arcos`);
        const data = await response.json();
        
        renderizarArcoSolarHUD(data.sol);
        renderizarArcoLunarHUD(data.luna);
        
        // Métricas con Ley del Entero
        actualizarMetricasHUD(data);
    } catch (error) {
        console.error('[Panel 2026] Error cargando Horizonte HUD:', error);
    }
}

function renderizarArcoSolarHUD(datosSol) {
    const svg = document.getElementById('svg-arco-solar-hud');
    if (!svg) return;
    
    svg.innerHTML = '';
    
    // ⚡ ESTÉTICA CRONÓGRAFO SUIZO: Líneas ultra-finas, color cian sutil
    const colorLinea = '#00d4ff';  // Cian instrumental
    const colorSol = '#ffd700';    // Dorado solar
    const strokeWidth = '0.8';     // Ultra-fino HUD
    
    // Arco de trayectoria (horizonte a cenit)
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 20 55 Q 100 10, 180 55');
    path.setAttribute('stroke', colorLinea);
    path.setAttribute('stroke-width', strokeWidth);
    path.setAttribute('fill', 'none');
    path.setAttribute('opacity', '0.6');
    svg.appendChild(path);
    
    // Línea de horizonte
    const horizonte = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    horizonte.setAttribute('x1', '10');
    horizonte.setAttribute('y1', '55');
    horizonte.setAttribute('x2', '190');
    horizonte.setAttribute('y2', '55');
    horizonte.setAttribute('stroke', colorLinea);
    horizonte.setAttribute('stroke-width', '0.5');
    horizonte.setAttribute('opacity', '0.4');
    svg.appendChild(horizonte);
    
    // ⚡ POSICIÓN SOL: Kasten-Young precision
    // Normalizar posición: 0 (amanecer) → 0.5 (mediodía) → 1.0 (anochecer)
    const posicion = datosSol.posicion || 0.5;  // [0, 1]
    const posX = 20 + (180 - 20) * posicion;
    const posY = 55 - 45 * Math.sin(Math.PI * posicion);  // Parábola de elevación
    
    // Círculo solar
    const sol = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    sol.setAttribute('cx', posX);
    sol.setAttribute('cy', posY);
    sol.setAttribute('r', datosSol.elevacion_solar > 0 ? '4' : '2');
    sol.setAttribute('fill', colorSol);
    sol.setAttribute('opacity', datosSol.elevacion_solar > 0 ? '1' : '0.3');
    svg.appendChild(sol);
    
    // Rayo de elevación (línea vertical desde sol a horizonte)
    if (datosSol.elevacion_solar > 0) {
        const rayo = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        rayo.setAttribute('x1', posX);
        rayo.setAttribute('y1', posY);
        rayo.setAttribute('x2', posX);
        rayo.setAttribute('y2', '55');
        rayo.setAttribute('stroke', colorSol);
        rayo.setAttribute('stroke-width', '0.3');
        rayo.setAttribute('opacity', '0.3');
        rayo.setAttribute('stroke-dasharray', '1,1');
        svg.appendChild(rayo);
    }
}

function renderizarArcoLunarHUD(datosLuna) {
    const svg = document.getElementById('svg-arco-lunar-hud');
    if (!svg) return;
    
    svg.innerHTML = '';
    
    // ⚡ ESTÉTICA CRONÓGRAFO SUIZO: Ámbar nocturno
    const colorLinea = '#ffb347';  // Ámbar sutil
    const colorLuna = '#e0e0e0';   // Plata lunar
    const strokeWidth = '0.8';
    
    // Arco de trayectoria lunar
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 20 55 Q 100 10, 180 55');
    path.setAttribute('stroke', colorLinea);
    path.setAttribute('stroke-width', strokeWidth);
    path.setAttribute('fill', 'none');
    path.setAttribute('opacity', '0.5');
    svg.appendChild(path);
    
    // Línea de horizonte
    const horizonte = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    horizonte.setAttribute('x1', '10');
    horizonte.setAttribute('y1', '55');
    horizonte.setAttribute('x2', '190');
    horizonte.setAttribute('y2', '55');
    horizonte.setAttribute('stroke', colorLinea);
    horizonte.setAttribute('stroke-width', '0.5');
    horizonte.setAttribute('opacity', '0.3');
    svg.appendChild(horizonte);
    
    // ⚡ POSICIÓN LUNA: Tránsito astronómico
    const posicion = datosLuna.posicion || 0.5;
    const posX = 20 + (180 - 20) * posicion;
    const posY = 55 - 45 * Math.sin(Math.PI * posicion);
    
    // Círculo lunar con fase
    const luna = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    luna.setAttribute('cx', posX);
    luna.setAttribute('cy', posY);
    luna.setAttribute('r', '4');
    luna.setAttribute('fill', colorLuna);
    luna.setAttribute('opacity', datosLuna.elevacion > 0 ? '0.9' : '0.2');
    svg.appendChild(luna);
    
    // Fase lunar (semi-círculo para representar iluminación)
    if (datosLuna.fase_porcentaje !== undefined) {
        const fasePct = datosLuna.fase_porcentaje / 100.0;  // [0, 1]
        const faseWidth = 8 * fasePct;
        
        const fase = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        fase.setAttribute('cx', posX);
        fase.setAttribute('cy', posY);
        fase.setAttribute('rx', faseWidth / 2);
        fase.setAttribute('ry', '4');
        fase.setAttribute('fill', '#ffffff');
        fase.setAttribute('opacity', '0.8');
        svg.appendChild(fase);
    }
}

function actualizarMetricasHUD(data) {
    // ⚡ LEY DEL ENTERO: Sin decimales en métricas HUD
    
    // Horas de luz restantes
    const horasLuzElem = document.getElementById('horas-luz-restantes');
    if (horasLuzElem && data.sol.horas_luz_restantes !== undefined) {
        const horas = Math.floor(data.sol.horas_luz_restantes);
        const minutos = Math.floor((data.sol.horas_luz_restantes - horas) * 60);
        horasLuzElem.textContent = `${horas}h ${minutos}m luz`;
    }
    
    // Amanecer/Anochecer
    const amanecerElem = document.getElementById('hora-amanecer');
    if (amanecerElem && data.sol.amanecer) {
        amanecerElem.textContent = data.sol.amanecer;
    }
    
    const anochecerElem = document.getElementById('hora-anochecer');
    if (anochecerElem && data.sol.anochecer) {
        anochecerElem.textContent = data.sol.anochecer;
    }
    
    // Fase lunar
    const faseLunarElem = document.getElementById('fase-lunar');
    if (faseLunarElem && data.luna.fase_nombre) {
        faseLunarElem.textContent = data.luna.fase_nombre;
    }
    
    // Salida/Puesta luna
    const salidaLunaElem = document.getElementById('hora-salida-luna');
    if (salidaLunaElem && data.luna.salida) {
        salidaLunaElem.textContent = data.luna.salida;
    }
    
    const puestaLunaElem = document.getElementById('hora-puesta-luna');
    if (puestaLunaElem && data.luna.puesta) {
        puestaLunaElem.textContent = data.luna.puesta;
    }
}

// ============================================================
// CAJONES LATERALES
// ============================================================

async function cargarCajones() {
    try {
        const response = await fetch(`${UI_API_BASE}/cajones`);
        const data = await response.json();
        estadoGlobal.cajones = data.cajones;
        
        renderizarCajones();
    } catch (error) {
        console.error('[Panel 2026] Error cargando cajones:', error);
    }
}

function renderizarCajones() {
    const cajonesIzq = document.getElementById('cajones-izquierda');
    const cajonesDer = document.getElementById('cajones-derecha');
    
    if (!cajonesIzq || !cajonesDer) return;
    
    cajonesIzq.innerHTML = '';
    cajonesDer.innerHTML = '';
    
    estadoGlobal.cajones.forEach((cajon, idx) => {
        const contenedor = idx % 2 === 0 ? cajonesIzq : cajonesDer;
        const cajonHtml = crearCajonHtml(cajon);
        contenedor.appendChild(cajonHtml);
    });
}

function crearCajonHtml(cajon) {
    const div = document.createElement('div');
    div.className = 'cajon';
    div.dataset.cajonId = cajon.id;
    
    // Tapa del cajón
    const tapa = document.createElement('div');
    tapa.className = 'cajon-tapa';
    tapa.innerHTML = `
        <span class="cajon-icono">${cajon.icono}</span>
        <span class="cajon-nombre">${cajon.nombre}</span>
    `;
    tapa.addEventListener('click', () => toggleCajon(cajon.id));
    
    // Contenido del cajón (colapsado por defecto)
    const contenido = document.createElement('div');
    contenido.className = 'cajon-contenido';
    contenido.style.display = 'none';
    
    if (cajon.valores_tapa && cajon.valores_tapa.length > 0) {
        cajon.valores_tapa.forEach(valor => {
            const valorDiv = document.createElement('div');
            valorDiv.className = 'cajon-valor';
            valorDiv.innerHTML = `
                <span class="valor-icono">${valor.icono || ''}</span>
                <span class="valor-nombre">${valor.nombre}</span>
                <span class="valor-dato">${formatearValor(valor.valor)} ${valor.unidad || ''}</span>
            `;
            valorDiv.addEventListener('click', () => abrirSubmenu(valor.nombre));
            contenido.appendChild(valorDiv);
        });
    }
    
    div.appendChild(tapa);
    div.appendChild(contenido);
    
    return div;
}

function toggleCajon(cajonId) {
    const cajon = document.querySelector(`[data-cajon-id="${cajonId}"]`);
    if (cajon) {
        const contenido = cajon.querySelector('.cajon-contenido');
        if (contenido) {
            contenido.style.display = contenido.style.display === 'none' ? 'block' : 'none';
        }
    }
}

async function abrirSubmenu(nombreValor) {
    try {
        const response = await fetch(`${UI_API_BASE}/submenu/${encodeURIComponent(nombreValor)}`);
        const data = await response.json();
        
        const overlay = document.getElementById('submenu-overlay');
        const contenido = document.getElementById('submenu-contenido');
        
        if (overlay && contenido) {
            contenido.innerHTML = `
                <h2>${data.nombre}</h2>
                <p><strong>Tipo:</strong> ${data.tipo}</p>
                <p><strong>Valor:</strong> ${formatearValor(data.valor)} ${data.unidad || ''}</p>
                <p><strong>Fiabilidad:</strong> ${data.fiabilidad}</p>
                <p><strong>Fórmula:</strong> ${data.formula || 'N/A'}</p>
                <p><strong>Estado:</strong> ${data.estado || 'N/A'}</p>
                <button onclick="cerrarSubmenu()">Cerrar</button>
            `;
            overlay.style.display = 'flex';
        }
    } catch (error) {
        console.error('[Panel 2026] Error abriendo submenú:', error);
    }
}

function cerrarSubmenu() {
    const overlay = document.getElementById('submenu-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ============================================================
// EVENTOS Y ACTUALIZACIÓN
// ============================================================

function configurarEventos() {
    // Botones de control
    const btnNoticias = document.getElementById('btn-noticias');
    if (btnNoticias) {
        btnNoticias.addEventListener('click', () => alert('Noticias: Funcionalidad pendiente'));
    }
    
    const btnAsistente = document.getElementById('btn-asistente');
    if (btnAsistente) {
        btnAsistente.addEventListener('click', () => alert('Asistente: Funcionalidad pendiente'));
    }
    
    const btnRestaurar = document.getElementById('btn-restaurar');
    if (btnRestaurar) {
        btnRestaurar.addEventListener('click', () => location.reload());
    }
    
    const btnConfiguracion = document.getElementById('btn-configuracion');
    if (btnConfiguracion) {
        btnConfiguracion.addEventListener('click', () => alert('Configuración: Funcionalidad pendiente'));
    }
    
    const btnFeedback = document.getElementById('btn-feedback');
    if (btnFeedback) {
        btnFeedback.addEventListener('click', () => alert('Feedback: Funcionalidad pendiente'));
    }
    
    // Cerrar submenú al hacer clic en el overlay
    const overlay = document.getElementById('submenu-overlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                cerrarSubmenu();
            }
        });
    }
}

function iniciarActualizaciones() {
    // Actualizar cada 10 segundos
    setInterval(() => {
        cargarPanelSuperior();
        cargarPanelCentral();
        cargarHorizonteHUD();  // ⚡ Actualizar Horizonte HUD
    }, 10000);
    
    // Actualizar cajones cada 30 segundos
    setInterval(() => {
        cargarCajones();
    }, 30000);
}

// ============================================================
// UTILIDADES DE FORMATO
// ============================================================

function formatearValor(valor, decimales = 1) {
    if (valor === null || valor === undefined) return '--';

    // Ley del Entero y Resolución de Diamante universal (2 decimales máximo, nunca 0.0 ni 0.0000)
    function diamondFormat(num, decs = 2) {
        if (typeof num !== 'number' || isNaN(num)) return '--';
        if (Math.abs(num) < 1e-8) return '0';
        if (Number.isInteger(num) || Math.abs(num - Math.round(num)) < 1e-8) return Math.round(num).toString();
        let txt = num.toFixed(decs);
        txt = txt.replace(/\.00$/, '');
        txt = txt.replace(/(\.\d)0$/, '$1');
        // Si tras redondear queda .00, quitarlo
        if (/\.0+$/.test(txt)) txt = txt.replace(/\.0+$/, '');
        return txt;
    }

    if (typeof valor === 'number') {
        return diamondFormat(valor, 2);
    }
    if (typeof valor === 'string' && /^-?\d+(\.\d+)?$/.test(valor.trim())) {
        const num = parseFloat(valor);
        return diamondFormat(num, 2);
    }
    return valor.toString();
}

function aplicarResolucionDiamante(uv) {
    if (uv === null || uv === undefined) return '--';
    
    // LEY DEL ENTERO: 2 decimales si tiene decimales, INT si es 0 o redondo
    if (uv === 0 || uv === Math.floor(uv)) {
        return Math.floor(uv).toString();
    } else {
        return uv.toFixed(2);
    }
}

// Exponer funciones globales
window.cerrarSubmenu = cerrarSubmenu;
window.toggleCajon = toggleCajon;

console.log('[Panel 2026] Script cargado correctamente');

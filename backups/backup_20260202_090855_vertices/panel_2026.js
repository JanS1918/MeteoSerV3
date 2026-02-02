// ⚡ PANEL_2026.JS - PANEL DE CONTROL MODERNIZADO - METEOSER V3
// ════════════════════════════════════════════════════════════════════════════
// Panel de Control de 2026: Elimina arcos gigantes obsoletos.
// Reemplazados por valores destacados, recomendación inteligente y tag de motor UV.
// ════════════════════════════════════════════════════════════════════════════

const PANEL_API_BASE = window.API_BASE || '/api/panel';
const UI_API_BASE = window.UI_API_BASE || '/api/ui';

let estadoGlobal = {
    cajones: [],
    panelSuperior: null,
    panelCentral: null
};

let animadorMeteo = null;
let cajonBloqueadoId = null;

function formatearCoord(valor) {
    if (valor === null || valor === undefined) return '0';
    const num = Number(valor);
    if (Number.isNaN(num)) return String(valor);
    return num.toString();
}

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
        const response = await fetch(`${PANEL_API_BASE}/superior`);
        const data = await response.json();
        estadoGlobal.panelSuperior = data;
        
        const latStr = formatearCoord(data.ubicacion.latitud);
        const lonStr = formatearCoord(data.ubicacion.longitud);
        document.getElementById('ubicacion-info').textContent = 
            `📍 ${data.ubicacion.poblacion} (${latStr}°, ${lonStr}°)`;

        const estacionIcono = obtenerIconoEstacion(data.estacion);
        document.getElementById('estacion-info').textContent = `${estacionIcono} ${data.estacion}`;
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
        const response = await fetch(`${PANEL_API_BASE}/central`);
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
        tempElem.textContent = formatearValor(valores.temperatura, 2);
        tempElem.onclick = () => abrirSubmenu('Temperatura');
        tempElem.classList.add('clickable');
    }
    
    // Humedad
    const humElem = document.getElementById('humedad-valor');
    if (humElem && valores.humedad !== undefined) {
        humElem.textContent = formatearValor(valores.humedad, 2);
        humElem.onclick = () => abrirSubmenu('Humedad');
        humElem.classList.add('clickable');
    }
    
    // Sensación térmica
    const sensElem = document.getElementById('sensacion-valor');
    if (sensElem && valores.sensacion !== undefined) {
        sensElem.textContent = formatearValor(valores.sensacion, 2);
        sensElem.onclick = () => abrirSubmenu('Sensación');
        sensElem.classList.add('clickable');
    }
}

function renderizarRecomendacion(recomendacion) {
    const recomElem = document.getElementById('recomendacion-texto');
    if (recomElem) {
        recomElem.textContent = recomendacion || 'Sin recomendaciones específicas';
        recomElem.onclick = () => abrirSubmenu('Recomendación');
        recomElem.classList.add('clickable');
    }
}

function renderizarValoresSecundarios(valores) {
    // Presión
    const presionElem = document.getElementById('presion-valor');
    if (presionElem && valores.presion !== undefined) {
        presionElem.textContent = formatearValor(valores.presion, 2);
        presionElem.onclick = () => abrirSubmenu('Presión');
        presionElem.classList.add('clickable');
    }
    
    // Viento
    const vientoElem = document.getElementById('viento-valor');
    if (vientoElem && valores.viento !== undefined) {
        vientoElem.textContent = formatearValor(valores.viento, 2);
        vientoElem.onclick = () => abrirSubmenu('Viento');
        vientoElem.classList.add('clickable');
    }

    const brujulaValor = document.getElementById('brujula-viento-valor');
    const brujulaFlecha = document.getElementById('brujula-flecha');
    if (brujulaValor && valores.viento !== undefined) {
        brujulaValor.textContent = formatearValor(valores.viento, 2);
        brujulaValor.onclick = () => abrirSubmenu('Viento');
        brujulaValor.classList.add('clickable');
    }
    if (brujulaFlecha) {
        const direccion = valores.direccion_viento ?? valores.viento_direccion ?? valores.direccion;
        if (direccion !== undefined && direccion !== null && !Number.isNaN(direccion)) {
            brujulaFlecha.style.transform = `rotate(${direccion}deg)`;
        }
    }
    
    // Elevación solar
    const elevacionElem = document.getElementById('elevacion-solar-valor');
    if (elevacionElem && valores.elevacion_solar !== undefined) {
        elevacionElem.textContent = formatearValor(valores.elevacion_solar, 2);
        elevacionElem.onclick = () => abrirSubmenu('Elevación solar');
        elevacionElem.classList.add('clickable');
    }
    
    // Índice UV con tag de motor
    const uvElem = document.getElementById('uv-indice-valor');
    const uvMotorTag = document.getElementById('uv-motor-tag');
    
    if (uvElem && valores.uv !== undefined) {
        uvElem.textContent = formatearValor(valores.uv, 2);
        uvElem.onclick = () => abrirSubmenu('Índice UV');
        uvElem.classList.add('clickable');
        
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
        const response = await fetch(`${PANEL_API_BASE}/arcos`);
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
    
    // Arco de trayectoria (horizonte a cenit) - viewBox 200x100
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 5 95 Q 100 5, 195 95');
    path.setAttribute('stroke', colorLinea);
    path.setAttribute('stroke-width', strokeWidth);
    path.setAttribute('fill', 'none');
    path.setAttribute('opacity', '0.6');
    svg.appendChild(path);
    
    // ⚡ POSICIÓN SOL: Kasten-Young precision
    // Normalizar posición: 0 (amanecer) → 0.5 (mediodía) → 1.0 (anochecer)
    const posicion = datosSol.posicion || 0.5;  // [0, 1]
    const posX = 5 + (195 - 5) * posicion;
    const posY = 95 - 85 * Math.sin(Math.PI * posicion);  // Parábola de elevación
    
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
        rayo.setAttribute('y2', '95');
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
    
    // Arco de trayectoria lunar - viewBox 200x100 (será invertido por CSS scaleY(-1))
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 5 95 Q 100 5, 195 95');
    path.setAttribute('stroke', colorLinea);
    path.setAttribute('stroke-width', strokeWidth);
    path.setAttribute('fill', 'none');
    path.setAttribute('opacity', '0.5');
    svg.appendChild(path);
    
    // ⚡ POSICIÓN LUNA: Tránsito astronómico
    const posicion = datosLuna.posicion || 0.5;
    const posX = 5 + (195 - 5) * posicion;
    const posY = 95 - 85 * Math.sin(Math.PI * posicion);
    
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
        horasLuzElem.onclick = () => abrirSubmenu('Horas de luz');
        horasLuzElem.classList.add('clickable');
    }
    
    // Amanecer/Anochecer
    const amanecerElem = document.getElementById('hora-amanecer');
    if (amanecerElem && data.sol.amanecer) {
        amanecerElem.textContent = data.sol.amanecer;
        amanecerElem.onclick = () => abrirSubmenu('Amanecer');
        amanecerElem.classList.add('clickable');
    }
    
    const anochecerElem = document.getElementById('hora-anochecer');
    if (anochecerElem && data.sol.anochecer) {
        anochecerElem.textContent = data.sol.anochecer;
        anochecerElem.onclick = () => abrirSubmenu('Anochecer');
        anochecerElem.classList.add('clickable');
    }
    
    // Horas en vértices del ojo
    const ojoAmanecerElem = document.getElementById('ojo-hora-amanecer');
    if (ojoAmanecerElem && data.sol.amanecer) {
        ojoAmanecerElem.textContent = data.sol.amanecer;
    }
    
    const ojoAnochecerElem = document.getElementById('ojo-hora-anochecer');
    if (ojoAnochecerElem && data.sol.anochecer) {
        ojoAnochecerElem.textContent = data.sol.anochecer;
    }
    
    // Fase lunar
    const faseLunarElem = document.getElementById('fase-lunar');
    if (faseLunarElem && data.luna.fase_nombre) {
        faseLunarElem.textContent = data.luna.fase_nombre;
        faseLunarElem.onclick = () => abrirSubmenu('Fase lunar');
        faseLunarElem.classList.add('clickable');
    }
    
    // Salida/Puesta luna
    const salidaLunaElem = document.getElementById('hora-salida-luna');
    if (salidaLunaElem && data.luna.salida) {
        salidaLunaElem.textContent = data.luna.salida;
        salidaLunaElem.onclick = () => abrirSubmenu('Salida lunar');
        salidaLunaElem.classList.add('clickable');
    }
    
    const puestaLunaElem = document.getElementById('hora-puesta-luna');
    if (puestaLunaElem && data.luna.puesta) {
        puestaLunaElem.textContent = data.luna.puesta;
        puestaLunaElem.onclick = () => abrirSubmenu('Puesta lunar');
        puestaLunaElem.classList.add('clickable');
    }
}

// ============================================================
// CAJONES LATERALES
// ============================================================

async function cargarCajones() {
    try {
        const response = await fetch(`${UI_API_BASE}/cajones`);
        const data = await response.json();
        estadoGlobal.cajones = Array.isArray(data.cajones) ? data.cajones : [];
        
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
    
    const cajonesRender = obtenerCajonesRender(estadoGlobal.cajones);
    cajonesRender.forEach((cajon, idx) => {
        const contenedor = idx < 5 ? cajonesIzq : cajonesDer;
        const cajonHtml = crearCajonHtml(cajon, idx + 1);
        contenedor.appendChild(cajonHtml);
    });
}

function obtenerCajonesRender(cajones) {
    if (Array.isArray(cajones) && cajones.length > 0) {
        const normalizados = cajones.slice(0, 10);
        if (normalizados.length < 10) {
            const faltan = 10 - normalizados.length;
            const placeholders = crearCajonesPlaceholder(faltan, normalizados.length);
            return normalizados.concat(placeholders);
        }
        return normalizados;
    }
    return crearCajonesPlaceholder(10, 0);
}

function crearCajonesPlaceholder(total, offset) {
    const nombres = [
        'Termodinámica',
        'Viento',
        'Biometría',
        'Precipitación',
        'Radiación',
        'Calidad del aire',
        'Sensores virtuales',
        'Predicciones',
        'Alertas y riesgos',
        'Índices misceláneos'
    ];
    return nombres.slice(offset, offset + total).map((nombre, idx) => ({
        id: `cajon_placeholder_${offset + idx}`,
        nombre,
        icono: '—',
        valores_tapa: [
            { nombre: '—', valor: 0, unidad: '' },
            { nombre: '—', valor: 0, unidad: '' }
        ],
        valores_completos: []
    }));
}

function crearCajonHtml(cajon, indice) {
    const div = document.createElement('div');
    div.className = 'cajon';
    div.dataset.cajonId = cajon.id;

    const valoresTapa = Array.isArray(cajon.valores_tapa)
        ? cajon.valores_tapa.slice(0, 2)
        : [];
    while (valoresTapa.length < 2) {
        valoresTapa.push({ nombre: '—', valor: 0, unidad: '' });
    }
    
    // Tapa del cajón
    const tapa = document.createElement('div');
    tapa.className = 'cajon-tapa';
    tapa.innerHTML = `
        <span class="cajon-indice">#${indice}</span>
        <span class="cajon-icono">${cajon.icono}</span>
        <span class="cajon-nombre">${cajon.nombre}</span>
        <span class="cajon-valores-tapa">
            ${valoresTapa.map(valor => `
                <span class="cajon-valor">
                    ${formatearValor(valor.valor)} ${valor.unidad || ''}
                </span>
            `).join('')}
        </span>
    `;
    tapa.addEventListener('mouseenter', () => mostrarCajonEnOverlay(cajon, false));
    tapa.addEventListener('mouseleave', () => {
        if (!cajonBloqueadoId) {
            cerrarSubmenu();
        }
    });
    tapa.addEventListener('click', (event) => {
        event.stopPropagation();
        cajonBloqueadoId = cajon.id;
        mostrarCajonEnOverlay(cajon, true);
    });
    
    // Contenido del cajón (colapsado por defecto vía CSS)
    const contenido = document.createElement('div');
    contenido.className = 'cajon-contenido';
    
    if (cajon.valores_tapa && cajon.valores_tapa.length > 0) {
        cajon.valores_tapa.forEach(valor => {
            const valorDiv = document.createElement('div');
            valorDiv.className = 'valor-item clickable';
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
    const cajon = estadoGlobal.cajones.find(item => item.id === cajonId);
    if (cajon) {
        cajonBloqueadoId = cajon.id;
        mostrarCajonEnOverlay(cajon, true);
    }
}

function mostrarCajonEnOverlay(cajon, bloquear) {
    const overlay = document.getElementById('submenu-overlay');
    const contenido = document.getElementById('submenu-contenido');
    if (!overlay || !contenido) return;

    const valores = (cajon.valores_completos && cajon.valores_completos.length > 0)
        ? cajon.valores_completos
        : (cajon.valores_tapa || []);

    contenido.innerHTML = `
        <h2>${cajon.icono || ''} ${cajon.nombre}</h2>
        <div class="cajon-overlay-valores">
            ${valores.map(valor => `
                <div class="valor-item clickable" data-nombre="${valor.nombre}">
                    <span class="valor-icono">${valor.icono || ''}</span>
                    <span class="valor-nombre">${valor.nombre}</span>
                    <span class="valor-dato">${formatearValor(valor.valor)} ${valor.unidad || ''}</span>
                </div>
            `).join('')}
        </div>
    `;

    contenido.querySelectorAll('[data-nombre]').forEach((item) => {
        item.addEventListener('click', () => abrirSubmenu(item.dataset.nombre));
    });

    overlay.style.display = 'flex';
    if (bloquear) {
        cajonBloqueadoId = cajon.id;
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
                <label class="campo-editable">Nombre
                    <input id="nombre-editable" type="text" value="${data.nombre || ''}" data-original="${data.nombre || ''}" />
                </label>
                <p><strong>Tipo:</strong> ${data.tipo}</p>
                <p><strong>Valor:</strong> ${formatearValor(data.valor)} ${data.unidad || ''}</p>
                <p><strong>Fiabilidad:</strong> ${data.fiabilidad}</p>
                <p><strong>Fórmula:</strong> ${data.formula || 'N/A'}</p>
                <p><strong>Sensores origen:</strong> ${(data.sensores_origen || []).join(', ')}</p>
                <p><strong>Dependencias:</strong> ${(data.dependencias || []).join(', ')}</p>
                ${Array.isArray(data.valores_usados) ? `<p><strong>Valores usados:</strong> ${data.valores_usados.join(', ')}</p>` : ''}
                <p><strong>Estado:</strong> ${data.estado || 'N/A'}</p>
                ${data.alerta ? `<p style="color: #ff6b6b;"><strong>Alerta:</strong> ${data.alerta}</p>` : ''}
                ${data.alerta && data.nombre_sensor ? `<button id="btn-eliminar-alerta" class="btn-control">Eliminar alerta</button>` : ''}
            `;
            overlay.style.display = 'flex';
            cajonBloqueadoId = null;

            const btnEliminar = document.getElementById('btn-eliminar-alerta');
            if (btnEliminar) {
                btnEliminar.addEventListener('click', async () => {
                    const confirmar = confirm('¿Está seguro de eliminar la alerta?');
                    if (!confirmar) return;
                    await fetch(`${UI_API_BASE}/fiabilidad/cerrar_alerta`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nombre_sensor: data.nombre_sensor })
                    });
                    cerrarSubmenu();
                });
            }
        }
    } catch (error) {
        console.error('[Panel 2026] Error abriendo submenú:', error);
    }
}

function cerrarSubmenu() {
    const overlay = document.getElementById('submenu-overlay');
    if (overlay) {
        const inputNombre = document.getElementById('nombre-editable');
        if (inputNombre && inputNombre.dataset.original !== undefined) {
            const nuevo = inputNombre.value.trim();
            const anterior = inputNombre.dataset.original;
            if (nuevo && nuevo !== anterior) {
                const confirmar = confirm('¿Está seguro de cambiar el nombre?');
                if (confirmar) {
                    fetch(`${UI_API_BASE}/auditoria/edicion`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            entidad: anterior,
                            campo: 'nombre',
                            valor_anterior: anterior,
                            valor_nuevo: nuevo,
                            usuario: 'usuario'
                        })
                    });
                }
            }
        }
        overlay.style.display = 'none';
    }
    cajonBloqueadoId = null;
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
    // Actualizar cada 20 segundos
    setInterval(() => {
        cargarPanelSuperior();
        cargarPanelCentral();
        cargarHorizonteHUD();  // ⚡ Actualizar Horizonte HUD
    }, 20000);
    
    // Actualizar cajones cada 60 segundos
    setInterval(() => {
        cargarCajones();
    }, 60000);
}

// ============================================================
// UTILIDADES DE FORMATO
// ============================================================

function formatearValor(valor, decimales = 2) {
    if (valor === null || valor === undefined || Number.isNaN(valor)) {
        return (0).toFixed(decimales);
    }
    if (typeof valor === 'number') {
        return valor.toFixed(decimales);
    }
    if (typeof valor === 'string' && /^-?\d+(\.\d+)?$/.test(valor.trim())) {
        const num = parseFloat(valor);
        return num.toFixed(decimales);
    }
    return valor.toString();
}

function obtenerIconoEstacion(estacion) {
    const nombre = (estacion || '').toLowerCase();
    if (nombre.includes('invierno')) return '❄️';
    if (nombre.includes('primavera')) return '🌸';
    if (nombre.includes('verano')) return '☀️';
    if (nombre.includes('otoño') || nombre.includes('otono')) return '🍂';
    return '🌡️';
}

function aplicarResolucionDiamante(uv) {
    if (uv === null || uv === undefined) return '0.00';
    return formatearValor(uv, 2);
}

// Exponer funciones globales
window.cerrarSubmenu = cerrarSubmenu;
window.toggleCajon = toggleCajon;

console.log('[Panel 2026] Script cargado correctamente');

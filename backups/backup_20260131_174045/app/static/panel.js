// panel.js
// Script para la nueva interfaz MeteoSer

// ============================================================
// CONFIGURACIÓN Y ESTADO GLOBAL
// ============================================================

const API_BASE = '/api/panel';
const UI_API_BASE = '/api/ui';
let estadoGlobal = {
    cajones: [],
    panelSuperior: null,
    arcos: null,
    panelCentral: null
};
let animadorMeteo = null;

// ============================================================
// INICIALIZACIÓN
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando panel MeteoSer...');
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
        console.error('AnimadorMeteorologico no está disponible');
    }
}

async function inicializarPanel() {
    try {
        await Promise.all([
            cargarPanelSuperior(),
            cargarArcosSolares(),
            cargarPanelCentral(),
            cargarCajones()
        ]);
        console.log('Panel inicializado correctamente');
    } catch (error) {
        console.error('Error inicializando panel:', error);
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
        console.error('Error cargando panel superior:', error);
    }
}

// ============================================================
// ARCOS SOLARES Y LUNARES
// ============================================================

async function cargarArcosSolares() {
    try {
        const response = await fetch(`${API_BASE}/arcos`);
        const data = await response.json();
        estadoGlobal.arcos = data;
        
        renderizarArcoSolar(data.sol);
        renderizarArcoLunar(data.luna);
        
        document.getElementById('duracion-dia').textContent = 
            `Duración del día: ${Math.floor(data.sol.duracion_dia / 60)}h ${Math.floor(data.sol.duracion_dia % 60)}m`;
        document.getElementById('duracion-noche').textContent = 
            `Duración de la noche: ${Math.floor(data.luna.duracion_noche / 60)}h ${Math.floor(data.luna.duracion_noche % 60)}m`;
    } catch (error) {
        console.error('Error cargando arcos:', error);
    }
}

function renderizarArcoSolar(datosSol) {
    const svg = document.getElementById('svg-arco-solar');
    svg.innerHTML = '';
    
    // Dibujar arco
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 50 130 Q 200 20, 350 130');
    path.setAttribute('stroke', '#ffd700');
    path.setAttribute('stroke-width', '4');
    path.setAttribute('fill', 'none');
    svg.appendChild(path);
    
    // Posición del sol
    const posX = 50 + (350 - 50) * datosSol.posicion;
    const posY = 130 - 110 * Math.sin(Math.PI * datosSol.posicion);
    
    // Icono del sol
    const sol = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    sol.setAttribute('cx', posX);
    sol.setAttribute('cy', posY);
    sol.setAttribute('r', datosSol.nublado ? '12' : '15');
    sol.setAttribute('fill', '#ffd700');
    svg.appendChild(sol);
    
    // Nubes si está nublado
    if (datosSol.nublado) {
        const nube = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
        nube.setAttribute('cx', posX);
        nube.setAttribute('cy', posY - 5);
        nube.setAttribute('rx', '20');
        nube.setAttribute('ry', '10');
        nube.setAttribute('fill', '#aaa');
        nube.setAttribute('opacity', '0.7');
        svg.appendChild(nube);
    }
    
    // Horas de amanecer y anochecer
    const textoAmanecer = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textoAmanecer.setAttribute('x', '50');
    textoAmanecer.setAttribute('y', '145');
    textoAmanecer.setAttribute('fill', '#ffd700');
    textoAmanecer.setAttribute('font-size', '12');
    textoAmanecer.textContent = datosSol.amanecer;
    svg.appendChild(textoAmanecer);
    
    const textoAnochecer = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textoAnochecer.setAttribute('x', '330');
    textoAnochecer.setAttribute('y', '145');
    textoAnochecer.setAttribute('fill', '#ffd700');
    textoAnochecer.setAttribute('font-size', '12');
    textoAnochecer.textContent = datosSol.anochecer;
    svg.appendChild(textoAnochecer);
}

function renderizarArcoLunar(datosLuna) {
    const svg = document.getElementById('svg-arco-lunar');
    svg.innerHTML = '';
    
    // Dibujar arco invertido
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M 50 20 Q 200 130, 350 20');
    path.setAttribute('stroke', '#4a90e2');
    path.setAttribute('stroke-width', '4');
    path.setAttribute('fill', 'none');
    svg.appendChild(path);
    
    // Posición de la luna (de derecha a izquierda)
    const posX = 350 - (350 - 50) * datosLuna.posicion;
    const posY = 20 + 110 * Math.sin(Math.PI * datosLuna.posicion);
    
    // Icono de la luna
    const luna = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    luna.setAttribute('cx', posX);
    luna.setAttribute('cy', posY);
    luna.setAttribute('r', '15');
    luna.setAttribute('fill', '#e0e0e0');
    svg.appendChild(luna);
    
    // Efecto de fase lunar (simplificado)
    if (datosLuna.fase < 0.5) {
        const sombra = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        sombra.setAttribute('cx', posX + (15 * (1 - 2 * datosLuna.fase)));
        sombra.setAttribute('cy', posY);
        sombra.setAttribute('r', '15');
        sombra.setAttribute('fill', '#1a1a2e');
        svg.appendChild(sombra);
    }
}

// ============================================================
// PANEL CENTRAL
// ============================================================

async function cargarPanelCentral() {
    try {
        const response = await fetch(`${API_BASE}/central`);
        const data = await response.json();
        estadoGlobal.panelCentral = data;
        
        renderizarPanelCentral(data);
    } catch (error) {
        console.error('Error cargando panel central:', error);
    }
}

function renderizarPanelCentral(data) {
    // Valores principales
    if (data.temperatura) {
        document.getElementById('temperatura-valor').textContent = 
            `🌡️ ${formatearValor(data.temperatura.valor, data.temperatura.unidad)}`;
    }
    if (data.humedad) {
        document.getElementById('humedad-valor').textContent = 
            `💧 ${formatearValor(data.humedad.valor, data.humedad.unidad)}`;
    }
    if (data.sensacion) {
        const texto = data.sensacion.unificado 
            ? `🏠 ${formatearValor(data.sensacion.edificio, '°C')}` 
            : `🏠 ${formatearValor(data.sensacion.edificio, '°C')} / 👤 ${formatearValor(data.sensacion.persona, '°C')}`;
        document.getElementById('sensacion-valor').textContent = texto;
    }
    
    // Recomendaciones
    if (data.recomendaciones) {
        document.getElementById('recomendacion-texto').textContent = data.recomendaciones.texto;
    }
    
    // Valores secundarios
    if (data.presion) {
        document.getElementById('presion-valor').textContent = 
            `🌡 ${formatearValor(data.presion.valor, data.presion.unidad)}`;
    }
    if (data.viento) {
        document.getElementById('viento-valor').textContent = 
            `💨 ${formatearValor(data.viento.valor, data.viento.unidad)}`;
    }
    
    // Actualizar animaciones meteorológicas
    if (animadorMeteo && data.estado_tiempo) {
        actualizarAnimaciones(data.estado_tiempo);
    }
}

function actualizarAnimaciones(estadoTiempo) {
    // Mapear estado meteorológico a tipo de animación
    let estadoAnimacion = 'despejado';
    
    // Detectar noche (simplificado, idealmente usar hora del día)
    const hora = new Date().getHours();
    const esNoche = hora < 6 || hora > 20;
    
    if (estadoTiempo.precipitacion) {
        if (estadoTiempo.precipitacion.tipo === 'nieve') {
            estadoAnimacion = 'nieve';
        } else if (estadoTiempo.precipitacion.intensidad === 'alta') {
            estadoAnimacion = 'lluvia_intensa';
        } else if (estadoTiempo.tormenta) {
            estadoAnimacion = 'tormenta';
        } else {
            estadoAnimacion = 'lluvia';
        }
    } else if (estadoTiempo.nubosidad) {
        if (estadoTiempo.nubosidad >= 70) {
            estadoAnimacion = 'nublado';
        } else if (estadoTiempo.nubosidad >= 30) {
            estadoAnimacion = 'parcialmente_nublado';
        } else if (esNoche) {
            estadoAnimacion = 'despejado_noche';
        }
    } else if (estadoTiempo.viento && estadoTiempo.viento >= 30) {
        estadoAnimacion = 'viento';
    } else if (esNoche) {
        estadoAnimacion = 'despejado_noche';
    }
    
    animadorMeteo.cambiarEstado(estadoAnimacion);
}

// ============================================================
// CAJONES LATERALES
// ============================================================

async function cargarCajones() {
    try {
        console.log('Solicitando cajones:', `${API_BASE}/cajones`);
        const response = await fetch(`${API_BASE}/cajones`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        estadoGlobal.cajones = data.cajones;
        
        renderizarCajones(Array.isArray(data.cajones) ? data.cajones : []);
    } catch (error) {
        console.error('Error cargando cajones:', error);
        renderizarCajones([]);
    }
}

function renderizarCajones(cajones) {
    const izquierda = document.getElementById('cajones-izquierda');
    const derecha = document.getElementById('cajones-derecha');
    
    izquierda.innerHTML = '';
    derecha.innerHTML = '';
    
    const cajonesFinales = cajones.length > 0 ? cajones : crearCajonesPlaceholder();
    cajonesFinales.forEach((cajon, index) => {
        const elemento = crearElementoCajon(cajon);
        if (index < 3) {
            izquierda.appendChild(elemento);
        } else {
            derecha.appendChild(elemento);
        }
    });
}

function crearCajonesPlaceholder() {
    const nombres = ['Termodinámica', 'Viento', 'Biometría', 'Precipitación', 'Radiación', 'Calidad Aire'];
    return nombres.map((nombre, idx) => ({
        id: `cajon_placeholder_${idx}`,
        nombre,
        icono: '—',
        prioridad: 0,
        valores_tapa: [{ nombre: '—', valor: '—', unidad: '' }],
        valores_completos: [],
        total_valores: 0
    }));
}

function crearElementoCajon(cajon) {
    const div = document.createElement('div');
    div.className = 'cajon';
    div.dataset.cajonId = cajon.id;
    
    // Tapa del cajón
    const tapa = document.createElement('div');
    tapa.className = 'cajon-tapa';
    
    const nombre = document.createElement('span');
    nombre.className = 'cajon-nombre';
    nombre.textContent = cajon.nombre;
    
    const valoresTapa = document.createElement('div');
    valoresTapa.className = 'cajon-valores-tapa';
    (cajon.valores_tapa || []).forEach(valor => {
        const span = document.createElement('span');
        span.textContent = formatearValor(valor.valor, valor.unidad);
        valoresTapa.appendChild(span);
    });
    
    tapa.appendChild(nombre);
    tapa.appendChild(valoresTapa);
    
    // Contenido del cajón
    const contenido = document.createElement('div');
    contenido.className = 'cajon-contenido';
    
    (cajon.valores_completos || []).forEach(valor => {
        const item = document.createElement('div');
        item.className = 'valor-item';
        item.textContent = `${valor.nombre}: ${formatearValor(valor.valor, valor.unidad)}`;
        item.onclick = () => abrirSubmenuValor(valor.nombre);
        contenido.appendChild(item);
    });
    
    div.appendChild(tapa);
    div.appendChild(contenido);
    
    // Eventos
    tapa.onclick = () => toggleCajon(div);
    
    return div;
}

function toggleCajon(cajonElement) {
    cajonElement.classList.toggle('abierto');
}

function formatearValor(valor, unidad = '') {
    if (valor === null || valor === undefined || Number.isNaN(valor)) {
        return `—${unidad}`.trim();
    }
    return `${valor}${unidad}`.trim();
}

// ============================================================
// SUBMENÚS
// ============================================================

async function abrirSubmenuValor(nombreValor) {
    try {
        const response = await fetch(`${API_BASE}/submenu/${encodeURIComponent(nombreValor)}`);
        const data = await response.json();
        
        mostrarSubmenu(data);
    } catch (error) {
        console.error('Error abriendo submenú:', error);
    }
}

function mostrarSubmenu(data) {
    const overlay = document.getElementById('submenu-overlay');
    const contenido = document.getElementById('submenu-contenido');
    
    contenido.innerHTML = `
        <h2>${data.nombre}</h2>
        <p><strong>Tipo:</strong> ${data.tipo}</p>
        <p><strong>Valor:</strong> ${data.valor} ${data.unidad}</p>
        <p><strong>Fiabilidad:</strong> ${data.fiabilidad}</p>
        <p><strong>Fórmula:</strong> ${data.formula}</p>
        <p><strong>Sensores origen:</strong> ${data.sensores_origen.join(', ')}</p>
        <p><strong>Dependencias:</strong> ${data.dependencias.join(', ')}</p>
        <p><strong>Estado:</strong> ${data.estado}</p>
        ${data.alerta ? `<p style="color: #ff6b6b;"><strong>Alerta:</strong> ${data.alerta}</p>` : ''}
    `;
    
    overlay.style.display = 'flex';
}

function cerrarSubmenu() {
    document.getElementById('submenu-overlay').style.display = 'none';
}

// ============================================================
// CONFIGURACIÓN DE EVENTOS
// ============================================================

function configurarEventos() {
    // Cerrar submenú al clicar fuera
    document.getElementById('submenu-overlay').onclick = function(e) {
        if (e.target === this) {
            cerrarSubmenu();
        }
    };
    
    // Botones de control (requieren botones_control.js)
    document.getElementById('btn-noticias').onclick = () => abrirNoticias();
    document.getElementById('btn-asistente').onclick = () => abrirAsistentePersonal();
    document.getElementById('btn-restaurar').onclick = () => abrirRestaurar();
    document.getElementById('btn-configuracion').onclick = () => abrirConfiguracion();
    document.getElementById('btn-feedback').onclick = () => abrirFeedback();
}

// ============================================================
// ACTUALIZACIONES PERIÓDICAS
// ============================================================

function iniciarActualizaciones() {
    // Actualizar cada 30 segundos
    setInterval(async () => {
        await cargarPanelSuperior();
        await cargarArcosSolares();
        await cargarPanelCentral();
        await cargarCajones();
    }, 30000);
    
    // Actualizar hora cada segundo
    setInterval(() => {
        const ahora = new Date();
        document.getElementById('hora-actual').textContent = 
            `🕐 ${ahora.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}`;
    }, 1000);
}

// ============================================================
// ANIMACIONES METEOROLÓGICAS (placeholder)
// ============================================================

// TODO: Implementar animaciones de lluvia, sol, viento, etc.
// usando el canvas #canvas-animaciones

console.log('Panel.js cargado correctamente');

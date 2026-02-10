// ══════════════════════════════════════════════════════════════════════════
// METEOSER V3 - PUZZLE.JS - JAVASCRIPT PROFESIONAL Y COMPLETO
// ══════════════════════════════════════════════════════════════════════════

// ═══ CONFIGURACIÓN Y CONSTANTES ═══
const API_BASE = '/api/ui';
const ICONOS_CAJONES = {
    '🌡️': ['temperatura', 'temp', 'térmica'],
    '💧': ['humedad', 'agua', 'rocío'],
    '🌪️': ['viento', 'ráfaga', 'brisa'],
    '☀️': ['solar', 'radiación', 'uv'],
    '🧭': ['presión', 'barométrica', 'atmosférica']
};

let datosGlobales = null;
let animadorMeteo = null;

// ═══ UTILIDADES ═══
function fmt(valor, decimales = 2) {
    if (valor === null || valor === undefined || isNaN(valor)) return '—';
    if (typeof valor === 'number') {
        return valor.toFixed(decimales);
    }
    const num = parseFloat(valor);
    return isNaN(num) ? String(valor) : num.toFixed(decimales);
}

function obtenerIconoCajon(nombreCajon) {
    const nombreLower = nombreCajon.toLowerCase();
    for (const [icono, palabras] of Object.entries(ICONOS_CAJONES)) {
        if (palabras.some(p => nombreLower.includes(p))) {
            return icono;
        }
    }
    return '📊';
}

// ═══ FUNCIONES DE FETCH ═══
async function fetchJSON(url) {
    try {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' }
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (error) {
        console.error(`Error al hacer fetch a ${url}:`, error);
        return null;
    }
}

async function cargarCajones() {
    const data = await fetchJSON(`${API_BASE}/cajones`);
    if (!data || !data.cajones) {
        console.error('No se pudieron cargar los cajones');
        return;
    }
    
    datosGlobales = data;
    renderizarCajones(data.cajones);
    renderizarSidebar(data.cajones);
}

async function cargarPanelSuperior() {
    const data = await fetchJSON(`${API_BASE}/panel/superior`);
    if (!data) return;
    
    // Actualizar ubicación con 4 decimales
    if (data.ubicacion) {
        document.getElementById('ubicacion-texto').textContent = data.ubicacion.nombre || 'Ubicación desconocida';
        if (data.ubicacion.latitud && data.ubicacion.longitud) {
            const lat = parseFloat(data.ubicacion.latitud).toFixed(4);
            const lon = parseFloat(data.ubicacion.longitud).toFixed(4);
            document.getElementById('coordenadas').textContent = `${lat}, ${lon}`;
        }
    }
    
    // Actualizar estado del sistema
    document.getElementById('estado-sistema').textContent = data.estado || 'Sistema operativo';
    document.getElementById('hora-actualizacion').textContent = data.ultima_actualizacion || new Date().toLocaleTimeString('es-ES');
}

async function cargarSubmenu(nombreValor) {
    const data = await fetchJSON(`${API_BASE}/submenu/${encodeURIComponent(nombreValor)}`);
    if (!data) {
        mostrarModal('Error', '<p>No se pudo cargar el submenú</p>');
        return;
    }
    
    let html = `<h2>${nombreValor}</h2><div class="submenu-lista">`;
    
    if (data.detalles && Array.isArray(data.detalles)) {
        data.detalles.forEach(item => {
            html += `
                <div class="submenu-item">
                    <div class="submenu-item-nombre">${item.nombre}</div>
                    <div class="submenu-item-valor">${fmt(item.valor, 2)} ${item.unidad || ''}</div>
                    ${item.descripcion ? `<div class="submenu-item-desc">${item.descripcion}</div>` : ''}
                </div>
            `;
        });
    } else {
        html += '<p>No hay información adicional disponible</p>';
    }
    
    html += '</div>';
    mostrarModal(nombreValor, html);
}

// ═══ RENDERIZADO DE UI ═══
function renderizarCajones(cajones) {
    const container = document.getElementById('cajones-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Limitar a 5 cajones
    const cajonesLimitados = cajones.slice(0, 5);
    
    cajonesLimitados.forEach((cajon, idx) => {
        const div = document.createElement('div');
        div.className = 'cajon';
        div.dataset.cajonId = idx;
        
        const icono = obtenerIconoCajon(cajon.nombre);
        
        let portadaHTML = '';
        if (cajon.indices && cajon.indices.length > 0) {
            portadaHTML = '<div class="cajon-portada">';
            cajon.indices.slice(0, 3).forEach(indice => {
                portadaHTML += `
                    <div class="portada-indice">
                        <span class="portada-indice-nombre">${indice.nombre}</span>
                        <span class="portada-indice-valor">${fmt(indice.valor, 2)} ${indice.unidad || ''}</span>
                    </div>
                `;
            });
            portadaHTML += '</div>';
        }
        
        let valoresHTML = '<div class="cajon-valores">';
        if (cajon.valores && cajon.valores.length > 0) {
            cajon.valores.forEach(valor => {
                valoresHTML += `
                    <div class="valor-item" data-valor-nombre="${valor.nombre}">
                        <span class="valor-nombre">${valor.nombre}</span>
                        <span class="valor-dato">${fmt(valor.valor, 2)} ${valor.unidad || ''}</span>
                    </div>
                `;
            });
        }
        valoresHTML += '</div>';
        
        div.innerHTML = `
            <div class="cajon-header">
                <div class="cajon-titulo">${cajon.nombre}</div>
                <div class="cajon-icono">${icono}</div>
            </div>
            ${portadaHTML}
            ${valoresHTML}
        `;
        
        container.appendChild(div);
    });
    
    // Añadir event listeners a valores clickables
    document.querySelectorAll('.valor-item').forEach(el => {
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            const nombreValor = el.dataset.valorNombre;
            if (nombreValor) {
                cargarSubmenu(nombreValor);
            }
        });
    });
}

function renderizarSidebar(cajones) {
    const sidebar = document.getElementById('sidebar-cajones');
    if (!sidebar) return;
    
    sidebar.innerHTML = '';
    
    // Limitar a 5 cajones
    const cajonesLimitados = cajones.slice(0, 5);
    
    cajonesLimitados.forEach((cajon, idx) => {
        const div = document.createElement('div');
        div.className = 'sidebar-cajon';
        div.dataset.sidebarId = idx;
        
        const icono = obtenerIconoCajon(cajon.nombre);
        
        let contenidoHTML = '<div class="sidebar-contenido">';
        if (cajon.valores && cajon.valores.length > 0) {
            cajon.valores.slice(0, 5).forEach(valor => {
                contenidoHTML += `
                    <div class="sidebar-valor">
                        ${valor.nombre}: ${fmt(valor.valor, 2)} ${valor.unidad || ''}
                    </div>
                `;
            });
        }
        contenidoHTML += '</div>';
        
        div.innerHTML = `
            <div class="sidebar-icono">${icono}</div>
            <div class="sidebar-titulo">${cajon.nombre}</div>
            ${contenidoHTML}
        `;
        
        // Click para expandir/contraer
        div.addEventListener('click', () => {
            // Contraer todos los demás
            document.querySelectorAll('.sidebar-cajon').forEach(el => {
                if (el !== div) el.classList.remove('expandido');
            });
            // Toggle este
            div.classList.toggle('expandido');
        });
        
        sidebar.appendChild(div);
    });
}

// ═══ MODAL ═══
function mostrarModal(titulo, contenidoHTML) {
    const overlay = document.getElementById('modal-overlay');
    const body = document.getElementById('modal-body');
    
    if (!overlay || !body) return;
    
    body.innerHTML = contenidoHTML;
    overlay.classList.add('activo');
}

function cerrarModal() {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) {
        overlay.classList.remove('activo');
    }
}

// ═══ ANIMACIONES METEOROLÓGICAS ═══
class AnimadorMeteorologico {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d', { desynchronized: true });
        this.particulas = [];
        this.estadoActual = 'despejado';
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        this.animar();
    }
    
    resize() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    crearLluvia() {
        for (let i = 0; i < 5; i++) {
            this.particulas.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height - this.canvas.height,
                velocidad: 5 + Math.random() * 3,
                largo: 10 + Math.random() * 10,
                tipo: 'lluvia'
            });
        }
    }
    
    crearNieve() {
        for (let i = 0; i < 3; i++) {
            this.particulas.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height - this.canvas.height,
                velocidad: 1 + Math.random() * 2,
                radio: 2 + Math.random() * 3,
                vx: (Math.random() - 0.5) * 0.5,
                tipo: 'nieve'
            });
        }
    }
    
    crearNube() {
        if (this.particulas.filter(p => p.tipo === 'nube').length < 3) {
            this.particulas.push({
                x: -200,
                y: 50 + Math.random() * 150,
                velocidad: 0.3 + Math.random() * 0.5,
                radio: 60 + Math.random() * 40,
                tipo: 'nube'
            });
        }
    }
    
    actualizar() {
        // Crear nuevas partículas según el estado
        if (this.estadoActual === 'lluvia' || this.estadoActual === 'tormenta') {
            this.crearLluvia();
        } else if (this.estadoActual === 'nieve') {
            this.crearNieve();
        } else if (this.estadoActual === 'nublado') {
            this.crearNube();
        }
        
        // Actualizar particulas existentes
        this.particulas = this.particulas.filter(p => {
            if (p.tipo === 'lluvia') {
                p.y += p.velocidad;
                return p.y < this.canvas.height;
            } else if (p.tipo === 'nieve') {
                p.y += p.velocidad;
                p.x += p.vx;
                return p.y < this.canvas.height;
            } else if (p.tipo === 'nube') {
                p.x += p.velocidad;
                return p.x < this.canvas.width + 200;
            }
            return false;
        });
    }
    
    dibujar() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particulas.forEach(p => {
            if (p.tipo === 'lluvia') {
                this.ctx.strokeStyle = 'rgba(174, 194, 224, 0.6)';
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.moveTo(p.x, p.y);
                this.ctx.lineTo(p.x, p.y + p.largo);
                this.ctx.stroke();
            } else if (p.tipo === 'nieve') {
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.radio, 0, Math.PI * 2);
                this.ctx.fill();
            } else if (p.tipo === 'nube') {
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.radio, 0, Math.PI * 2);
                this.ctx.arc(p.x + p.radio * 0.7, p.y, p.radio * 0.8, 0, Math.PI * 2);
                this.ctx.arc(p.x + p.radio * 1.5, p.y, p.radio * 0.9, 0, Math.PI * 2);
                this.ctx.fill();
            }
        });
    }
    
    animar() {
        this.actualizar();
        this.dibujar();
        requestAnimationFrame(() => this.animar());
    }
    
    cambiarEstado(nuevoEstado) {
        this.estadoActual = nuevoEstado;
    }
}

// ═══ INICIALIZACIÓN ═══
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar animador
    animadorMeteo = new AnimadorMeteorologico('canvas-animaciones');
    
    // Cargar datos
    cargarPanelSuperior();
    cargarCajones();
    
    // Actualizar periódicamente
    setInterval(() => {
        cargarPanelSuperior();
        cargarCajones();
    }, 15000);
    
    // Event listeners del modal
    const modalClose = document.getElementById('modal-close');
    const modalOverlay = document.getElementById('modal-overlay');
    
    if (modalClose) {
        modalClose.addEventListener('click', cerrarModal);
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                cerrarModal();
            }
        });
    }
});

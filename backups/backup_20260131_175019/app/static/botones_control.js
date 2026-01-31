/**
 * Lógica de los botones de control del panel
 * Noticias, Asistente Personal, Restaurar, Configuración, Feedback
 */

// ============================================================
// NOTICIAS
// ============================================================

function abrirNoticias() {
    const modal = crearModal('Noticias del Sistema');
    
    fetch('/api/ui/noticias')
        .then(res => res.json())
        .then(data => {
            const noticias = data.noticias || [];
            let html = '<div class="noticias-container">';
            
            if (noticias.length === 0) {
                html += '<p class="sin-datos">No hay noticias recientes</p>';
            } else {
                noticias.forEach(noticia => {
                    const icono = obtenerIconoNoticia(noticia.tipo);
                    html += `
                        <div class="noticia-item tipo-${noticia.tipo}">
                            <span class="noticia-icono">${icono}</span>
                            <div class="noticia-contenido">
                                <p class="noticia-texto">${noticia.texto}</p>
                                <span class="noticia-fecha">${noticia.fecha}</span>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            modal.querySelector('.modal-body').innerHTML = html;
        })
        .catch(err => {
            console.error('Error cargando noticias:', err);
            modal.querySelector('.modal-body').innerHTML = 
                '<p class="error">Error al cargar noticias</p>';
        });
}

function obtenerIconoNoticia(tipo) {
    const iconos = {
        'alerta': '⚠️',
        'info': 'ℹ️',
        'exito': '✅',
        'warning': '⚡',
        'error': '❌'
    };
    return iconos[tipo] || 'ℹ️';
}

// ============================================================
// ASISTENTE PERSONAL
// ============================================================

function abrirAsistentePersonal() {
    const modal = crearModal('Asistente Personal MeteoSer');
    
    const html = `
        <div class="asistente-container">
            <div class="asistente-menu">
                <button class="asistente-btn" onclick="consultarAsistente('clima')">
                    🌤️ Predicción del tiempo
                </button>
                <button class="asistente-btn" onclick="consultarAsistente('consejos')">
                    💡 Consejos personalizados
                </button>
                <button class="asistente-btn" onclick="consultarAsistente('alertas')">
                    ⚠️ Alertas configuradas
                </button>
                <button class="asistente-btn" onclick="consultarAsistente('historial')">
                    📊 Historial y tendencias
                </button>
                <button class="asistente-btn" onclick="consultarAsistente('optimizacion')">
                    ⚙️ Optimización del sistema
                </button>
            </div>
            <div id="asistente-respuesta" class="asistente-respuesta">
                <p class="placeholder">Selecciona una opción del menú</p>
            </div>
        </div>
    `;
    
    modal.querySelector('.modal-body').innerHTML = html;
}

function consultarAsistente(tema) {
    const respuestaDiv = document.getElementById('asistente-respuesta');
    respuestaDiv.innerHTML = '<div class="loading">⏳ Consultando...</div>';
    
    fetch(`/api/ui/asistente?tema=${tema}`)
        .then(res => res.json())
        .then(data => {
            let html = '<div class="asistente-resultado">';
            html += `<h3>${data.titulo}</h3>`;
            html += `<p>${data.respuesta}</p>`;
            
            if (data.detalles && data.detalles.length > 0) {
                html += '<ul class="detalles-lista">';
                data.detalles.forEach(detalle => {
                    html += `<li>${detalle}</li>`;
                });
                html += '</ul>';
            }
            
            if (data.acciones && data.acciones.length > 0) {
                html += '<div class="acciones-sugeridas">';
                data.acciones.forEach(accion => {
                    html += `<button class="accion-btn" onclick="${accion.handler}">${accion.texto}</button>`;
                });
                html += '</div>';
            }
            
            html += '</div>';
            respuestaDiv.innerHTML = html;
        })
        .catch(err => {
            console.error('Error consultando asistente:', err);
            respuestaDiv.innerHTML = '<p class="error">Error al consultar el asistente</p>';
        });
}

// ============================================================
// RESTAURAR
// ============================================================

function abrirRestaurar() {
    const modal = crearModal('Restaurar Cambios');
    
    fetch('/api/ui/auditoria/historial?tipo=movimiento&limite=20')
        .then(res => res.json())
        .then(data => {
            const movimientos = data.historial || [];
            let html = '<div class="restaurar-container">';
            
            if (movimientos.length === 0) {
                html += '<p class="sin-datos">No hay movimientos para restaurar</p>';
            } else {
                html += '<p class="info">Selecciona los movimientos que deseas restaurar:</p>';
                html += '<div class="movimientos-lista">';
                
                movimientos.forEach(mov => {
                    html += `
                        <div class="movimiento-item">
                            <input type="checkbox" id="mov-${mov.id}" value="${mov.id}">
                            <label for="mov-${mov.id}">
                                <strong>${mov.valor_nombre}</strong>: 
                                ${mov.desde_cajon} → ${mov.hacia_cajon}
                                <span class="fecha">${mov.fecha}</span>
                            </label>
                        </div>
                    `;
                });
                
                html += '</div>';
                html += '<button class="btn-restaurar" onclick="ejecutarRestaurar()">Restaurar seleccionados</button>';
            }
            
            html += '</div>';
            modal.querySelector('.modal-body').innerHTML = html;
        })
        .catch(err => {
            console.error('Error cargando historial:', err);
            modal.querySelector('.modal-body').innerHTML = 
                '<p class="error">Error al cargar historial de movimientos</p>';
        });
}

function ejecutarRestaurar() {
    const checkboxes = document.querySelectorAll('.movimiento-item input[type="checkbox"]:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) {
        alert('Selecciona al menos un movimiento para restaurar');
        return;
    }
    
    fetch('/api/ui/auditoria/restaurar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ids_movimiento: ids})
    })
    .then(res => res.json())
    .then(data => {
        if (data.exito) {
            alert(`Restaurados ${data.restaurados} movimientos`);
            cerrarModal();
            // Recargar cajones
            cargarCajones();
        } else {
            alert('Error al restaurar: ' + data.error);
        }
    })
    .catch(err => {
        console.error('Error restaurando:', err);
        alert('Error al restaurar movimientos');
    });
}

// ============================================================
// CONFIGURACIÓN
// ============================================================

function abrirConfiguracion() {
    const modal = crearModal('Configuración del Sistema');
    
    const html = `
        <div class="configuracion-container">
            <div class="config-seccion">
                <h3>Ubicación</h3>
                <label>Latitud: <input type="number" id="config-lat" step="0.0001"></label>
                <label>Longitud: <input type="number" id="config-lon" step="0.0001"></label>
                <button onclick="guardarUbicacion()">Guardar ubicación</button>
            </div>
            
            <div class="config-seccion">
                <h3>Unidades de medida</h3>
                <label>
                    Temperatura:
                    <select id="config-temp-unit">
                        <option value="C">Celsius (°C)</option>
                        <option value="F">Fahrenheit (°F)</option>
                        <option value="K">Kelvin (K)</option>
                    </select>
                </label>
                <label>
                    Presión:
                    <select id="config-presion-unit">
                        <option value="hPa">Hectopascales (hPa)</option>
                        <option value="mmHg">Milímetros de mercurio (mmHg)</option>
                        <option value="inHg">Pulgadas de mercurio (inHg)</option>
                    </select>
                </label>
                <button onclick="guardarUnidades()">Guardar unidades</button>
            </div>
            
            <div class="config-seccion">
                <h3>Actualización automática</h3>
                <label>
                    Intervalo (segundos):
                    <input type="number" id="config-intervalo" min="5" max="300" value="30">
                </label>
                <button onclick="guardarIntervalo()">Guardar intervalo</button>
            </div>
            
            <div class="config-seccion">
                <h3>Escala de pantalla</h3>
                <label>
                    Zoom (%):
                    <input type="range" id="config-zoom" min="80" max="150" value="100" step="5" oninput="aplicarZoom(this.value)">
                    <span id="zoom-valor">100%</span>
                </label>
            </div>
        </div>
    `;
    
    modal.querySelector('.modal-body').innerHTML = html;
    
    // Cargar configuración actual
    cargarConfiguracionActual();
}

function cargarConfiguracionActual() {
    // Implementar carga de configuración desde el backend
    console.log('Cargando configuración actual...');
}

function guardarUbicacion() {
    const lat = document.getElementById('config-lat').value;
    const lon = document.getElementById('config-lon').value;
    
    fetch('/api/ui/configuracion/ubicacion', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({latitud: parseFloat(lat), longitud: parseFloat(lon)})
    })
    .then(res => res.json())
    .then(data => {
        if (data.exito) {
            alert('Ubicación guardada correctamente');
            location.reload();
        }
    })
    .catch(err => console.error('Error guardando ubicación:', err));
}

function guardarUnidades() {
    const tempUnit = document.getElementById('config-temp-unit').value;
    const presionUnit = document.getElementById('config-presion-unit').value;
    
    console.log('Guardando unidades:', tempUnit, presionUnit);
    // Implementar guardado de unidades
}

function guardarIntervalo() {
    const intervalo = document.getElementById('config-intervalo').value;
    console.log('Guardando intervalo:', intervalo);
    // Implementar cambio de intervalo de actualización
}

function aplicarZoom(valor) {
    document.getElementById('zoom-valor').textContent = valor + '%';
    document.body.style.transform = `scale(${valor / 100})`;
    document.body.style.transformOrigin = 'top left';
}

// ============================================================
// FEEDBACK
// ============================================================

function abrirFeedback() {
    const modal = crearModal('Enviar Feedback');
    
    const html = `
        <div class="feedback-container">
            <p>Ayúdanos a mejorar MeteoSer con tu opinión sobre los valores mostrados:</p>
            
            <div class="feedback-form">
                <label>
                    Valor:
                    <select id="feedback-valor">
                        <option value="">Selecciona un valor...</option>
                        <option value="temperatura">Temperatura</option>
                        <option value="humedad">Humedad</option>
                        <option value="presion">Presión</option>
                        <option value="viento">Viento</option>
                        <option value="utci">UTCI (Sensación térmica)</option>
                    </select>
                </label>
                
                <label>
                    ¿El valor es correcto?
                    <select id="feedback-correcto">
                        <option value="si">Sí, es correcto</option>
                        <option value="no">No, es incorrecto</option>
                    </select>
                </label>
                
                <div id="feedback-correccion" style="display: none;">
                    <label>
                        Valor correcto (opcional):
                        <input type="number" id="feedback-valor-real" step="0.1">
                    </label>
                </div>
                
                <label>
                    Comentarios adicionales:
                    <textarea id="feedback-comentarios" rows="4"></textarea>
                </label>
                
                <button class="btn-enviar" onclick="enviarFeedback()">Enviar feedback</button>
            </div>
        </div>
    `;
    
    modal.querySelector('.modal-body').innerHTML = html;
    
    // Mostrar campo de corrección si el valor es incorrecto
    document.getElementById('feedback-correcto').addEventListener('change', function() {
        const correccionDiv = document.getElementById('feedback-correccion');
        correccionDiv.style.display = this.value === 'no' ? 'block' : 'none';
    });
}

function enviarFeedback() {
    const valor = document.getElementById('feedback-valor').value;
    const correcto = document.getElementById('feedback-correcto').value === 'si';
    const valorReal = parseFloat(document.getElementById('feedback-valor-real').value) || null;
    const comentarios = document.getElementById('feedback-comentarios').value;
    
    if (!valor) {
        alert('Selecciona un valor para enviar feedback');
        return;
    }
    
    const payload = {
        valor_nombre: valor,
        correcto: correcto,
        valor_real: valorReal,
        comentarios: comentarios
    };
    
    fetch('/api/ui/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.exito) {
            alert('¡Gracias por tu feedback! Confianza actual: ' + (data.confianza_actual * 100).toFixed(1) + '%');
            cerrarModal();
        } else {
            alert('Error al enviar feedback');
        }
    })
    .catch(err => {
        console.error('Error enviando feedback:', err);
        alert('Error al enviar feedback');
    });
}

// ============================================================
// UTILIDADES DE MODAL
// ============================================================

function crearModal(titulo) {
    // Remover modal existente si lo hay
    const existente = document.getElementById('modal-control');
    if (existente) {
        existente.remove();
    }
    
    const modal = document.createElement('div');
    modal.id = 'modal-control';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-contenido">
            <div class="modal-header">
                <h2>${titulo}</h2>
                <button class="btn-cerrar" onclick="cerrarModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="loading">Cargando...</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Cerrar al hacer clic fuera del modal
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            cerrarModal();
        }
    });
    
    return modal;
}

function cerrarModal() {
    const modal = document.getElementById('modal-control');
    if (modal) {
        modal.remove();
    }
}

// Exportar funciones para uso global
window.abrirNoticias = abrirNoticias;
window.abrirAsistentePersonal = abrirAsistentePersonal;
window.abrirRestaurar = abrirRestaurar;
window.abrirConfiguracion = abrirConfiguracion;
window.abrirFeedback = abrirFeedback;
window.consultarAsistente = consultarAsistente;
window.ejecutarRestaurar = ejecutarRestaurar;
window.guardarUbicacion = guardarUbicacion;
window.guardarUnidades = guardarUnidades;
window.guardarIntervalo = guardarIntervalo;
window.aplicarZoom = aplicarZoom;
window.enviarFeedback = enviarFeedback;
window.cerrarModal = cerrarModal;

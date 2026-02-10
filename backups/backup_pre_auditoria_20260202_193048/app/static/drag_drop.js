/**
 * Sistema de Drag & Drop para MeteoSer V3
 * Permite reorganizar cajones y valores mediante arrastrar y soltar
 */

let draggedElement = null;
let draggedType = null; // 'cajon' o 'valor'

function inicializarDragDrop() {
    console.log('[Drag&Drop] Inicializando sistema...');
    
    // Observer para detectar nuevos cajones y valores
    const observer = new MutationObserver(() => {
        habilitarDragDropEnCajones();
        habilitarDragDropEnValores();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Habilitar inmediatamente
    habilitarDragDropEnCajones();
    habilitarDragDropEnValores();
}

function habilitarDragDropEnCajones() {
    const cajones = document.querySelectorAll('.cajon:not([draggable])');
    cajones.forEach(cajon => {
        cajon.setAttribute('draggable', 'true');
        
        cajon.addEventListener('dragstart', (e) => {
            draggedElement = cajon;
            draggedType = 'cajon';
            cajon.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            console.log('[Drag&Drop] Arrastrando cajón:', cajon.dataset.cajonId);
        });
        
        cajon.addEventListener('dragend', (e) => {
            cajon.classList.remove('dragging');
            document.querySelectorAll('.drag-over').forEach(el => {
                el.classList.remove('drag-over');
            });
            draggedElement = null;
            draggedType = null;
        });
        
        cajon.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (draggedType === 'cajon' && draggedElement !== cajon) {
                cajon.classList.add('drag-over');
            }
        });
        
        cajon.addEventListener('dragleave', (e) => {
            cajon.classList.remove('drag-over');
        });
        
        cajon.addEventListener('drop', (e) => {
            e.preventDefault();
            cajon.classList.remove('drag-over');
            
            if (draggedType === 'cajon' && draggedElement !== cajon) {
                intercambiarCajones(draggedElement, cajon);
            }
        });
    });
}

function habilitarDragDropEnValores() {
    const valores = document.querySelectorAll('.valor-item:not([draggable])');
    valores.forEach(valor => {
        valor.setAttribute('draggable', 'true');
        
        valor.addEventListener('dragstart', (e) => {
            draggedElement = valor;
            draggedType = 'valor';
            valor.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.stopPropagation(); // Evitar conflicto con drag del cajón
            console.log('[Drag&Drop] Arrastrando valor:', valor.textContent);
        });
        
        valor.addEventListener('dragend', (e) => {
            valor.classList.remove('dragging');
            document.querySelectorAll('.drag-over').forEach(el => {
                el.classList.remove('drag-over');
            });
            draggedElement = null;
            draggedType = null;
        });
        
        valor.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (draggedType === 'valor' && draggedElement !== valor) {
                valor.classList.add('drag-over');
            }
        });
        
        valor.addEventListener('dragleave', (e) => {
            valor.classList.remove('drag-over');
        });
        
        valor.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            valor.classList.remove('drag-over');
            
            if (draggedType === 'valor' && draggedElement !== valor) {
                intercambiarValores(draggedElement, valor);
            }
        });
    });
}

function intercambiarCajones(cajon1, cajon2) {
    console.log('[Drag&Drop] Intercambiando cajones');
    
    const parent1 = cajon1.parentNode;
    const parent2 = cajon2.parentNode;
    
    const next1 = cajon1.nextSibling;
    const next2 = cajon2.nextSibling;
    
    // Intercambiar posiciones
    if (next1 === cajon2) {
        parent1.insertBefore(cajon2, cajon1);
    } else if (next2 === cajon1) {
        parent2.insertBefore(cajon1, cajon2);
    } else {
        parent1.insertBefore(cajon2, next1);
        parent2.insertBefore(cajon1, next2);
    }
    
    // Animación de confirmación
    cajon1.style.animation = 'pulsoConfirmacion 0.5s ease';
    cajon2.style.animation = 'pulsoConfirmacion 0.5s ease';
    
    setTimeout(() => {
        cajon1.style.animation = '';
        cajon2.style.animation = '';
    }, 500);
    
    // Notificar al backend (opcional, para persistir)
    notificarMovimiento('cajon', cajon1.dataset.cajonId, cajon2.dataset.cajonId);
}

function intercambiarValores(valor1, valor2) {
    console.log('[Drag&Drop] Intercambiando valores');
    
    const parent1 = valor1.parentNode;
    const parent2 = valor2.parentNode;
    
    const next1 = valor1.nextSibling;
    const next2 = valor2.nextSibling;
    
    // Intercambiar posiciones
    if (next1 === valor2) {
        parent1.insertBefore(valor2, valor1);
    } else if (next2 === valor1) {
        parent2.insertBefore(valor1, valor2);
    } else {
        parent1.insertBefore(valor2, next1);
        parent2.insertBefore(valor1, next2);
    }
    
    // Animación de confirmación
    valor1.style.animation = 'pulsoConfirmacion 0.5s ease';
    valor2.style.animation = 'pulsoConfirmacion 0.5s ease';
    
    setTimeout(() => {
        valor1.style.animation = '';
        valor2.style.animation = '';
    }, 500);
    
    // Notificar al backend (opcional, para persistir)
    notificarMovimiento('valor', valor1.textContent, valor2.textContent);
}

async function notificarMovimiento(tipo, origen, destino) {
    try {
        const response = await fetch('/api/ui/movimiento', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tipo,
                origen,
                destino,
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            console.log('[Drag&Drop] Movimiento registrado en backend');
        }
    } catch (error) {
        console.warn('[Drag&Drop] Error notificando movimiento:', error);
    }
}

// Exportar para uso global
window.inicializarDragDrop = inicializarDragDrop;

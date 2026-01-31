/**
 * Sistema de Animaciones Meteorológicas para Panel Central
 * Efectos canvas-based: lluvia, sol, viento, nieve, nubes, estrellas
 * 
 * Uso: const animador = new AnimadorMeteorologico('canvas-id', 'estado');
 *      animador.iniciar();
 */

class AnimadorMeteorologico {
    constructor(canvasId, estadoInicial = 'despejado') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas #${canvasId} no encontrado`);
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.estado = estadoInicial;
        this.animacionActiva = false;
        this.particulas = [];
        this.frameId = null;
        
        // Ajustar canvas al contenedor
        this.redimensionar();
        window.addEventListener('resize', () => this.redimensionar());
    }
    
    redimensionar() {
        const parent = this.canvas.parentElement;
        this.canvas.width = parent.clientWidth;
        this.canvas.height = parent.clientHeight;
        this.reiniciarParticulas();
    }
    
    cambiarEstado(nuevoEstado) {
        if (this.estado !== nuevoEstado) {
            this.estado = nuevoEstado;
            this.reiniciarParticulas();
        }
    }
    
    reiniciarParticulas() {
        this.particulas = [];
        switch (this.estado) {
            case 'lluvia':
                this.crearLluvia(150);
                break;
            case 'lluvia_intensa':
                this.crearLluvia(300);
                break;
            case 'nieve':
                this.crearNieve(100);
                break;
            case 'tormenta':
                this.crearLluvia(200);
                this.crearRelampagos();
                break;
            case 'nublado':
                this.crearNubes(5);
                break;
            case 'parcialmente_nublado':
                this.crearNubes(3);
                break;
            case 'despejado':
                // Sin partículas para despejado diurno
                break;
            case 'despejado_noche':
                this.crearEstrellas(150);
                break;
            case 'viento':
                this.crearViento(80);
                break;
            default:
                break;
        }
    }
    
    crearLluvia(cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.particulas.push({
                tipo: 'lluvia',
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height - this.canvas.height,
                velocidadY: 5 + Math.random() * 5,
                velocidadX: -1 + Math.random() * 2,
                largo: 10 + Math.random() * 20,
                opacidad: 0.3 + Math.random() * 0.4
            });
        }
    }
    
    crearNieve(cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.particulas.push({
                tipo: 'nieve',
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height - this.canvas.height,
                velocidadY: 1 + Math.random() * 2,
                velocidadX: -0.5 + Math.random() * 1,
                radio: 2 + Math.random() * 3,
                opacidad: 0.6 + Math.random() * 0.4,
                rotacion: Math.random() * Math.PI * 2,
                velocidadRotacion: (Math.random() - 0.5) * 0.05
            });
        }
    }
    
    crearNubes(cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.particulas.push({
                tipo: 'nube',
                x: Math.random() * this.canvas.width,
                y: 20 + Math.random() * (this.canvas.height * 0.3),
                velocidadX: 0.2 + Math.random() * 0.5,
                ancho: 80 + Math.random() * 120,
                alto: 30 + Math.random() * 40,
                opacidad: 0.3 + Math.random() * 0.3
            });
        }
    }
    
    crearEstrellas(cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.particulas.push({
                tipo: 'estrella',
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radio: 0.5 + Math.random() * 1.5,
                opacidad: 0.3 + Math.random() * 0.7,
                velocidadParpadeo: 0.01 + Math.random() * 0.02,
                direccionParpadeo: Math.random() > 0.5 ? 1 : -1
            });
        }
    }
    
    crearViento(cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.particulas.push({
                tipo: 'viento',
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                velocidadX: 3 + Math.random() * 4,
                velocidadY: -0.5 + Math.random() * 1,
                largo: 20 + Math.random() * 40,
                opacidad: 0.1 + Math.random() * 0.2
            });
        }
    }
    
    crearRelampagos() {
        // Los relámpagos se generan aleatoriamente durante la animación
        this.ultimoRelampago = Date.now();
        this.intervaloRelampago = 2000 + Math.random() * 5000;
    }
    
    iniciar() {
        if (this.animacionActiva) return;
        this.animacionActiva = true;
        this.animar();
    }
    
    detener() {
        this.animacionActiva = false;
        if (this.frameId) {
            cancelAnimationFrame(this.frameId);
            this.frameId = null;
        }
    }
    
    animar() {
        if (!this.animacionActiva) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Renderizar relámpagos (tormenta)
        if (this.estado === 'tormenta' && Date.now() - this.ultimoRelampago > this.intervaloRelampago) {
            this.renderizarRelampago();
            this.ultimoRelampago = Date.now();
            this.intervaloRelampago = 2000 + Math.random() * 5000;
        }
        
        // Actualizar y renderizar partículas
        this.particulas.forEach((p, index) => {
            switch (p.tipo) {
                case 'lluvia':
                    this.actualizarLluvia(p);
                    this.renderizarLluvia(p);
                    break;
                case 'nieve':
                    this.actualizarNieve(p);
                    this.renderizarNieve(p);
                    break;
                case 'nube':
                    this.actualizarNube(p);
                    this.renderizarNube(p);
                    break;
                case 'estrella':
                    this.actualizarEstrella(p);
                    this.renderizarEstrella(p);
                    break;
                case 'viento':
                    this.actualizarViento(p);
                    this.renderizarViento(p);
                    break;
            }
        });
        
        this.frameId = requestAnimationFrame(() => this.animar());
    }
    
    actualizarLluvia(p) {
        p.y += p.velocidadY;
        p.x += p.velocidadX;
        if (p.y > this.canvas.height) {
            p.y = -p.largo;
            p.x = Math.random() * this.canvas.width;
        }
    }
    
    renderizarLluvia(p) {
        this.ctx.strokeStyle = `rgba(174, 194, 224, ${p.opacidad})`;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(p.x, p.y);
        this.ctx.lineTo(p.x + p.velocidadX * 2, p.y + p.largo);
        this.ctx.stroke();
    }
    
    actualizarNieve(p) {
        p.y += p.velocidadY;
        p.x += p.velocidadX;
        p.rotacion += p.velocidadRotacion;
        if (p.y > this.canvas.height) {
            p.y = -p.radio;
            p.x = Math.random() * this.canvas.width;
        }
    }
    
    renderizarNieve(p) {
        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate(p.rotacion);
        this.ctx.fillStyle = `rgba(255, 255, 255, ${p.opacidad})`;
        this.ctx.beginPath();
        this.ctx.arc(0, 0, p.radio, 0, Math.PI * 2);
        this.ctx.fill();
        // Copo hexagonal
        for (let i = 0; i < 6; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, 0);
            this.ctx.lineTo(p.radio * 1.5 * Math.cos(i * Math.PI / 3), p.radio * 1.5 * Math.sin(i * Math.PI / 3));
            this.ctx.strokeStyle = `rgba(255, 255, 255, ${p.opacidad * 0.6})`;
            this.ctx.lineWidth = 0.5;
            this.ctx.stroke();
        }
        this.ctx.restore();
    }
    
    actualizarNube(p) {
        p.x += p.velocidadX;
        if (p.x > this.canvas.width + p.ancho) {
            p.x = -p.ancho;
            p.y = 20 + Math.random() * (this.canvas.height * 0.3);
        }
    }
    
    renderizarNube(p) {
        this.ctx.fillStyle = `rgba(200, 200, 220, ${p.opacidad})`;
        this.ctx.beginPath();
        this.ctx.ellipse(p.x, p.y, p.ancho / 2, p.alto / 2, 0, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.beginPath();
        this.ctx.ellipse(p.x + p.ancho / 4, p.y - p.alto / 3, p.ancho / 3, p.alto / 2.5, 0, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.beginPath();
        this.ctx.ellipse(p.x - p.ancho / 4, p.y - p.alto / 4, p.ancho / 3.5, p.alto / 3, 0, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    actualizarEstrella(p) {
        p.opacidad += p.velocidadParpadeo * p.direccionParpadeo;
        if (p.opacidad > 1 || p.opacidad < 0.3) {
            p.direccionParpadeo *= -1;
        }
    }
    
    renderizarEstrella(p) {
        this.ctx.fillStyle = `rgba(255, 255, 255, ${p.opacidad})`;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radio, 0, Math.PI * 2);
        this.ctx.fill();
        // Destellos
        this.ctx.strokeStyle = `rgba(255, 255, 255, ${p.opacidad * 0.5})`;
        this.ctx.lineWidth = 0.5;
        this.ctx.beginPath();
        this.ctx.moveTo(p.x - p.radio * 2, p.y);
        this.ctx.lineTo(p.x + p.radio * 2, p.y);
        this.ctx.moveTo(p.x, p.y - p.radio * 2);
        this.ctx.lineTo(p.x, p.y + p.radio * 2);
        this.ctx.stroke();
    }
    
    actualizarViento(p) {
        p.x += p.velocidadX;
        p.y += p.velocidadY;
        if (p.x > this.canvas.width) {
            p.x = -p.largo;
            p.y = Math.random() * this.canvas.height;
        }
    }
    
    renderizarViento(p) {
        this.ctx.strokeStyle = `rgba(200, 220, 240, ${p.opacidad})`;
        this.ctx.lineWidth = 1.5;
        this.ctx.beginPath();
        this.ctx.moveTo(p.x, p.y);
        this.ctx.lineTo(p.x + p.largo, p.y + p.velocidadY * 5);
        this.ctx.stroke();
    }
    
    renderizarRelampago() {
        const x = Math.random() * this.canvas.width;
        const segmentos = 5 + Math.floor(Math.random() * 5);
        let posX = x;
        let posY = 0;
        
        this.ctx.strokeStyle = 'rgba(255, 255, 200, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.shadowBlur = 10;
        this.ctx.shadowColor = 'rgba(255, 255, 255, 1)';
        this.ctx.beginPath();
        this.ctx.moveTo(posX, posY);
        
        for (let i = 0; i < segmentos; i++) {
            posX += (Math.random() - 0.5) * 40;
            posY += this.canvas.height / segmentos;
            this.ctx.lineTo(posX, posY);
        }
        
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;
        
        // Iluminación de fondo breve
        setTimeout(() => {
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }, 50);
    }
}

// Exportar para uso global
window.AnimadorMeteorologico = AnimadorMeteorologico;

// Efectos visuales meteorológicos para el dashboard MeteoSer
// Este archivo se debe importar en dashboard.html después de app.js

(function() {
    // Crea un canvas para efectos visuales
    function crearCanvasEfectos() {
        let canvas = document.getElementById('meteo-effects-canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'meteo-effects-canvas';
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.pointerEvents = 'none';
            canvas.style.zIndex = '10';
            document.body.appendChild(canvas);
        }
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        return canvas;
    }

    // Efecto lluvia
    function efectoLluvia(ctx, gotas) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.strokeStyle = 'rgba(120,180,255,0.35)';
        ctx.lineWidth = 1.2;
        gotas.forEach(gota => {
            ctx.beginPath();
            ctx.moveTo(gota.x, gota.y);
            ctx.lineTo(gota.x + gota.dx, gota.y + gota.dy);
            ctx.stroke();
            gota.x += gota.dx;
            gota.y += gota.dy;
            if (gota.y > ctx.canvas.height || gota.x > ctx.canvas.width) {
                gota.x = Math.random() * ctx.canvas.width;
                gota.y = -10;
            }
        });
    }

    // Efecto nubes
    function efectoNubes(ctx, nubes) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        nubes.forEach(nube => {
            ctx.save();
            ctx.globalAlpha = 0.18;
            ctx.beginPath();
            ctx.ellipse(nube.x, nube.y, nube.rx, nube.ry, 0, 0, 2 * Math.PI);
            ctx.fillStyle = '#e0e6ed';
            ctx.fill();
            ctx.restore();
            nube.x += nube.dx;
            if (nube.x - nube.rx > ctx.canvas.width) {
                nube.x = -nube.rx;
            }
        });
    }

    // Efecto viento
    function efectoViento(ctx, lineas) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.strokeStyle = 'rgba(180,255,220,0.22)';
        ctx.lineWidth = 2;
        lineas.forEach(linea => {
            ctx.beginPath();
            ctx.moveTo(linea.x, linea.y);
            ctx.bezierCurveTo(linea.x + 30, linea.y - 10, linea.x + 60, linea.y + 10, linea.x + 90, linea.y);
            ctx.stroke();
            linea.x += linea.dx;
            if (linea.x > ctx.canvas.width) {
                linea.x = -100;
                linea.y = Math.random() * ctx.canvas.height;
            }
        });
    }

    // Efecto nieve
    function efectoNieve(ctx, copos) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        copos.forEach(copo => {
            ctx.beginPath();
            ctx.arc(copo.x, copo.y, copo.r, 0, 2 * Math.PI);
            ctx.fill();
            copo.y += copo.dy;
            copo.x += copo.dx;
            if (copo.y > ctx.canvas.height) {
                copo.y = -copo.r;
                copo.x = Math.random() * ctx.canvas.width;
            }
            if (copo.x > ctx.canvas.width) copo.x = 0;
            if (copo.x < 0) copo.x = ctx.canvas.width;
        });
    }

    // Efecto sol
    function efectoSol(ctx) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        const cx = ctx.canvas.width - 120;
        const cy = 120;
        ctx.save();
        ctx.globalAlpha = 0.18;
        ctx.beginPath();
        ctx.arc(cx, cy, 60, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffe066';
        ctx.shadowColor = '#ffe066';
        ctx.shadowBlur = 40;
        ctx.fill();
        ctx.restore();
        // Rayos
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * 2 * Math.PI;
            const x1 = cx + Math.cos(angle) * 70;
            const y1 = cy + Math.sin(angle) * 70;
            const x2 = cx + Math.cos(angle) * 90;
            const y2 = cy + Math.sin(angle) * 90;
            ctx.save();
            ctx.globalAlpha = 0.18;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = '#ffe066';
            ctx.lineWidth = 6;
            ctx.stroke();
            ctx.restore();
        }
    }

    // Detectar estado y animar
    function animarEfectoMeteo(estado, intensidad = 0.4) {
        const canvas = crearCanvasEfectos();
        const ctx = canvas.getContext('2d');
        let animId;
        let elementos = [];
        const factor = Math.max(0.2, Math.min(1, intensidad));
        function loop() {
            if (estado === 'lluvia') efectoLluvia(ctx, elementos);
            else if (estado === 'nubes') efectoNubes(ctx, elementos);
            else if (estado === 'viento') efectoViento(ctx, elementos);
            else if (estado === 'nieve') efectoNieve(ctx, elementos);
            else if (estado === 'sol') efectoSol(ctx);
            else ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            animId = requestAnimationFrame(loop);
        }
        // Inicializar elementos
        if (estado === 'lluvia') {
            const count = Math.round(30 + 60 * factor);
            elementos = Array.from({length: count}, () => ({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                dx: 2 + Math.random() * 2,
                dy: 12 + Math.random() * 8
            }));
        } else if (estado === 'nubes') {
            const count = Math.round(4 + 8 * factor);
            elementos = Array.from({length: count}, () => ({
                x: Math.random() * canvas.width,
                y: 60 + Math.random() * 120,
                rx: 120 + Math.random() * 80,
                ry: 32 + Math.random() * 18,
                dx: 0.3 + Math.random() * 0.5
            }));
        } else if (estado === 'viento') {
            const count = Math.round(8 + 16 * factor);
            elementos = Array.from({length: count}, () => ({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                dx: 2.5 + Math.random() * 2
            }));
        } else if (estado === 'nieve') {
            const count = Math.round(24 + 48 * factor);
            elementos = Array.from({length: count}, () => ({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: 2 + Math.random() * 2,
                dx: -0.5 + Math.random(),
                dy: 1.5 + Math.random() * 1.5
            }));
        }
        loop();
        // Devuelve función para limpiar
        return () => {
            cancelAnimationFrame(animId);
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        };
    }

    // Exponer globalmente
    let limpiarActual = null;
    window.activarEfectoMeteo = (estado, intensidad) => {
        if (limpiarActual) limpiarActual();
        limpiarActual = animarEfectoMeteo(estado, intensidad);
    };
    window.animarEfectoMeteo = animarEfectoMeteo;
})();

// puzzle.js: carga dinámica real para interfaz tipo puzzle MeteoSer

async function fetchJSON(url, options) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

function setContent(id, text) {
    const el = document.getElementById(id + '-content');
    if (el) el.textContent = text;
}

function fmt(val, unit = '') {
    if (val === null || val === undefined || Number.isNaN(val)) return '—';
    const n = typeof val === 'number' ? val : parseFloat(val);
    if (Number.isNaN(n)) return String(val);
    return `${n.toFixed(2)}${unit ? ' ' + unit : ''}`;
}

async function cargarEstado() {
    try {
        const data = await fetchJSON('/estado');
        const temp = Object.keys(data?.meteo?.sensores || {}).find(k => k.includes('temp'));
        const hum = Object.keys(data?.meteo?.sensores || {}).find(k => k.includes('humedad'));
        const tempVal = temp ? data.meteo.sensores[temp] : null;
        const humVal = hum ? data.meteo.sensores[hum] : null;
        setContent('estado', 'Sistema operativo');
        setContent('sensores', `Temp: ${fmt(tempVal?.value, tempVal?.unit)} | HR: ${fmt(humVal?.value, humVal?.unit)}`);
        setContent('indices', `Arco solar: ${fmt(data?.indices?.arco_solar?.valor ?? data?.indices?.arco_solar)}°`);
        setContent('prediccion', data?.predicciones ? JSON.stringify(data.predicciones) : 'Sin predicción');
        setContent('recomendaciones', data?.recomendacion ? String(data.recomendacion) : 'Sin recomendaciones');
        setContent('historial', data?.meteo?.ts ? `Última actualización: ${new Date(data.meteo.ts * 1000).toLocaleString('es-ES')}` : 'Sin historial');
        setContent('noticias', data?.organizacion?.noticias ? String(data.organizacion.noticias) : 'Sin noticias');
        setContent('asistente', data?.asistente ? 'Asistente disponible' : 'Asistente sin datos');
        setContent('configuracion', data?.indices?.origen_ubicacion ? `Ubicación: ${data.indices.origen_ubicacion}` : 'Configuración');
    } catch (err) {
        setContent('estado', 'Error al cargar estado');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    cargarEstado();
    setInterval(cargarEstado, 15000);
});

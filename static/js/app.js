const STATE_URL = '/estado';

const charts = {
    tempHum: null
};

const cacheState = {
    sensors: new Set(),
    indices: new Set(),
    recHistory: [],
    lastRec: null,
    lastSignals: []
};

const storageKeys = {
    hidden: 'meteoser_hidden_items',
    show: 'meteoser_show_items',
    labels: 'meteoser_label_overrides',
    uiScale: 'meteoser_ui_scale',
    uiCompact: 'meteoser_ui_compact'
};

const userPrefs = {
    hidden: { sensor: new Set(), indice: new Set() },
    show: { sensor: new Set(), indice: new Set() },
    labels: {},
    uiScale: 1,
    uiCompact: false
};

let currentEffects = null;
let lastEstado = null;
let voiceSessionId = null;

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

const fahrenheitTemperatureKeys = new Set([
    'tempf',
    'tempf_original',
    'tempinf',
    'tempinf_original'
]);

function convertFahrenheitToCelsius(value) {
    const numeric = typeof value === 'number' ? value : parseFloat(value);
    if (Number.isNaN(numeric)) return null;
    return (numeric - 32) * 5.0 / 9.0;
}

function normalizeUnitLabel(unit) {
    if (!unit) return '';
    const cleaned = String(unit).trim();
    const slug = cleaned.replace(/\s+/g, '').toLowerCase();
    if (['c', '°c', 'celsius', 'celcius', 'célcius', 'cº'].includes(slug)) return '°C';
    if (['f', '°f', 'fahrenheit'].includes(slug)) return '°F';
    return cleaned;
}

function fmt(value, unit = '') {
    if (value === null || value === undefined || Number.isNaN(value)) return '—';
    if (typeof value === 'string') {
        const trimmed = value.trim();
        if (!/^[-+]?\d+(\.\d+)?$/.test(trimmed)) {
            return trimmed;
        }
    }
    const numeric = typeof value === 'number' ? value : parseFloat(value);
    if (Number.isNaN(numeric)) return String(value);
    let txt = numeric.toFixed(2);
    txt = txt.replace(/\.00$/, '');
    txt = txt.replace(/(\.\d)0$/, '$1');
    const normalizedUnit = normalizeUnitLabel(unit);
    return normalizedUnit ? `${txt} ${normalizedUnit}` : txt;
}

function normalizeNumeric(value) {
    const n = typeof value === 'number' ? value : parseFloat(value);
    if (Number.isNaN(n)) return null;
    if (n <= 1 && n >= 0) return n * 100;
    return n;
}

function capitalize(text) {
    if (!text) return '';
    const str = String(text);
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function classifyValue(key, value, unit = '') {
    const normalized = normalizeNumeric(value);
    if (normalized === null) return '';
    if (key.includes('indice_cielo_astronomico')) {
        if (normalized >= 75) return 'value--good';
        if (normalized >= 45) return 'value--med';
        return 'value--bad';
    }
    if (key.includes('indice_cetreria')) {
        if (normalized >= 75) return 'value--good';
        if (normalized >= 45) return 'value--med';
        return 'value--bad';
    }
    if (key.includes('temp') || unit.toLowerCase().includes('c')) {
        if (normalized >= 26) return 'value--temp-hot';
        if (normalized >= 18) return 'value--temp-ok';
        return 'value--temp-cold';
    }
    if (normalized >= 70) return 'value--high';
    if (normalized >= 35) return 'value--med';
    return 'value--low';
}

function toArray(value) {
    if (value == null) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'object') return Object.values(value);
    return [value];
}

function isAnomaly(key, value) {
    const normalized = normalizeNumeric(value);
    if (normalized === null) return false;
    if (key.includes('riesgo') || key.includes('alerta')) return normalized >= 60;
    if (key.includes('viento') || key.includes('racha')) return normalized >= 50;
    if (key.includes('frio')) return normalized <= -5;
    if (key.includes('calor')) return normalized >= 35;
    return normalized >= 85;
}

const iconMap = {
    temp: '🌡️',
    humedad: '💧',
    presion: '🧭',
    viento: '🌬️',
    lluvia: '🌧️',
    sol: '☀️',
    nieve: '❄️',
    co2: '🫧',
    uv: '🕶️',
    luz: '💡',
    energia: '⚡',
    ruido: '🔊',
    ozono: '🧪',
    riesgo: '⚠️'
};

const labelMap = {
    tempf: 'Temperatura (sensor)',
    humidity: 'Humedad (sensor)',
    windspeedmph: 'Viento (sensor)',
    rainratein: 'Lluvia (intensidad)',
    rain_ratein: 'Lluvia (intensidad)',
    rainrate: 'Lluvia (intensidad)',
    rain_rate: 'Lluvia (intensidad)',
    rainin: 'Lluvia acumulada',
    dailyrainin: 'Lluvia acumulada día',
    eventrainin: 'Lluvia acumulada evento',
    hourlyrainin: 'Lluvia acumulada hora',
    lightning: 'Distancia del rayo',
    lightning_num: 'Contador de rayos',
    lightning_time: 'Último rayo',
    ultimo_rayo: 'Último rayo',
    rayos: 'Rayos detectados',
    rayos_total: 'Rayos detectados',
    rayos_offset: 'Offset rayos',
    distancia_rayo: 'Distancia del rayo',
    pm25: 'Partículas PM2.5',
    wh51: 'Humedad suelo',
    wh51_ad: 'Humedad suelo (AD)',
    lluvia_1h: 'Lluvia 1h',
    lluvia_24h: 'Lluvia 24h',
    lluvia_acumulada: 'Lluvia acumulada',
    lluvia_rate: 'Lluvia (mm/h)',
    lluvia: 'Lluvia (mm/h)',
    temperatura: 'Temperatura exterior',
    humedad: 'Humedad exterior',
    temperatura_interior: 'Temperatura interior',
    humedad_interior: 'Humedad interior',
    presion: 'Presión',
    presion_relativa: 'Presión relativa',
    presion_absoluta: 'Presión absoluta',
    viento: 'Viento',
    racha: 'Racha',
    lluvia: 'Lluvia',
    radiacion: 'Radiación solar',
    uv: 'UV',
    nubosidad_estimada: 'Nubosidad estimada',
    sonometro: 'Sonógrafo',
    sismografo: 'Sismógrafo',
    indice_cielo_astronomico: 'Índice cielo astronómico',
    indice_cielo_astronomico_nivel: 'Nivel cielo astronómico',
    cielo_observable_nocturno: 'Cielo observable nocturno',
    ventana_observacion_nocturna: 'Ventana observación nocturna',
    duracion_noche_h: 'Duración de noche',
    transparencia_atmosferica: 'Transparencia atmosférica',
    riesgo_empaniamiento_optica: 'Riesgo empañamiento óptica',
    seeing_termico_basico: 'Seeing térmico básico',
    fase_lunar: 'Fase lunar',
    indice_cetreria: 'Índice cetrería',
    viento_cetreria: 'Viento cetrería',
    visibilidad_terreno: 'Visibilidad del terreno',
    termales_probabilidad: 'Probabilidad de térmicas',
    barro_campo: 'Barro en campo',
    confort_ave: 'Confort del ave',
    indice_viento_cetreria: 'Índice viento cetrería',
    indice_visibilidad_cetreria: 'Índice visibilidad cetrería',
    indice_termales: 'Índice térmicas',
    indice_seguridad_vuelo: 'Índice seguridad de vuelo',
    tempinf_original: 'Temperatura interior original',
    humidityin_original: 'Humedad interior original',
    baromrelin_original: 'Presión relativa interior original',
    baromabsin_original: 'Presión absoluta interior original',
    tempf_original: 'Temperatura exterior original',
    humidity_original: 'Humedad exterior original',
    windspeedmph_original: 'Viento original',
    solarradiation_original: 'Radiación solar original',
    rainratein_original: 'Lluvia (intensidad) original',
    rainin_original: 'Lluvia acumulada original',
    ultimo_ecowitt: 'Último Ecowitt',
    ultimo_ecowitt_error: 'Último Ecowitt (error)',
    mqtt_test_sensor: 'MQTT test',
    mqtt_temp: 'Temp. MQTT',
};

const sensorDescriptionMap = {
    tempf_original: 'Lectura original de temperatura exterior recibida por Ecowitt (sin normalizar).',
    tempinf_original: 'Lectura original de temperatura interior recibida por Ecowitt (sin normalizar).',
    humidity_original: 'Lectura original de humedad exterior recibida por Ecowitt (sin normalizar).',
    humidityin_original: 'Lectura original de humedad interior recibida por Ecowitt (sin normalizar).',
    baromrelin_original: 'Presión relativa interior original recibida por Ecowitt.',
    baromabsin_original: 'Presión absoluta interior original recibida por Ecowitt.',
    windspeedmph_original: 'Velocidad de viento original en mph recibida por Ecowitt.',
    solarradiation_original: 'Radiación solar original recibida por Ecowitt.',
    rainratein_original: 'Intensidad de lluvia original recibida por Ecowitt.',
    rainin_original: 'Lluvia acumulada original recibida por Ecowitt.',
    viento: 'Velocidad de viento ya convertida a km/h y normalizada por MeteoSer.',
    windspeedmph_original: 'Velocidad del viento original en mph recibida por Ecowitt (sin convertir).',
    lluvia: 'Intensidad de lluvia en mm/h cuando está disponible.',
    lluvia_rate: 'Intensidad de lluvia en mm/h.',
    ultimo_ecowitt: 'Marca de tiempo del último paquete Ecowitt recibido.',
    ultimo_ecowitt_error: 'Último intento fallido de recepción Ecowitt.',
    mqtt_test_sensor: 'Sensor de pruebas publicado vía MQTT.',
    mqtt_temp: 'Temperatura reportada por dispositivo MQTT.',
    wh51: 'Humedad de suelo medida por sensor WH51.'
};

const labelAbbrevMap = {
    Temperatura: 'Temp.',
    Humedad: 'Hum.',
    Presión: 'Pres.',
    Radiación: 'Rad.',
    Velocidad: 'Vel.',
    Intensidad: 'Int.',
    acumulada: 'acum.',
    interior: 'int.',
    exterior: 'ext.',
    original: 'orig.',
    Último: 'Últ.',
    Última: 'Últ.',
    Duración: 'Dur.',
    Ventana: 'Vent.',
    Observación: 'Obs.',
    Probabilidad: 'Prob.',
    Seguridad: 'Seg.',
    Visibilidad: 'Vis.',
    Cetrería: 'Cetr.',
    astronómico: 'astro.',
    astronómica: 'astro.'
};

function abbreviateLabel(label) {
    if (!label) return '';
    let result = label;
    Object.entries(labelAbbrevMap).forEach(([word, abbr]) => {
        const re = new RegExp(`\\b${word}\\b`, 'gi');
        result = result.replace(re, abbr);
    });
    result = result.replace(/\s{2,}/g, ' ').trim();
    if (result.length > 28) {
        result = result
            .split(' ')
            .map(word => (word.length > 6 ? `${word.slice(0, 4)}.` : word))
            .join(' ');
    }
    return result;
}

function humanizeKey(key) {
    if (!key) return '';
    const cleaned = key.replace(/_/g, ' ');
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function getDisplayLabel(key) {
    if (!key) return '';
    if (userPrefs.labels && userPrefs.labels[key]) {
        return userPrefs.labels[key];
    }
    if (key.startsWith('mqtt_')) {
        const suffix = humanizeKey(key.replace(/^mqtt_/, ''));
        return abbreviateLabel(`MQTT ${suffix}`);
    }
    return abbreviateLabel(labelMap[key] || humanizeKey(key));
}

const lightningGroupKeys = new Set([
    'lightning',
    'lightning_num',
    'lightning_time',
    'ultimo_rayo',
    'rayos',
    'rayos_total',
    'rayos_offset',
    'distancia_rayo'
]);

const hiddenSensorKeys = new Set([
    'wh51_ad',
    'lightning',
    'lightning_num',
    'lightning_time',
    'rayos_offset',
    'rayos_total'
]);

const hiddenRawSensorKeys = new Set([
    'tempf',
    'tempinf',
    'humidity',
    'humidityin',
    'baromrelin',
    'baromabsin',
    'windspeedmph',
    'windspdmph_avg10m',
    'windgustmph',
    'maxdailygust',
    'rainratein',
    'rain_ratein',
    'rainrate',
    'rain_rate',
    'rainin',
    'dailyrainin',
    'eventrainin',
    'hourlyrainin',
    'solarradiation',
    'uvindex',
    'uv_index'
]);

const hiddenIndexKeys = new Set([
    'pm25',
    'amanecer',
    'amanecer_astronomico',
    'amanecer_hibrido',
    'atardecer',
    'atardecer_astronomico',
    'atardecer_hibrido',
    'arco_solar',
    'duracion_dia_h',
    'duracion_noche_h',
    'lightning',
    'lightning_num',
    'rayos_offset',
    'rayos',
    'rayos_total',
    'latitud',
    'longitud',
    'origen_ubicacion',
    'seeing_termico_basico'
]);

function loadUserPrefs() {
    try {
        const hiddenRaw = JSON.parse(localStorage.getItem(storageKeys.hidden) || '{}');
        const showRaw = JSON.parse(localStorage.getItem(storageKeys.show) || '{}');
        const labelsRaw = JSON.parse(localStorage.getItem(storageKeys.labels) || '{}');
        const uiScale = parseFloat(localStorage.getItem(storageKeys.uiScale) || '1');
        const uiCompact = localStorage.getItem(storageKeys.uiCompact) === '1';
        userPrefs.hidden.sensor = new Set(hiddenRaw.sensor || []);
        userPrefs.hidden.indice = new Set(hiddenRaw.indice || []);
        userPrefs.show.sensor = new Set(showRaw.sensor || []);
        userPrefs.show.indice = new Set(showRaw.indice || []);
        userPrefs.labels = labelsRaw || {};
        userPrefs.uiScale = Number.isNaN(uiScale) ? 1 : uiScale;
        userPrefs.uiCompact = uiCompact;
    } catch (err) {
        // ignore
    }
}

function saveUserPrefs() {
    const hiddenPayload = {
        sensor: Array.from(userPrefs.hidden.sensor),
        indice: Array.from(userPrefs.hidden.indice)
    };
    const showPayload = {
        sensor: Array.from(userPrefs.show.sensor),
        indice: Array.from(userPrefs.show.indice)
    };
    localStorage.setItem(storageKeys.hidden, JSON.stringify(hiddenPayload));
    localStorage.setItem(storageKeys.show, JSON.stringify(showPayload));
    localStorage.setItem(storageKeys.labels, JSON.stringify(userPrefs.labels || {}));
    localStorage.setItem(storageKeys.uiScale, String(userPrefs.uiScale || 1));
    localStorage.setItem(storageKeys.uiCompact, userPrefs.uiCompact ? '1' : '0');
}

function applyUiPrefs() {
    document.documentElement.style.setProperty('--ui-scale', userPrefs.uiScale || 1);
    document.body.classList.toggle('compact', userPrefs.uiCompact);
    const scaleInput = document.getElementById('ui-scale-input');
    if (scaleInput) scaleInput.value = String(userPrefs.uiScale || 1);
    const compactToggle = document.getElementById('ui-compact-toggle');
    if (compactToggle) compactToggle.checked = userPrefs.uiCompact;
}

function isBaseHiddenSensor(key) {
    if (hiddenSensorKeys.has(key)) return true;
    if (hiddenRawSensorKeys.has(key)) return true;
    if (key.endsWith('_original')) return true;
    return false;
}

function isBaseHiddenIndex(key) {
    return hiddenIndexKeys.has(key);
}

function isHiddenItem(kind, key) {
    const forceShow = kind === 'sensor' ? userPrefs.show.sensor : userPrefs.show.indice;
    if (forceShow && forceShow.has(key)) return false;
    if (kind === 'sensor') {
        return isBaseHiddenSensor(key) || userPrefs.hidden.sensor.has(key);
    }
    if (kind === 'indice') {
        return isBaseHiddenIndex(key) || userPrefs.hidden.indice.has(key);
    }
    return false;
}

function setHiddenItem(kind, key, hidden) {
    const target = kind === 'sensor' ? userPrefs.hidden.sensor : userPrefs.hidden.indice;
    if (!target) return;
    if (hidden) target.add(key);
    else target.delete(key);
    saveUserPrefs();
}

function setForceShow(kind, key, enabled) {
    const target = kind === 'sensor' ? userPrefs.show.sensor : userPrefs.show.indice;
    if (!target) return;
    if (enabled) target.add(key);
    else target.delete(key);
    saveUserPrefs();
}

const cetreriaSubindices = [
    'viento_cetreria',
    'visibilidad_terreno',
    'termales_probabilidad',
    'barro_campo',
    'confort_ave',
    'indice_viento_cetreria',
    'indice_visibilidad_cetreria',
    'indice_termales',
    'indice_seguridad_vuelo',
    'seeing_termico_basico'
];

cetreriaSubindices.forEach(key => hiddenIndexKeys.add(key));

function parseLightningTimestamp(value) {
    if (value === null || value === undefined || value === '') return null;
    if (typeof value === 'number') {
        const ms = value < 1e12 ? value * 1000 : value;
        return new Date(ms);
    }
    const raw = String(value).trim();
    if (!raw) return null;
    if (/^\d+$/.test(raw)) {
        const num = Number(raw);
        const ms = num < 1e12 ? num * 1000 : num;
        return new Date(ms);
    }
    const parsed = new Date(raw);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatLightningAge(value) {
    const dt = parseLightningTimestamp(value);
    if (!dt) return 'Sin datos';
    const now = new Date();
    const diffMs = now.getTime() - dt.getTime();
    const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));
    if (diffDays <= 0) {
        return `Hoy ${dt.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
    }
    return `${diffDays} día${diffDays === 1 ? '' : 's'}`;
}

function formatLightningFull(value) {
    const dt = parseLightningTimestamp(value);
    if (!dt) return 'Sin datos';
    const fecha = dt.toLocaleDateString('es-ES');
    const hora = dt.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    return `${fecha} / ${hora}`;
}

function formatIsoDate(value) {
    const dt = parseLightningTimestamp(value);
    if (!dt) return String(value);
    const fecha = dt.toLocaleDateString('es-ES');
    const hora = dt.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    return `${fecha} / ${hora}`;
}

function formatValueForKey(key, value, unit = '') {
    const normalizedKey = (key || '').toLowerCase();
    if (fahrenheitTemperatureKeys.has(normalizedKey)) {
        const converted = convertFahrenheitToCelsius(value);
        if (converted === null) {
            return fmt(value, '°F');
        }
        return fmt(converted, '°C');
    }
    if (key === 'ultimo_rayo' || key === 'lightning_time') {
        return formatLightningAge(value);
    }
    if (key === 'ultimo_ecowitt' || key === 'ultimo_ecowitt_error') {
        return formatIsoDate(value);
    }
    if (key === 'amanecer' || key === 'amanecer_astronomico' || key === 'amanecer_hibrido'
        || key === 'atardecer' || key === 'atardecer_astronomico' || key === 'atardecer_hibrido') {
        return String(value || '—');
    }
    if (key === 'rayos' || key === 'rayos_total' || key === 'lightning_num') {
        const num = Number(value);
        return Number.isNaN(num) ? value : Math.round(num);
    }
    return fmt(value, unit);
}

function pickIcon(label) {
    const l = label.toLowerCase();
    const key = Object.keys(iconMap).find(k => l.includes(k));
    return key ? iconMap[key] : '•';
}

function buildItemHtml({ label, value, unit = '', key = '', warn = false }) {
    const icon = pickIcon(label || key);
    const valueClass = classifyValue(key || label, value, unit);
    const displayValue = formatValueForKey(key, value, unit);
    const classes = ['data-item'];
    if (warn) classes.push('item--warning');
    if (isAnomaly(key || label, value)) classes.push('item--alert');
    return `
        <div class="${classes.join(' ')}" data-key="${key}">
            <span class="item-label"><span class="item-icon">${icon}</span>${label}</span>
            <strong class="item-value ${valueClass}">${displayValue}</strong>
        </div>
    `;
}

function renderKeyValueList(items) {
    if (!items || items.length === 0) return '<div class="data-item">Sin datos</div>';
    return items.map(item => {
        const html = buildItemHtml(item);
        if (!item.kind) return html;
        return html.replace('data-key', `data-${item.kind}-key`);
    }).join('');
}

function renderList(items) {
    if (!items || items.length === 0) return '<div class="data-item">Sin datos</div>';
    return items
        .map(item => {
            const label = item && typeof item === 'object' && 'label' in item ? item.label : String(item);
            const value = item && typeof item === 'object' && 'value' in item ? item.value : '';
            const key = item && typeof item === 'object' && 'key' in item ? item.key : label;
            const kind = item && typeof item === 'object' && 'kind' in item ? item.kind : undefined;
            const html = buildItemHtml({ label, value, key });
            if (!kind) return html;
            return html.replace('data-key', `data-${kind}-key`);
        })
        .join('');
}

async function fetchJSON(url, options = {}) {
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

function getSensorNormalized(data, predicate) {
    const sensors = data?.meteo?.sensores || {};
    const keys = Object.keys(sensors);
    const key = keys.find(predicate);
    if (!key) return null;
    return { key, ...sensors[key] };
}

function getSensorValue(data, predicate) {
    const sensors = data?.sensores || {};
    const keys = Object.keys(sensors);
    const key = keys.find(predicate);
    if (!key) return null;
    return sensors[key];
}

function ensureChart(canvasId, label, dataPoints, color) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    const labels = dataPoints.map(point => point.label);
    const values = dataPoints.map(point => point.value);
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label,
                data: values,
                borderColor: color,
                backgroundColor: 'rgba(56, 242, 192, 0.18)',
                fill: true,
                tension: 0.25,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            animation: false,
            plugins: { legend: { display: false } },
            scales: { x: { display: false }, y: { display: false } }
        }
    });
}

async function updateCharts(tempKey, humKey) {
    if (!tempKey || !humKey) return;
    try {
        const [tempHist, humHist] = await Promise.all([
            fetchJSON(`/api/sensores/historial?nombre=${encodeURIComponent(tempKey)}`),
            fetchJSON(`/api/sensores/historial?nombre=${encodeURIComponent(humKey)}`)
        ]);
        const tempPoints = (tempHist.historial || []).slice(-30).map(([ts, val]) => ({
            label: new Date(ts * 1000).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
            value: Number(val)
        }));
        const humPoints = (humHist.historial || []).slice(-30).map(([ts, val]) => ({
            label: new Date(ts * 1000).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
            value: Number(val)
        }));
        if (tempPoints.length > 1) {
            if (!charts.tempHum) {
                charts.tempHum = ensureChart('graficoTempHum', 'Temperatura', tempPoints, '#38f2c0');
            } else {
                charts.tempHum.data.labels = tempPoints.map(point => point.label);
                charts.tempHum.data.datasets[0].data = tempPoints.map(point => point.value);
            }
        }
        if (humPoints.length > 1 && charts.tempHum) {
            const humidityDataset = {
                label: 'Humedad',
                data: humPoints.map(p => p.value),
                borderColor: '#60a5fa',
                backgroundColor: 'rgba(96, 165, 250, 0.15)',
                fill: true,
                tension: 0.25,
                pointRadius: 0
            };
            if (charts.tempHum.data.datasets.length < 2) {
                charts.tempHum.data.datasets.push(humidityDataset);
            } else {
                charts.tempHum.data.datasets[1] = humidityDataset;
            }
        }
        if (charts.tempHum) charts.tempHum.update();
    } catch (err) {
        // silently ignore chart errors
    }
}

function updateLocation(indices) {
    if (!indices) return;
    const lat = indices.latitud;
    const lon = indices.longitud;
    const origen = indices.origen_ubicacion;
    const locationMeta = indices.coordenadas;
    if (lat !== undefined && lon !== undefined) {
        let origenLabel = origen || 'n/d';
        if (locationMeta && typeof locationMeta === 'object') {
            const label = locationMeta.ubicacion || locationMeta.label || locationMeta.nombre;
            if (label) {
                origenLabel = label;
            }
        }
        if (!locationMeta && String(origen).toLowerCase() === 'manual') {
            origenLabel = 'Argentona';
        }
        setText('ubicacion', `Lat ${Number(lat).toFixed(4)} | Lon ${Number(lon).toFixed(4)} (${origenLabel})`);
    }
}
function formatClientTimeIso(iso) {
    if (!iso) return '—';
    const parsed = new Date(iso);
    if (Number.isNaN(parsed.getTime())) return iso;
    return parsed.toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' });
}

function formatSkewValue(skew) {
    if (skew === undefined || skew === null) return '—';
    const seconds = Number(skew);
    if (Number.isNaN(seconds)) return '—';
    const sign = seconds >= 0 ? '+' : '';
    return `${sign}${seconds}s`;
}

function formatOffsetMinutes(minutes) {
    if (minutes === undefined || minutes === null) return 'UTC —';
    const total = Number(minutes);
    if (Number.isNaN(total)) return 'UTC —';
    const sign = total >= 0 ? '+' : '-';
    const absMinutes = Math.abs(total);
    const hours = Math.floor(absMinutes / 60);
    const mins = absMinutes % 60;
    return `UTC${sign}${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
}

function formatCoordsValue(coords) {
    if (!coords) return '—';
    let lat;
    let lon;
    let locationLabel = '';
    if (Array.isArray(coords)) {
        [lat, lon] = coords;
    } else if (typeof coords === 'object') {
        locationLabel = coords.ubicacion || coords.label || coords.nombre || '';
        lat = coords.lat ?? coords.latitude ?? coords.latitud;
        lon = coords.lon ?? coords.longitude ?? coords.longitud;
    }
    const latNum = Number(lat);
    const lonNum = Number(lon);
    if (Number.isNaN(latNum) || Number.isNaN(lonNum)) return '—';
    const coordText = `Lat ${latNum.toFixed(4)} · Lon ${lonNum.toFixed(4)}`;
    return locationLabel ? `${locationLabel} · ${coordText}` : coordText;
}

function updateContextMetadata(data) {
    const contexto = data?.predicciones?.contexto || {};
    const indices = data?.indices || {};
    const horaClienteIso = contexto.hora_cliente_iso || indices.hora_cliente_iso || (indices.hora_cliente && indices.hora_cliente.valor);
    setText('context-client-time', formatClientTimeIso(horaClienteIso));
    const confidence = contexto.hora_cliente_confianza ?? (indices.hora_cliente && indices.hora_cliente.confianza);
    const skew = contexto.hora_cliente_skew_seconds ?? (indices.hora_cliente && indices.hora_cliente.skew_seconds);
    const confidenceLabel = confidence ? capitalize(String(confidence)) : '—';
    setText('context-client-sync', `Confianza ${confidenceLabel} · Skew ${formatSkewValue(skew)}`);
    const offset = contexto.timezone_offset_minutes ?? contexto.context_timezone_offset_minutes ?? indices.context_timezone_offset_minutes;
    setText('context-client-offset', formatOffsetMinutes(offset));
    const coords = contexto.coordenadas || indices.coordenadas;
    setText('context-client-coords', formatCoordsValue(coords));
}

function getSensorBase(data, keys) {
    const sensores = data?.sensores || {};
    const metadata = data?.sensores_metadata || {};
    for (const key of keys) {
        if (sensores[key] !== undefined && sensores[key] !== null) {
            const meta = metadata[key] || {};
            return { key, value: sensores[key], unit: meta.unidad || '' };
        }
    }
    return null;
}

function formatSensorValue(sensor, fallbackKey = '') {
    if (!sensor) return '—';
    const key = sensor.key || fallbackKey;
    return formatValueForKey(key, sensor.value, sensor.unit);
}

function updateHero(data) {
    const temp = getSensorBase(data, ['temperatura', 'temperatura_interior']);
    const hum = getSensorBase(data, ['humedad', 'humedad_interior']);
    const wind = getSensorBase(data, ['viento']);
    const pressure = getSensorBase(data, ['presion', 'presion_relativa', 'presion_absoluta', 'presion_relativa_interior', 'presion_absoluta_interior']);
    if (temp) {
        const tempUnit = temp.unit || '°C';
        setText('hero-temp-value', formatValueForKey(temp.key, temp.value, tempUnit));
        const sensacion = data?.meteo?.derivadas?.sensacion_termica;
        if (sensacion && sensacion.value !== undefined && sensacion.value !== null) {
            setText('hero-feels', fmt(sensacion.value, sensacion.unit || '°C'));
        } else {
            setText('hero-feels', formatValueForKey(temp.key, temp.value, tempUnit));
        }
    }
    if (hum) {
        setText('hero-humidity', formatValueForKey(hum.key, hum.value, hum.unit || '%'));
    }
    if (wind) {
        setText('hero-wind', formatValueForKey(wind.key, wind.value, wind.unit || 'km/h'));
    }
    if (pressure) {
        setText('hero-pressure', formatValueForKey(pressure.key, pressure.value, pressure.unit || 'hPa'));
    }
    const rec = data?.recomendacion;
    if (rec && typeof rec === 'object') {
        setText('hero-summary', rec.mensaje || rec.texto || rec.text || 'Recomendación activa');
    } else {
        setText('hero-summary', rec || 'Sin recomendaciones activas');
    }
}

function updateSolar(indices) {
    if (!indices) return;
    setText('hero-sunrise', indices.amanecer || '--:--');
    setText('hero-sunset', indices.atardecer || '--:--');
    const arco = indices.arco_solar?.valor ?? indices.arco_solar;
    const duracion = indices.duracion_dia_h?.valor ?? indices.duracion_dia_h;
    setText('hero-solar-arc', arco !== undefined && arco !== null ? `${fmt(arco)}°` : '--');
    setText('hero-solar-duration', duracion !== undefined && duracion !== null ? `${fmt(duracion)} h` : '--');
    const esDia = indices.es_dia_astronomico ?? indices.es_dia_sensor;
    const lunar = indices.fase_lunar || {};
    const faseLabel = lunar?.etapa || '--';
    const direccion = lunar?.direccion ? capitalize(lunar.direccion) : '--';
    setText('hero-moon-icon', lunar?.icono || '🌙');
    setText('hero-moon-phase', faseLabel);
    setText('hero-moon-direction', direccion);
    const overlay = document.getElementById('solar-overlay');
    if (overlay) {
        overlay.classList.toggle('solar-overlay--night', esDia === false);
    }
    try {
        window._lastSolarIndices = indices;
        setTimeout(placeSolarOverlay, 60);
    } catch (e) {}
}

/* Posiciona el arco solar en la capa overlay para evitar que sea recortado por otros contenedores */
function placeSolarOverlay() {
    try {
        const overlay = document.getElementById('solar-overlay');
        const heroCard = document.querySelector('.hero-card--compact');
        if (!overlay || !heroCard) return;

        const heroRect = heroCard.getBoundingClientRect();
        const MARGIN = 16;
        const MIN_WIDTH = 120;
        const viewWidth = Math.max(window.innerWidth, document.documentElement.clientWidth);
        const availWidth = Math.max(MIN_WIDTH, Math.min(viewWidth - MARGIN * 2, heroRect.width * 1.25));
        const rawWidth = Math.max(MIN_WIDTH, Math.min(availWidth, heroRect.width * 1.15));

        // Ajustes: aumentar ligeramente tamaño del arco (más cercano a la versión previa)
        const SIZE_SCALE = 0.8; // escala del radio respecto al ancho disponible
        const radius = Math.max(30, Math.min((rawWidth / 2) * SIZE_SCALE, heroRect.height * 0.7));
        const arcWidth = radius * 2;
        const arcHeight = radius;
        // Convertir coordenadas del rect viewport a coordenadas del documento
        const scrollX = window.scrollX || window.pageXOffset || 0;
        const scrollY = window.scrollY || window.pageYOffset || 0;
        const centerX = heroRect.left + scrollX + heroRect.width / 2;
        const rawLeft = centerX - arcWidth / 2;
        const left = Math.max(MARGIN, Math.min(rawLeft, viewWidth - arcWidth - MARGIN));

        // baseline situado ligeramente por debajo de la tarjeta para "bajar" el arco (document coords)
        const baselineY = heroRect.top + scrollY + heroRect.height + 12;
        const Y_DOWN = 90; // desplazar un poco más hacia abajo
        const top = Math.max(MARGIN, baselineY - arcHeight + Y_DOWN);

        renderSolarSVG({ left, top, width: arcWidth, height: arcHeight });
    } catch (e) {
        // no bloquear la UI por errores de posicionamiento
    }
}

function renderSolarSVG(arcRect) {
    try {
        const overlay = document.getElementById('solar-overlay');
        if (!overlay || !arcRect) return;
        let svg = document.getElementById('solar-arc-svg');
        if (!svg) {
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('id', 'solar-arc-svg');
            svg.style.position = 'absolute';
            svg.style.left = '0';
            svg.style.top = '0';
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.pointerEvents = 'none';
            svg.style.zIndex = '241';
            overlay.appendChild(svg);
        }
        const viewW = Math.max(document.documentElement.scrollWidth || 0, window.innerWidth || 0, document.documentElement.clientWidth || 0);
        const viewH = Math.max(document.documentElement.scrollHeight || 0, window.innerHeight || 0, document.documentElement.clientHeight || 0);
        svg.setAttribute('viewBox', `0 0 ${viewW} ${viewH}`);
        svg.setAttribute('width', String(viewW));
        svg.setAttribute('height', String(viewH));
        svg.innerHTML = '';

        const radius = arcRect.width / 2;
        const centerX = arcRect.left + radius;
        const baseY = arcRect.top + arcRect.height;
        const arcY = baseY - radius;
        const startX = centerX - radius;
        const endX = centerX + radius;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = `M ${startX} ${arcY} A ${radius} ${radius} 0 0 1 ${endX} ${arcY}`;
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', 'rgba(255,255,255,0.18)');
        path.setAttribute('stroke-width', '1.5');
        path.setAttribute('stroke-dasharray', '8 8');
        path.setAttribute('stroke-linecap', 'round');
        svg.appendChild(path);

        const sun = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        const sunRadius = Math.max(4, Math.round(radius * 0.12));
        sun.setAttribute('r', String(sunRadius));
        sun.setAttribute('fill', '#facc15');
        sun.setAttribute('stroke', 'rgba(250,204,21,0.4)');
        sun.setAttribute('stroke-width', Math.max(1, Math.round(radius * 0.05)));
        sun.style.filter = 'drop-shadow(0 0 12px rgba(250,204,21,0.6))';
        svg.appendChild(sun);

        const indices = window._lastSolarIndices || {};
        const frac = computeSolarFraction(indices);
        if (!Number.isFinite(frac)) {
            sun.setAttribute('visibility', 'hidden');
            return;
        }
        const clamped = Math.max(0, Math.min(1, frac));
        if (clamped <= 0 || clamped >= 1) {
            sun.setAttribute('visibility', 'hidden');
            return;
        }
        const totalLen = path.getTotalLength();
        const point = path.getPointAtLength(totalLen * clamped);
        sun.setAttribute('cx', String(point.x));
        sun.setAttribute('cy', String(point.y));
        sun.setAttribute('visibility', 'visible');
        
        // Añadir textos de amanecer/atardecer centrados en los pies del arco
        try {
            const startPt = path.getPointAtLength(0);
            const endPt = path.getPointAtLength(totalLen);
            const sunriseText = document.getElementById('hero-sunrise')?.textContent || '';
            const sunsetText = document.getElementById('hero-sunset')?.textContent || '';

            const footY = baseY + Math.max(12, sunRadius + 6);
            const txtStart = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            txtStart.setAttribute('x', String(startPt.x));
            txtStart.setAttribute('y', String(footY));
            txtStart.setAttribute('fill', 'rgba(255,255,255,0.92)');
            txtStart.setAttribute('font-size', '12');
            txtStart.setAttribute('text-anchor', 'middle');
            txtStart.setAttribute('dominant-baseline', 'hanging');
            txtStart.textContent = sunriseText;
            svg.appendChild(txtStart);

            const txtEnd = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            txtEnd.setAttribute('x', String(endPt.x));
            txtEnd.setAttribute('y', String(footY));
            txtEnd.setAttribute('fill', 'rgba(255,255,255,0.92)');
            txtEnd.setAttribute('font-size', '12');
            txtEnd.setAttribute('text-anchor', 'middle');
            txtEnd.setAttribute('dominant-baseline', 'hanging');
            txtEnd.textContent = sunsetText;
            svg.appendChild(txtEnd);

            // Radiación y UV dentro del arco (si existen en índices)
            const radVal = indices.radiacion !== undefined ? (typeof indices.radiacion === 'object' ? indices.radiacion.valor ?? indices.radiacion : indices.radiacion) : null;
            const uvVal = indices.uv !== undefined ? (typeof indices.uv === 'object' ? indices.uv.valor ?? indices.uv : indices.uv) : null;
            const mid1 = path.getPointAtLength(totalLen * 0.36);
            const mid2 = path.getPointAtLength(totalLen * 0.64);
            if (radVal !== null) {
                const radTxt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                radTxt.setAttribute('x', String(mid1.x));
                radTxt.setAttribute('y', String(mid1.y - 14));
                radTxt.setAttribute('fill', 'rgba(255,255,255,0.9)');
                radTxt.setAttribute('font-size', '11');
                radTxt.setAttribute('text-anchor', 'middle');
                radTxt.textContent = `${fmt(radVal)} W/m²`;
                svg.appendChild(radTxt);
            }
            if (uvVal !== null) {
                const uvTxt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                uvTxt.setAttribute('x', String(mid2.x));
                uvTxt.setAttribute('y', String(mid2.y - 14));
                uvTxt.setAttribute('fill', 'rgba(255,255,255,0.9)');
                uvTxt.setAttribute('font-size', '11');
                uvTxt.setAttribute('text-anchor', 'middle');
                uvTxt.textContent = `UV ${fmt(uvVal)}`;
                svg.appendChild(uvTxt);
            }
        } catch (e) {
            // ignore positioning errors
        }
    } catch (e) {
        // no bloquear UI
    }
}

// Parse time string `HH:MM` or ISO to a Date on today's date (local). Returns null if invalid.
function parseTimeToToday(timeStr) {
    if (!timeStr) return null;
    try {
        if (typeof timeStr === 'number') {
            // assume seconds or ms
            const n = Number(timeStr);
            const ms = n > 1e12 ? n : (n < 1e12 ? n * 1000 : n);
            return new Date(ms);
        }
        const s = String(timeStr).trim();
        // If ISO-like, try Date parsing
        if (s.includes('T') || s.includes('-')) {
            const d = new Date(s);
            if (!Number.isNaN(d.getTime())) return d;
        }
        // HH:MM or H:MM
        const m = s.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
        if (m) {
            const now = new Date();
            const hh = Number(m[1]);
            const mm = Number(m[2]);
            const ss = m[3] ? Number(m[3]) : 0;
            const d = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mm, ss);
            return d;
        }
        // fallback: attempt Date parse
        const d2 = new Date(s);
        return Number.isNaN(d2.getTime()) ? null : d2;
    } catch (e) {
        return null;
    }
}

// Compute fraction of day [0..1] between amanecer and atardecer using indices.
function computeSolarFraction(indices) {
    try {
        if (!indices) return NaN;
        const amanecer = indices.amanecer || indices.amanecer_hibrido || indices.amanecer_astronomico || indices.amanecer_astronomico || null;
        const atardecer = indices.atardecer || indices.atardecer_hibrido || indices.atardecer_astronomico || null;
        const start = parseTimeToToday(amanecer);
        const end = parseTimeToToday(atardecer);
        if (!start || !end) return NaN;
        const now = new Date();
        const total = end.getTime() - start.getTime();
        if (total <= 0) return NaN;
        const frac = (now.getTime() - start.getTime()) / total;
        return Math.max(0, Math.min(1, frac));
    } catch (e) {
        return NaN;
    }
}

// Reposicionar al cargar estado y al cambiar tamaño de ventana
window.addEventListener('resize', () => {
    // pequeño debounce
    if (window._solarOverlayTimer) clearTimeout(window._solarOverlayTimer);
    window._solarOverlayTimer = setTimeout(() => placeSolarOverlay(), 120);
});

// Intentar posicionar periódicamente tras actualizaciones UI
const _original_loadEstado = typeof loadEstado === 'function' ? loadEstado : null;
if (_original_loadEstado) {
    // envolver la función para asegurar posicionamiento tras la carga
    window.loadEstado = async function() {
        await _original_loadEstado();
        setTimeout(placeSolarOverlay, 80);
    };
}

// Posicionar al inicializar la página
document.addEventListener('DOMContentLoaded', () => setTimeout(placeSolarOverlay, 200));

function updateSensors(data) {
    const sensors = data?.sensores || {};
    const meteo = data?.meteo?.sensores || {};
    const indices = data?.indices || {};
    const derivedMetadata = lastEstado?.sensores_derivados_metadata || {};
    const extraKeys = ['nubosidad_estimada'];
    Object.keys(sensors).forEach(key => cacheState.sensors.add(key));
    Object.keys(meteo).forEach(key => cacheState.sensors.add(key));
    extraKeys.forEach(key => {
        if (key in indices) cacheState.sensors.add(key);
    });
    const items = Array.from(cacheState.sensors)
        .filter(key => !isHiddenItem('sensor', key))
        .sort()
        .map(key => {
        const norm = meteo[key];
        const indexVal = indices[key];
        const indexValue = typeof indexVal === 'object' && indexVal !== null && 'valor' in indexVal ? indexVal.valor : indexVal;
        const unitMap = {
            nubosidad_estimada: '%',
            sonometro: 'dB',
            sismografo: '',
            uv: '',
            lluvia: 'mm/h',
            lluvia_rate: 'mm/h',
            lluvia_acumulada: 'mm',
            mqtt_temp: '°C'
        };
        const derivedInfo = derivedMetadata[key] || {};
        const unit = unitMap[key] || norm?.unit || derivedInfo.unidad || '';
        const value = sensors[key] ?? norm?.value ?? indexValue;
        const warn = value === undefined || value === null || value === '';
        return { label: getDisplayLabel(key), value, unit, key, warn, kind: 'sensor' };
    });
    setHTML('sensors-grid', renderKeyValueList(items));
}

function updateIndices(data) {
    const indices = data?.indices || {};
    Object.keys(indices).forEach(key => cacheState.indices.add(key));
    const grouped = {};
    Array.from(cacheState.indices).forEach(key => {
        if (isHiddenItem('indice', key)) return;
        const group = lightningGroupKeys.has(key) ? 'rayos' : key.split('_').slice(0, 2).join('_');
        if (!grouped[group]) grouped[group] = [];
        grouped[group].push(key);
    });
    const visibleItems = [];
    const hiddenItems = [];
    const keyPriority = {
        ultimo_rayo: 0,
        lightning_time: 0,
        rayos: 1,
        rayos_total: 1,
        distancia_rayo: 2,
        lightning: 2
    };
    Object.keys(grouped).sort().forEach(group => {
        const keys = grouped[group]
            .slice()
            .sort((a, b) => {
                const aNivel = a.includes('_nivel') ? 1 : 0;
                const bNivel = b.includes('_nivel') ? 1 : 0;
                if (aNivel !== bNivel) return aNivel - bNivel;
                const aPrio = keyPriority[a] ?? 5;
                const bPrio = keyPriority[b] ?? 5;
                if (aPrio !== bPrio) return aPrio - bPrio;
                return a.localeCompare(b, 'es');
            });
        keys.forEach((key, idx) => {
            const val = indices[key];
            const display = typeof val === 'object' && val !== null && 'valor' in val ? val.valor : val;
            const item = { label: getDisplayLabel(key), value: display, key, kind: 'indice' };
            if (idx === 0) visibleItems.push(item);
            else hiddenItems.push(item);
        });
    });
    setHTML('indices-grid', renderKeyValueList(visibleItems));
    setHTML('overlay-indices-contenido', renderList(hiddenItems));
}

function updateRecomendacion(data) {
    const rec = data?.recomendacion;
    // Log para depuración: ver qué viene en la recomendación
    try {
        console.debug('updateRecomendacion - rec raw:', rec);
    } catch (e) {
        // ignore
    }
    const recText = rec && typeof rec === 'object'
        ? (rec.estado || rec.mensaje || rec.texto || rec.text || '')
        : String(rec || '');
    const recMotivos = rec && typeof rec === 'object' && rec.motivos ? Object.values(rec.motivos) : [];
    const alerts = [...toArray(data?.meteorologico?.alertas), ...toArray(data?.intrusion?.alertas)].map(String);
    const avisos = toArray(data?.avisos_practicos).map(String);
    const indices = data?.indices || {};
    const riesgos = Object.keys(indices)
        .filter(key => key.startsWith('riesgo_') || key.startsWith('alerta_'))
        .map(key => {
            const val = indices[key];
            const display = typeof val === 'object' && val !== null && 'valor' in val ? val.valor : val;
            const normalized = normalizeNumeric(display);
            return normalized !== null && normalized >= 50 ? key : null;
        })
        .filter(Boolean);

    const signals = [...alerts, ...avisos, ...riesgos, ...recMotivos].filter(Boolean);
    const hasSignals = signals.length > 0;

    // Heurísticas para construir una frase unificada y coloquial
    function getNumericIndex(key) {
        const v = indices[key];
        if (v === undefined || v === null) return null;
        return typeof v === 'object' && 'valor' in v ? normalizeNumeric(v.valor) : normalizeNumeric(v);
    }

    const sensacion = getNumericIndex('sensacion_termica') || (data?.meteo?.derivadas?.sensacion_termica?.value ?? null);
    const nub = getNumericIndex('nubosidad_estimada') || null;
    const lluviaRisk = getNumericIndex('riesgo_lluvia') || getNumericIndex('lluvia') || null;

    const parts = [];
    // Temperatura / sensación
    if (sensacion !== null) {
        parts.push(`Hace ${sensacion < 15 ? 'fresco' : (sensacion > 25 ? 'calor' : 'bueno')}`);
    }

    // Nubosidad y luminosidad
    if (nub !== null) {
        if (nub >= 80) parts.push('hay muchas nubes');
        else if (nub >= 40) parts.push('hay bastantes nubes');
        else parts.push('hay pocas nubes');
        if (nub >= 70) parts.push('y el día está bastante oscuro');
        else if (nub >= 40) parts.push('y el día está algo poco soleado');
    }

    // Recomendaciones prácticas (abrigo, paraguas)
    const actions = [];
    if (sensacion !== null && sensacion < 15) actions.push('abrígate');
    if (lluviaRisk !== null) {
        if (lluviaRisk >= 60) actions.push('lleva paraguas, hay alto riesgo de lluvia');
        else if (lluviaRisk >= 30) actions.push('coge paraguas, riesgo moderado de lluvia');
    }

    // Cetrería (si aparece en motivos)
    const cetreriaActive = recMotivos.some(m => String(m).toLowerCase().includes('cetrer'));
    // Polvo / mala calidad del aire (interior detection heuristic)
    const polvoIndex = getNumericIndex('alerta_polvo') || getNumericIndex('riesgo_polvo') || null;
    let polvoText = '';
    if (polvoIndex !== null && polvoIndex >= 60) {
        // intentar detectar si el sensor que mide PM25 está en interior
        const sensoresKeys = Object.keys(data?.sensores || {});
        const pmInterior = sensoresKeys.some(k => k.toLowerCase().includes('pm25') && (k.toLowerCase().includes('in') || k.toLowerCase().includes('interior') || k.toLowerCase().includes('inside')));
        polvoText = `Riesgo alto de polvo o mala calidad del aire ${pmInterior ? 'en casa' : ''}`.trim();
    }

    // Unificar la frase
    const mainPhrase = [];
    if (parts.length) mainPhrase.push(parts.join(', '));
    if (actions.length) mainPhrase.push(actions.join(' y '));
    let finalText = mainPhrase.join('. ');
    if (finalText) finalText = finalText.replace(/\s+\./g, '.');
    if (cetreriaActive) finalText += (finalText ? '. ' : '') + 'Aun así, es un día aceptable para la cetrería.';
    if (polvoText) finalText += (finalText ? ' ' : '') + polvoText + '.';

    // Fallback: si no hay señales ni texto, decir que no hay recomendaciones
    let text = '';
    if (hasSignals) {
        text = finalText || signals.slice(0, 4).join(' · ');
    } else {
        text = 'Sin recomendaciones';
    }

    const friendly = makeFriendlyTone(text);
    setText('recomendacion', friendly);
    setText('hero-recommendation-detail', friendly);
    const moodText = hasSignals ? 'Recomendación activa' : 'Sin recomendaciones activas';
    setText('hero-summary', moodText);
    if (hasSignals) {
        const summary = signals.slice(0, 4).join(' · ');
        setHTML('recommendation-summary', `<span>${summary}</span>`);
    } else {
        setHTML('recommendation-summary', '');
    }

    const changedRec = String(friendly || '') !== String(cacheState.lastRec || '');
    const changedSignals = signals.join('|') !== cacheState.lastSignals.join('|');
    if (hasSignals && (changedRec || changedSignals)) {
        const entry = {
            text: friendly,
            ts: new Date().toLocaleString('es-ES'),
            signals: signals.slice(0, 6)
        };
        cacheState.recHistory.unshift(entry);
        cacheState.recHistory = cacheState.recHistory.slice(0, 20);
        cacheState.lastRec = friendly;
        cacheState.lastSignals = signals.slice(0, 12);
    }

    if (!hasSignals && cacheState.lastRec && cacheState.lastSignals.length) {
        const entry = {
            text: `Finalizada: ${cacheState.lastRec}`,
            ts: new Date().toLocaleString('es-ES'),
            signals: ['sin señales activas']
        };
        cacheState.recHistory.unshift(entry);
        cacheState.recHistory = cacheState.recHistory.slice(0, 20);
        cacheState.lastRec = null;
        cacheState.lastSignals = [];
    }

    if (cacheState.recHistory.length) {
        setHTML(
            'overlay-historico-contenido',
            renderList(cacheState.recHistory.map(item => ({
                label: item.ts,
                value: `${item.text}${item.signals?.length ? ` (${item.signals.join(', ')})` : ''}`
            })))
        );
    }
}

// Transforma una frase en un tono más coloquial, cariñoso y un poco bromista.
function makeFriendlyTone(text) {
    if (!text || text === 'Sin recomendaciones') return text;
    // Pequeñas transformaciones para suavizar y unir frases
    let t = String(text).trim();
    // Replaces comunes para evitar estilo telegrama
    t = t.replace(/\bHace\s+fresco\b/gi, 'Hace fresco');
    t = t.replace(/\bHace\s+calor\b/gi, 'Hace calor');
    // Añadir conectores más naturales
    t = t.replace(/\.(\s*)/g, ', ');
    t = t.replace(/\s+,/g, ',');
    // Limpiar repeticiones de comas
    t = t.replace(/,\s*,/g, ',');
    // Añadir prefacio cariñoso y remate afectuoso
    const prefix = 'Oye,';
    const suffix = ' Cuídate ❤️';
    // Capitalizar primera letra después del prefijo
    t = t.charAt(0).toLowerCase() === t.charAt(0) ? t.charAt(0).toUpperCase() + t.slice(1) : t;
    return `${prefix} ${t.trim()}.${suffix}`;
}

function updateAlertas(data) {
    const alerts = [];
    const meteo = data?.meteorologico?.alertas || [];
    alerts.push(...meteo.map(String));
    const intrusion = data?.intrusion?.alertas || [];
    alerts.push(...intrusion.map(String));
    const formatted = alerts.map((alert, idx) => ({ label: `Alerta ${idx + 1}`, value: alert }));
    setHTML('alertas', renderList(formatted));
}

function updateRiesgos(data) {
    const riesgos = [];
    const avisos = toArray(data?.avisos_practicos);
    riesgos.push(...avisos.map(String));
    const indices = data?.indices || {};
    Object.keys(indices).forEach(key => {
        if (!(key.startsWith('riesgo_') || key.startsWith('alerta_'))) return;
        const val = indices[key];
        const display = typeof val === 'object' && val !== null && 'valor' in val ? val.valor : val;
        if (display === undefined || display === null || display === '') return;
        riesgos.push({ label: getDisplayLabel(key), value: formatValueForKey(key, display), key, kind: 'indice' });
    });
    setHTML('riesgos', renderList(riesgos));
}

function updateSensorHealth(data) {
    const sensors = data?.sensores || {};
    const meteo = data?.meteo?.sensores || {};
    const issues = [];
    Array.from(cacheState.sensors).forEach(key => {
        const norm = meteo[key];
        const value = norm?.value ?? sensors[key];
        if (value === undefined || value === null || value === '') {
            issues.push({ label: key, value: 'Sin datos' });
        }
    });
    setHTML('sensores-alertas', renderList(issues));
}

function updateOrganizer(data) {
    const org = data?.organizacion || {};
    setHTML('asistente-noticias', renderList([{ label: 'Resumen', value: org.noticias || 'Sin novedades' }]));
    setHTML('asistente-eventos', renderList((org.eventos || []).map(evento => ({ label: evento.titulo || 'Evento', value: evento.hora || 'Hora desconocida' }))));
    setHTML('asistente-alarmas', renderList((org.alarmas || []).map(alarma => ({ label: alarma.hora || '--:--', value: alarma.recurrencia || 'Sin recurrencia' }))));
    setHTML('asistente-tareas', renderList((org.tareas || []).map(tarea => ({ label: tarea.titulo || 'Tarea', value: `P${tarea.prioridad || 0}` }))));
    setHTML('asistente-compra', renderList((org.lista_compra || []).map(item => ({ label: item.item || item.nombre || 'Producto', value: item.categoria || 'General' }))));
    setHTML('asistente-impresion', renderList((org.cola_impresion || []).map(item => ({ label: item.texto || item.documento || 'Impresión', value: '' }))));
    setHTML('asistente-recomendaciones', renderList((org.recomendaciones || []).map(rec => ({ label: rec, value: '' }))));
    const asistente = data?.asistente || {};
    setHTML('asistente-eventos-sugerencias', renderList((asistente.sugerencias_eventos || []).map(String)));
    setHTML('asistente-tareas-sugerencias', renderList((asistente.sugerencias_tareas || []).map(String)));
    setHTML('asistente-compra-sugerencias', renderList((asistente.sugerencias_compra || []).map(String)));

    setHTML('overlay-noticias-contenido', renderList([{ label: 'Noticias', value: org.noticias || 'Sin novedades' }]));
    setHTML('overlay-tareas-contenido', renderList((org.tareas || []).map(tarea => ({
        label: tarea.titulo || 'Tarea',
        value: `P${tarea.prioridad || 0}`
    }))));
}

function updateEffects(data) {
    const lluvia = Number(getSensorValue(data, key => key.includes('lluvia'))?.value || 0);
    const viento = Number(getSensorValue(data, key => key.includes('viento'))?.value || 0);
    const nubosidad = Number(data?.indices?.nubosidad_estimada?.valor || data?.indices?.nubosidad_estimada || 0);
    let estado = 'sol';
    let intensidad = 0.3;
    if (lluvia > 0) estado = 'lluvia';
    else if (viento > 6) estado = 'viento';
    else if (nubosidad > 60) estado = 'nubes';
    if (estado === 'lluvia') intensidad = Math.min(1, lluvia / 20);
    if (estado === 'viento') intensidad = Math.min(1, viento / 12);
    if (estado === 'nubes') intensidad = Math.min(1, nubosidad / 100);
    if (typeof activarEfectoMeteo === 'function') activarEfectoMeteo(estado, intensidad);
}

async function loadEstado() {
    let data;
    try {
        data = await fetchJSON(STATE_URL);
    } catch (err) {
        console.error('Error fetching /estado', err);
        setText('recomendacion', 'Error al cargar estado');
        return;
    }
    try {
        lastEstado = data;
        // Mostrar recomendación primero para evitar que fallos en otras
        // actualizaciones impidan que el usuario vea recomendaciones.
        try {
            updateRecomendacion(data);
        } catch (recErr) {
            console.error('Error updating recommendation', recErr);
        }
        updateLocation(data.indices);
        updateContextMetadata(data);
        updateHero(data);
        updateSolar(data.indices);
        updateSensors(data);
        updateIndices(data);
        updateAlertas(data);
        updateRiesgos(data);
        updateOrganizer(data);
        updateSensorHealth(data);
        updateEffects(data);
        renderSubmenuHiddenList();
        const tempKey = getSensorNormalized(data, key => key.includes('temp'))?.key;
        const humKey = getSensorNormalized(data, key => key.includes('humedad') || key.includes('hum'))?.key;
        if (tempKey && humKey) {
            await updateCharts(tempKey, humKey);
        }
    } catch (err) {
        console.error('Error updating estado UI', err);
    }
}

    async function sendVirtualSensor(name, value, unit = '', reliability = 80) {
        try {
            await fetchJSON('/sensor_virtual', {
                method: 'POST',
                body: JSON.stringify({
                    name,
                    value,
                    unit,
                    type: name,
                    source: 'frontend',
                    origin: 'device',
                    reliability
                })
            });
        } catch (err) {
            // ignore
        }
    }

    async function initLocalSonometer() {
        if (!navigator.mediaDevices?.getUserMedia) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 2048;
            source.connect(analyser);
            const data = new Float32Array(analyser.fftSize);
            setInterval(() => {
                analyser.getFloatTimeDomainData(data);
                let sum = 0;
                for (let i = 0; i < data.length; i++) {
                    sum += data[i] * data[i];
                }
                const rms = Math.sqrt(sum / data.length);
                let db = 20 * Math.log10(rms || 1e-6);
                db = Math.max(0, Math.min(120, db + 100));
                sendVirtualSensor('sonometro', Number(db.toFixed(1)), 'dB', 70);
            }, 1500);
        } catch (err) {
            // mic denied or not available
        }
    }

    function initLocalSeismometer() {
        if (!('DeviceMotionEvent' in window)) return;
        let lastSend = 0;
        window.addEventListener('devicemotion', event => {
            const accel = event.accelerationIncludingGravity || event.acceleration;
            if (!accel) return;
            const ax = accel.x || 0;
            const ay = accel.y || 0;
            const az = accel.z || 0;
            const magnitude = Math.sqrt(ax * ax + ay * ay + az * az);
            const now = Date.now();
            if (now - lastSend < 1500) return;
            lastSend = now;
            sendVirtualSensor('sismografo', Number(magnitude.toFixed(3)), 'm/s²', 70);
        });
    }

function initOverlays() {
    const openButtons = document.querySelectorAll('[data-overlay-target]');
    openButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-overlay-target');
            const overlay = document.getElementById(id);
            if (!overlay) return;
            overlay.classList.add('is-active');
        });
    });

    document.querySelectorAll('.overlay').forEach(overlay => {
        overlay.addEventListener('click', event => {
            if (event.target === overlay || event.target.hasAttribute('data-overlay-close')) {
                overlay.classList.remove('is-active');
            }
        });
    });
}

let currentSubmenuItem = null;

function openSubmenu(kind, key) {
    if (!key) return;
    currentSubmenuItem = { kind, key };
    const sensores = lastEstado?.sensores || {};
    const indices = lastEstado?.indices || {};
    const indicesCatalogo = lastEstado?.indices_catalogo || {};
    const meta = lastEstado?.sensores_metadata?.[key] || lastEstado?.sensores_derivados_metadata?.[key] || {};
    let value = '—';
    let unit = '';
    let descripcion = '';
    if (kind === 'sensor') {
        value = sensores[key];
        unit = meta.unidad || '';
        descripcion = meta.explicacion || meta.descripcion || sensorDescriptionMap[key] || 'Sensor físico o derivado.';
    } else {
        const raw = indices[key];
        const info = typeof raw === 'object' && raw !== null ? raw : { valor: raw };
        value = info?.valor ?? raw;
        unit = indicesCatalogo?.[key]?.unidad || '';
        descripcion = info?.explicacion || indicesCatalogo?.[key]?.descripcion || 'Índice calculado.';
    }
    setText('submenu-item-title', getDisplayLabel(key));
    setText('submenu-item-key', key);
    setText('submenu-item-value', formatValueForKey(key, value, unit));
    setText('submenu-item-unit', unit || '—');
    setText('submenu-item-description', descripcion || '—');

    const renameInput = document.getElementById('submenu-rename-input');
    if (renameInput) renameInput.value = userPrefs.labels?.[key] || '';

    const hideBtn = document.getElementById('submenu-hide-toggle');
    if (hideBtn) {
        const hidden = isHiddenItem(kind, key);
        hideBtn.textContent = hidden ? 'Mostrar' : 'Ocultar';
        hideBtn.dataset.hidden = hidden ? '1' : '0';
    }
    renderSubmenuHiddenList();
    document.getElementById('overlay-submenu')?.classList.add('is-active');
}

function renderSubmenuHiddenList() {
    const container = document.getElementById('submenu-hidden-list');
    if (!container) return;
    const items = [];
    cacheState.sensors.forEach(key => {
        if (isHiddenItem('sensor', key) || isBaseHiddenSensor(key)) {
            items.push({ kind: 'sensor', key, forced: isBaseHiddenSensor(key) });
        }
    });
    cacheState.indices.forEach(key => {
        if (isHiddenItem('indice', key) || isBaseHiddenIndex(key)) {
            items.push({ kind: 'indice', key, forced: isBaseHiddenIndex(key) });
        }
    });
    if (!items.length) {
        container.innerHTML = '<div class="data-item">Sin ocultos</div>';
        return;
    }
    container.innerHTML = items
        .sort((a, b) => a.key.localeCompare(b.key, 'es'))
        .map(item => {
            const label = getDisplayLabel(item.key);
            const tag = item.forced ? 'Sistema' : 'Usuario';
            const actionLabel = isHiddenItem(item.kind, item.key) ? 'Mostrar' : 'Ocultar';
            return `
                <div class="submenu-item">
                    <div>
                        <strong>${label}</strong>
                        <div class="panel-subtitle">${item.key} · ${tag}</div>
                    </div>
                    <button class="console-btn" data-submenu-toggle data-kind="${item.kind}" data-key="${item.key}">${actionLabel}</button>
                </div>
            `;
        })
        .join('');
}

function initSubmenuControls() {
    const renameSave = document.getElementById('submenu-rename-save');
    const renameReset = document.getElementById('submenu-rename-reset');
    const renameInput = document.getElementById('submenu-rename-input');
    const hideBtn = document.getElementById('submenu-hide-toggle');
    const list = document.getElementById('submenu-hidden-list');
    const scaleInput = document.getElementById('ui-scale-input');
    const compactToggle = document.getElementById('ui-compact-toggle');

    if (renameSave) {
        renameSave.addEventListener('click', () => {
            if (!currentSubmenuItem) return;
            const value = (renameInput?.value || '').trim();
            if (value) {
                userPrefs.labels[currentSubmenuItem.key] = value;
            }
            saveUserPrefs();
            renderSubmenuHiddenList();
            loadEstado();
        });
    }
    if (renameReset) {
        renameReset.addEventListener('click', () => {
            if (!currentSubmenuItem) return;
            delete userPrefs.labels[currentSubmenuItem.key];
            saveUserPrefs();
            if (renameInput) renameInput.value = '';
            renderSubmenuHiddenList();
            loadEstado();
        });
    }
    if (hideBtn) {
        hideBtn.addEventListener('click', () => {
            if (!currentSubmenuItem) return;
            const kind = currentSubmenuItem.kind;
            const key = currentSubmenuItem.key;
            const currentlyHidden = isHiddenItem(kind, key);
            if (isBaseHiddenSensor(key) || isBaseHiddenIndex(key)) {
                setForceShow(kind, key, currentlyHidden);
            } else {
                setHiddenItem(kind, key, !currentlyHidden);
            }
            renderSubmenuHiddenList();
            loadEstado();
            const hiddenNow = isHiddenItem(kind, key);
            hideBtn.textContent = hiddenNow ? 'Mostrar' : 'Ocultar';
            hideBtn.dataset.hidden = hiddenNow ? '1' : '0';
        });
    }
    if (list) {
        list.addEventListener('click', event => {
            const btn = event.target.closest('[data-submenu-toggle]');
            if (!btn) return;
            const kind = btn.getAttribute('data-kind');
            const key = btn.getAttribute('data-key');
            if (!kind || !key) return;
            const currentlyHidden = isHiddenItem(kind, key);
            if (isBaseHiddenSensor(key) || isBaseHiddenIndex(key)) {
                setForceShow(kind, key, currentlyHidden);
            } else {
                setHiddenItem(kind, key, !currentlyHidden);
            }
            renderSubmenuHiddenList();
            loadEstado();
        });
    }
    if (scaleInput) {
        scaleInput.addEventListener('input', () => {
            userPrefs.uiScale = parseFloat(scaleInput.value);
            applyUiPrefs();
            saveUserPrefs();
        });
    }
    if (compactToggle) {
        compactToggle.addEventListener('change', () => {
            userPrefs.uiCompact = compactToggle.checked;
            applyUiPrefs();
            saveUserPrefs();
        });
    }
}

function initItemSubmenu() {
    document.addEventListener('click', event => {
        const sensorItem = event.target.closest('[data-sensor-key]');
        if (sensorItem) {
            const key = sensorItem.getAttribute('data-sensor-key');
            if (key) openSubmenu('sensor', key);
            return;
        }
        const indiceItem = event.target.closest('[data-index-key]') || event.target.closest('[data-indice-key]');
        if (indiceItem) {
            const key = indiceItem.getAttribute('data-index-key') || indiceItem.getAttribute('data-indice-key');
            if (key) openSubmenu('indice', key);
        }
    });
}

function initIndiceDetalle() {
    const container = document.getElementById('indices-grid');
    const overlayContainer = document.getElementById('overlay-indices-contenido');
    const handler = event => {
        const item = event.target.closest('[data-index-key]') || event.target.closest('[data-indice-key]');
        if (!item) return;
        const key = item.getAttribute('data-index-key') || item.getAttribute('data-indice-key');
        openSubmenu('indice', key);
    };
    if (container) container.addEventListener('click', handler);
    if (overlayContainer) overlayContainer.addEventListener('click', handler);
}

function initSensorDetalle() {
    const container = document.getElementById('sensors-grid');
    if (!container) return;
    container.addEventListener('click', event => {
        const item = event.target.closest('[data-sensor-key]');
        if (!item) return;
        const key = item.getAttribute('data-sensor-key');
        openSubmenu('sensor', key);
    });
}

function initDraggablePanels() {
    const grid = document.querySelector('.dashboard-grid');
    if (!grid) return;
    const panels = Array.from(grid.children);
    panels.forEach(panel => {
        panel.addEventListener('dblclick', () => {
            const draggable = panel.getAttribute('draggable') === 'true';
            panel.setAttribute('draggable', draggable ? 'false' : 'true');
        });
        panel.addEventListener('dragstart', event => {
            panel.classList.add('dragging');
            event.dataTransfer.setData('text/plain', panel.id || '');
        });
        panel.addEventListener('dragend', () => {
            panel.classList.remove('dragging');
            savePanelOrder(grid);
        });
    });
    grid.addEventListener('dragover', event => {
        event.preventDefault();
        const dragging = grid.querySelector('.dragging');
        const afterElement = getDragAfterElement(grid, event.clientY);
        if (!dragging) return;
        if (afterElement == null) {
            grid.appendChild(dragging);
        } else {
            grid.insertBefore(dragging, afterElement);
        }
    });
    restorePanelOrder(grid);
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.panel[draggable="true"]:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset, element: child };
        }
        return closest;
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function savePanelOrder(grid) {
    const order = Array.from(grid.children).map(panel => panel.id).filter(Boolean);
    localStorage.setItem('meteoser-panel-order', JSON.stringify(order));
}

function restorePanelOrder(grid) {
    const order = JSON.parse(localStorage.getItem('meteoser-panel-order') || '[]');
    if (!order.length) return;
    order.forEach(id => {
        const panel = document.getElementById(id);
        if (panel) grid.appendChild(panel);
    });
}

function bindActions() {
    const actionConfig = {
        'news-refresh': {
            method: 'POST',
            url: '/asistente/noticias',
            buildPayload: () => {
                const cats = (document.getElementById('news-categories')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                return { categorias: cats };
            }
        },
        'add-evento': {
            method: 'POST',
            url: '/asistente/eventos',
            buildPayload: () => ({
                titulo: document.getElementById('evento-titulo')?.value,
                hora: document.getElementById('evento-hora')?.value,
                canal: document.getElementById('evento-canal')?.value,
                duracion: document.getElementById('evento-duracion')?.value
            })
        },
        'add-alarma': {
            method: 'POST',
            url: '/asistente/alarmas',
            buildPayload: () => ({
                hora: document.getElementById('alarma-hora')?.value,
                recurrencia: document.getElementById('alarma-recurrencia')?.value,
                aviso_min: document.getElementById('alarma-aviso')?.value
            })
        },
        'update-alarma': {
            method: 'POST',
            url: '/asistente/alarmas/update',
            buildPayload: () => ({
                index: document.getElementById('alarma-index')?.value,
                hora: document.getElementById('alarma-hora')?.value,
                recurrencia: document.getElementById('alarma-recurrencia')?.value,
                aviso_min: document.getElementById('alarma-aviso')?.value
            })
        },
        'toggle-alarma': {
            method: 'POST',
            url: '/asistente/alarmas/toggle',
            buildPayload: () => ({
                index: document.getElementById('alarma-index')?.value
            })
        },
        'add-tarea': {
            method: 'POST',
            url: '/asistente/tareas',
            buildPayload: () => ({
                titulo: document.getElementById('tarea-titulo')?.value,
                prioridad: document.getElementById('tarea-prioridad')?.value
            })
        },
        'add-compra': {
            method: 'POST',
            url: '/asistente/lista_compra',
            buildPayload: () => ({
                item: document.getElementById('compra-item')?.value,
                categoria: document.getElementById('compra-categoria')?.value
            })
        },
        'add-impresion': {
            method: 'POST',
            url: '/asistente/impresion',
            buildPayload: () => ({
                texto: document.getElementById('impresion-texto')?.value,
                tipo: document.getElementById('impresion-tipo')?.value
            })
        },
        'add-recomendaciones': {
            method: 'POST',
            url: '/asistente/recomendaciones',
            buildPayload: () => {
                const raw = (document.getElementById('reco-sugerencias')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
                return { sugerencias: raw };
            }
        }
    };
    document.querySelectorAll('.console-btn[data-action]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const action = btn.getAttribute('data-action');
            const config = actionConfig[action];
            if (!config) return;
            try {
                const payload = config.buildPayload();
                await fetchJSON(config.url, {
                    method: config.method,
                    body: JSON.stringify(payload)
                });
            } catch (err) {
                // ignore failures for now
            }
            await loadEstado();
        });
    });
}

async function sendVoiceText(text) {
    if (!text) return;
    try {
        const payload = { text, session_id: voiceSessionId };
        const resp = await fetchJSON('/voz/texto', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (resp?.session_id) voiceSessionId = resp.session_id;
        if (resp?.text) {
            setText('voice-output', resp.text);
            const played = playServerAudio(resp);
            if (!played) {
                speakText(resp.text);
            }
        }
    } catch (err) {
        setText('voice-output', 'Error al enviar voz.');
    }
}

function playServerAudio(resp) {
    const audioBase64 = resp?.audio_base64;
    if (!audioBase64) return false;
    const mime = resp?.audio_mime || 'audio/wav';
    try {
        const audio = new Audio(`data:${mime};base64,${audioBase64}`);
        audio.play();
        return true;
    } catch (err) {
        return false;
    }
}

function speakText(text) {
    if (!text || !('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = 'es-ES';
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
}

function initVoiceControls() {
    const btn = document.getElementById('voice-start-btn');
    const sendBtn = document.getElementById('voice-send-btn');
    const input = document.getElementById('voice-text-input');
    const status = document.getElementById('voice-status');
    const visual = document.querySelector('.voice-visual');
    if (sendBtn && input) {
        sendBtn.addEventListener('click', () => sendVoiceText(input.value));
    }

    if (!btn) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        if (status) status.textContent = 'Reconocimiento de voz no disponible en este navegador.';
        return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    recognition.onstart = () => {
        if (status) status.textContent = 'Escuchando...';
        if (visual) visual.classList.add('is-listening');
    };
    recognition.onerror = () => {
        if (status) status.textContent = 'Error de reconocimiento.';
        if (visual) visual.classList.remove('is-listening');
    };
    recognition.onend = () => {
        if (status) status.textContent = 'Listo.';
        if (visual) visual.classList.remove('is-listening');
    };
    recognition.onresult = event => {
        const text = event.results?.[0]?.[0]?.transcript || '';
        if (input) input.value = text;
        sendVoiceText(text);
    };
    btn.addEventListener('click', () => recognition.start());
}

function updateClock() {
    const now = new Date();
    const seasonInfo = getSeasonInfo(now);
    const fecha = now.toLocaleDateString('es-ES');
    const hora = now.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'});
    const html = `${seasonInfo.icon} ${seasonInfo.name} — ${fecha} / ${hora}`;
    setHTML('fecha-hora', html);
    // enviar la hora del dashboard al servidor cada 30s
    if (!window._lastClientTimeSent || (Date.now() - window._lastClientTimeSent) > 30000) {
        postClientTime(now.toISOString());
        window._lastClientTimeSent = Date.now();
    }
}

function setHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

function getSeasonInfo(dt) {
    const m = dt.getMonth() + 1; // 1-12
    // Meteorological seasons (northern hemisphere)
    if (m === 12 || m === 1 || m === 2) return {name: 'Invierno', icon: '❄️'};
    if (m >= 3 && m <= 5) return {name: 'Primavera', icon: '🌱'};
    if (m >= 6 && m <= 8) return {name: 'Verano', icon: '☀️'};
    return {name: 'Otoño', icon: '🍂'};
}

async function postClientTime(iso) {
    try {
        await fetch('/client_time', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({iso: iso}),
        });
    } catch (err) {
        // no bloquear si falla
        console.debug('postClientTime error', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadUserPrefs();
    applyUiPrefs();
    updateClock();
    setInterval(updateClock, 1000);
    initOverlays();
    initIndiceDetalle();
    initSensorDetalle();
    initItemSubmenu();
    initSubmenuControls();
    initDraggablePanels();
    bindActions();
    initVoiceControls();
    loadEstado();
    setInterval(loadEstado, 10000);
    initLocalSonometer();
    initLocalSeismometer();
});


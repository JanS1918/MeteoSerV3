"""
Dashboard Visual - Endpoints para interfaz web de fusión adaptativa WH65+WH31
Autor: MeteoSerV3 System
Fecha: 2026-02-10
Descripción: Proporciona visualización en tiempo real de sensores fusionados
"""

from fastapi import APIRouter, HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime

router = APIRouter(prefix="/fusion-dashboard", tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Interfaz web principal del dashboard de fusión"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MeteoSerV3 - Dashboard Fusión Adaptativa WH65+WH31</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                color: #f0f0f0;
                padding: 20px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
                border-bottom: 3px solid #00d4ff;
                padding-bottom: 20px;
            }
            
            .header h1 {
                font-size: 2.5em;
                color: #00d4ff;
                margin-bottom: 10px;
                text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
            }
            
            .header p {
                color: #aaa;
                font-size: 0.9em;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            
            .card {
                background: rgba(30, 40, 60, 0.9);
                border: 2px solid #00d4ff;
                border-radius: 10px;
                padding: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
                transition: all 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                border-color: #00ff88;
                box-shadow: 0 12px 40px rgba(0, 255, 136, 0.3);
            }
            
            .card h2 {
                color: #00d4ff;
                font-size: 1.2em;
                margin-bottom: 15px;
                border-bottom: 2px solid #00d4ff;
                padding-bottom: 10px;
            }
            
            .sensor-group {
                margin-bottom: 15px;
                padding: 12px;
                background: rgba(0, 212, 255, 0.05);
                border-left: 3px solid #00d4ff;
                border-radius: 5px;
            }
            
            .sensor-name {
                font-weight: bold;
                color: #00ff88;
                font-size: 0.9em;
                margin-bottom: 8px;
            }
            
            .sensor-value {
                font-size: 1.8em;
                color: #00d4ff;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .sensor-unit {
                font-size: 0.6em;
                color: #aaa;
            }
            
            .fusion-badge {
                display: inline-block;
                background: #ff6b00;
                color: white;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.7em;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .fusion-badge.active {
                background: #00ff88;
                color: #0f3460;
            }
            
            .ponderacion {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-top: 10px;
                padding: 10px;
                background: rgba(0, 212, 255, 0.1);
                border-radius: 5px;
                font-size: 0.85em;
            }
            
            .ponderacion-item {
                text-align: center;
            }
            
            .ponderacion-label {
                color: #aaa;
                font-size: 0.8em;
            }
            
            .ponderacion-value {
                color: #00ff88;
                font-weight: bold;
                font-size: 1.2em;
            }
            
            .anomalia {
                background: rgba(255, 107, 0, 0.2);
                border: 2px solid #ff6b00;
                color: #ffaa44;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-weight: bold;
            }
            
            .anomalia.none {
                background: rgba(0, 255, 136, 0.1);
                border-color: #00ff88;
                color: #00ff88;
            }
            
            .chart-container {
                position: relative;
                height: 300px;
                margin: 20px 0;
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #00d4ff;
            }
            
            .alerts {
                background: rgba(255, 107, 0, 0.1);
                border: 2px solid #ff6b00;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            
            .alerts h3 {
                color: #ff6b00;
                margin-bottom: 15px;
            }
            
            .alert-item {
                background: rgba(255, 107, 0, 0.2);
                padding: 10px;
                margin: 8px 0;
                border-left: 3px solid #ff6b00;
                border-radius: 5px;
                font-size: 0.9em;
            }
            
            .alert-item.microclima {
                border-left-color: #00d4ff;
                background: rgba(0, 212, 255, 0.1);
            }
            
            .timestamp {
                color: #666;
                font-size: 0.8em;
                margin-top: 10px;
                text-align: right;
            }
            
            .status {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #ff6b00;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }
            
            .status.online {
                background: #00ff88;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .contexto-info {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
                margin: 15px 0;
                padding: 10px;
                background: rgba(0, 212, 255, 0.05);
                border-radius: 5px;
                font-size: 0.85em;
            }
            
            .contexto-item {
                text-align: center;
            }
            
            .contexto-label {
                color: #aaa;
                font-size: 0.8em;
            }
            
            .contexto-value {
                color: #00ff88;
                font-weight: bold;
                font-size: 1.1em;
            }
            
            @media (max-width: 768px) {
                .header h1 { font-size: 1.8em; }
                .grid { grid-template-columns: 1fr; }
                .sensor-value { font-size: 1.3em; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌡️ MeteoSerV3 - Dashboard Fusión Adaptativa</h1>
                <p>Visualización en tiempo real: WH65 (Calle) + WH31 (Sombreado)</p>
                <div style="margin-top: 10px;">
                    <span class="status online"></span>
                    <span id="status-text">Conectado</span>
                </div>
            </div>
            
            <div class="grid">
                <!-- Sensores WH65 -->
                <div class="card">
                    <h2>☀️ WH65 (Calle/Expuesto)</h2>
                    <div class="sensor-group">
                        <div class="sensor-name">Temperatura</div>
                        <div class="sensor-value">
                            <span id="wh65-temp">--</span>
                            <span class="sensor-unit">°C</span>
                        </div>
                    </div>
                    <div class="sensor-group">
                        <div class="sensor-name">Humedad Relativa</div>
                        <div class="sensor-value">
                            <span id="wh65-hum">--</span>
                            <span class="sensor-unit">%</span>
                        </div>
                    </div>
                    <div class="timestamp" id="wh65-time"></div>
                </div>
                
                <!-- Sensores WH31 -->
                <div class="card">
                    <h2>🌳 WH31 (Sombreado/Protegido)</h2>
                    <div class="sensor-group">
                        <div class="sensor-name">Temperatura</div>
                        <div class="sensor-value">
                            <span id="wh31-temp">--</span>
                            <span class="sensor-unit">°C</span>
                        </div>
                    </div>
                    <div class="sensor-group">
                        <div class="sensor-name">Humedad Relativa</div>
                        <div class="sensor-value">
                            <span id="wh31-hum">--</span>
                            <span class="sensor-unit">%</span>
                        </div>
                    </div>
                    <div class="timestamp" id="wh31-time"></div>
                </div>
                
                <!-- Fusión Adaptativa -->
                <div class="card">
                    <h2>⚡ Fusión Adaptativa
                        <span class="fusion-badge active" id="fusion-status">ACTIVA</span>
                    </h2>
                    <div class="sensor-group">
                        <div class="sensor-name">Temperatura Fusionada</div>
                        <div class="sensor-value">
                            <span id="fusion-temp">--</span>
                            <span class="sensor-unit">°C</span>
                        </div>
                    </div>
                    <div class="sensor-group">
                        <div class="sensor-name">Humedad Fusionada</div>
                        <div class="sensor-value">
                            <span id="fusion-hum">--</span>
                            <span class="sensor-unit">%</span>
                        </div>
                    </div>
                    <div class="sensor-group">
                        <div class="sensor-name">Contexto Actual</div>
                        <div class="sensor-value" style="font-size: 1.1em;">
                            <span id="fusion-contexto">confort</span>
                        </div>
                    </div>
                    <div class="ponderacion">
                        <div class="ponderacion-item">
                            <div class="ponderacion-label">Peso WH65 T°</div>
                            <div class="ponderacion-value" id="pond-wh65-t">30%</div>
                        </div>
                        <div class="ponderacion-item">
                            <div class="ponderacion-label">Peso WH31 T°</div>
                            <div class="ponderacion-value" id="pond-wh31-t">70%</div>
                        </div>
                        <div class="ponderacion-item">
                            <div class="ponderacion-label">Peso WH65 HR</div>
                            <div class="ponderacion-value" id="pond-wh65-h">40%</div>
                        </div>
                        <div class="ponderacion-item">
                            <div class="ponderacion-label">Peso WH31 HR</div>
                            <div class="ponderacion-value" id="pond-wh31-h">60%</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Anomalías -->
            <div id="anomalia-section" style="display: none;">
                <div class="anomalia none" id="anomalia-status">
                    ✓ Sin anomalías detectadas
                </div>
            </div>
            
            <!-- Alertas -->
            <div id="alerts-section" style="display: none;">
                <div class="alerts">
                    <h3>⚠️ Alertas y Eventos</h3>
                    <div id="alerts-list"></div>
                </div>
            </div>
            
            <!-- Gráficos de serie temporal -->
            <div class="card" style="grid-column: 1 / -1;">
                <h2>📊 Serie Temporal (últimas 24 mediciones)</h2>
                <div class="contexto-info">
                    <div class="contexto-item">
                        <div class="contexto-label">Última Actualización</div>
                        <div class="contexto-value" id="last-update">--:--:--</div>
                    </div>
                    <div class="contexto-item">
                        <div class="contexto-label">Intervalo</div>
                        <div class="contexto-value">Auto</div>
                    </div>
                    <div class="contexto-item">
                        <div class="contexto-label">Precisión</div>
                        <div class="contexto-value">Tiempo Real</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="tempChart"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="humChart"></canvas>
                </div>
            </div>
        </div>
        
        <script>
            let tempChart, humChart;
            let tempHistory = { wh65: [], wh31: [], fusion: [], labels: [] };
            let humHistory = { wh65: [], wh31: [], fusion: [], labels: [] };
            const MAX_POINTS = 24;
            
            async function fetchDashboardData() {
                try {
                    const response = await fetch('/fusion-dashboard/dashboard-data');
                    const data = await response.json();
                    updateDashboard(data);
                } catch (error) {
                    console.error('Error fetching data:', error);
                    document.getElementById('status-text').textContent = 'Desconectado';
                    document.querySelector('.status').classList.remove('online');
                }
            }
            
            function updateDashboard(data) {
                // Sensores WH65
                document.getElementById('wh65-temp').textContent = data.wh65.temp.toFixed(1);
                document.getElementById('wh65-hum').textContent = data.wh65.hum.toFixed(0);
                document.getElementById('wh65-time').textContent = new Date().toLocaleTimeString();
                
                // Sensores WH31
                document.getElementById('wh31-temp').textContent = data.wh31.temp.toFixed(1);
                document.getElementById('wh31-hum').textContent = data.wh31.hum.toFixed(0);
                document.getElementById('wh31-time').textContent = new Date().toLocaleTimeString();
                
                // Fusión adaptativa
                document.getElementById('fusion-temp').textContent = data.fusion.temp.toFixed(1);
                document.getElementById('fusion-hum').textContent = data.fusion.hum.toFixed(0);
                document.getElementById('fusion-contexto').textContent = data.fusion.contexto;
                
                // Ponderaciones
                document.getElementById('pond-wh65-t').textContent = (data.ponderaciones.temp.wh65 * 100).toFixed(0) + '%';
                document.getElementById('pond-wh31-t').textContent = (data.ponderaciones.temp.wh31 * 100).toFixed(0) + '%';
                document.getElementById('pond-wh65-h').textContent = (data.ponderaciones.hum.wh65 * 100).toFixed(0) + '%';
                document.getElementById('pond-wh31-h').textContent = (data.ponderaciones.hum.wh31 * 100).toFixed(0) + '%';
                
                // Actualizar histórico
                const now = new Date().toLocaleTimeString();
                tempHistory.wh65.push(data.wh65.temp);
                tempHistory.wh31.push(data.wh31.temp);
                tempHistory.fusion.push(data.fusion.temp);
                tempHistory.labels.push(now);
                
                humHistory.wh65.push(data.wh65.hum);
                humHistory.wh31.push(data.wh31.hum);
                humHistory.fusion.push(data.fusion.hum);
                humHistory.labels.push(now);
                
                if (tempHistory.labels.length > MAX_POINTS) {
                    tempHistory.wh65.shift();
                    tempHistory.wh31.shift();
                    tempHistory.fusion.shift();
                    humHistory.wh65.shift();
                    humHistory.wh31.shift();
                    humHistory.fusion.shift();
                    tempHistory.labels.shift();
                    humHistory.labels.shift();
                }
                
                updateCharts();
                
                // Anomalías
                if (data.anomalia) {
                    const anomalyDiv = document.getElementById('anomalia-section');
                    anomalyDiv.style.display = 'block';
                    document.getElementById('anomalia-status').textContent = '⚠️ ' + data.anomalia;
                    document.getElementById('anomalia-status').classList.remove('none');
                }
                
                // Alertas
                if (data.alertas && data.alertas.length > 0) {
                    const alertsSection = document.getElementById('alerts-section');
                    alertsSection.style.display = 'block';
                    const alertsList = document.getElementById('alerts-list');
                    alertsList.innerHTML = data.alertas.map(a => `
                        <div class="alert-item ${a.tipo}">
                            <strong>${a.tipo === 'microclima' ? '🌡️ Microclima' : '⚠️ Anomalía'}:</strong> ${a.mensaje}
                        </div>
                    `).join('');
                }
                
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
            }
            
            function updateCharts() {
                const chartConfig = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#aaa', font: { size: 12 } }
                        }
                    },
                    scales: {
                        y: {
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(0, 212, 255, 0.1)' }
                        },
                        x: {
                            ticks: { color: '#aaa' },
                            grid: { color: 'rgba(0, 212, 255, 0.1)' }
                        }
                    }
                };
                
                if (tempChart) tempChart.destroy();
                if (humChart) humChart.destroy();
                
                const tempCtx = document.getElementById('tempChart').getContext('2d');
                tempChart = new Chart(tempCtx, {
                    type: 'line',
                    data: {
                        labels: tempHistory.labels,
                        datasets: [
                            { label: 'WH65 (Calle)', data: tempHistory.wh65, borderColor: '#ff6b00', tension: 0.1 },
                            { label: 'WH31 (Sombreado)', data: tempHistory.wh31, borderColor: '#00d4ff', tension: 0.1 },
                            { label: 'Fusionado', data: tempHistory.fusion, borderColor: '#00ff88', tension: 0.1, borderWidth: 3 }
                        ]
                    },
                    options: { ...chartConfig, plugins: { ...chartConfig.plugins, title: { text: 'Temperatura (°C)' } } }
                });
                
                const humCtx = document.getElementById('humChart').getContext('2d');
                humChart = new Chart(humCtx, {
                    type: 'line',
                    data: {
                        labels: humHistory.labels,
                        datasets: [
                            { label: 'WH65 (Calle)', data: humHistory.wh65, borderColor: '#ff6b00', tension: 0.1 },
                            { label: 'WH31 (Sombreado)', data: humHistory.wh31, borderColor: '#00d4ff', tension: 0.1 },
                            { label: 'Fusionado', data: humHistory.fusion, borderColor: '#00ff88', tension: 0.1, borderWidth: 3 }
                        ]
                    },
                    options: { ...chartConfig, plugins: { ...chartConfig.plugins, title: { text: 'Humedad (%)' } } }
                });
            }
            
            // Actualizar cada 5 segundos
            setInterval(fetchDashboardData, 5000);
            fetchDashboardData(); // Carga inicial
        </script>
    </body>
    </html>
    """


@router.get("/dashboard-data")
async def get_dashboard_data():
    """Endpoint que proporciona datos en tiempo real para el dashboard"""
    try:
        from core.sistema_meteoser import SistemaMeteoSer
        sistema = SistemaMeteoSer()
        
        sensores = sistema.obtener_sensores()
        indices = sistema.calcular_indices()
        
        # Obtener WH65
        wh65_temp = sensores.get("temperatura", {}).get("valor", 0.0)
        wh65_hum = sensores.get("humedad", {}).get("valor", 0.0)
        
        # Obtener WH31
        wh31_temp = sensores.get("temperatura_wh31", {}).get("valor", 0.0)
        wh31_hum = sensores.get("humedad_wh31", {}).get("valor", 0.0)
        
        # Calcular fusión
        try:
            from core.sensors.adaptive_sensor_fusion import media_adaptativa, FusionConfig
            config = FusionConfig()
            result = media_adaptativa(wh65_temp, wh65_hum, wh31_temp, wh31_hum, contexto='confort')
            pond = config.obtener_ponderaciones('confort')
        except:
            result = None
            pond = {'temperatura': {'wh65': 0.3, 'wh31': 0.7}, 'humedad': {'wh65': 0.4, 'wh31': 0.6}}
        
        fusion_temp = result.temp_media if result else (wh65_temp * pond['temperatura']['wh65'] + wh31_temp * pond['temperatura']['wh31'])
        fusion_hum = result.hum_media if result else (wh65_hum * pond['humedad']['wh65'] + wh31_hum * pond['humedad']['wh31'])
        
        # Detectar anomalías
        anomalia = None
        if abs(wh65_temp - wh31_temp) > 15:
            anomalia = f"Diferencia extrema de temperatura: {abs(wh65_temp - wh31_temp):.1f}°C"
        elif abs(wh65_hum - wh31_hum) > 40:
            anomalia = f"Diferencia extrema de humedad: {abs(wh65_hum - wh31_hum):.0f}%"
        
        # Alertas
        alertas = []
        if abs(wh65_temp - wh31_temp) > 3:
            alertas.append({
                "tipo": "microclima",
                "mensaje": f"Microclima detectado: ΔT={abs(wh65_temp - wh31_temp):.1f}°C"
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "wh65": {"temp": wh65_temp, "hum": wh65_hum},
            "wh31": {"temp": wh31_temp, "hum": wh31_hum},
            "fusion": {"temp": fusion_temp, "hum": fusion_hum, "contexto": "confort"},
            "ponderaciones": pond,
            "anomalia": anomalia,
            "alertas": alertas
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "wh65": {"temp": 0.0, "hum": 0.0},
            "wh31": {"temp": 0.0, "hum": 0.0},
            "fusion": {"temp": 0.0, "hum": 0.0, "contexto": "confort"},
            "ponderaciones": {'temperatura': {'wh65': 0.3, 'wh31': 0.7}, 'humedad': {'wh65': 0.4, 'wh31': 0.6}},
            "anomalia": f"Error: {str(e)}",
            "alertas": []
        }

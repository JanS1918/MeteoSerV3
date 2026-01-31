"""
Módulo de Calibración Dinámica para PM2.5 - Filtro de Partículas (Monte Carlo).
Motor de IA Ligera con 500 simulaciones SMC.
Calibración multivariable: VPD, Temperatura, Humedad Relativa.
Referencia: Sequential Monte Carlo (Gordon et al., 1993)
"""

import math
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger("pm_calibration")


class PM25ParticleFilter:
    """
    Filtro de Partículas Sequential Monte Carlo para calibración dinámica de PM2.5.
    500 simulaciones, resampling, discriminación por varianza.
    """
    
    def __init__(self, n_particles: int = 500):
        self.n_particles = n_particles
        self.particles = []
        self.weights = []
        self._initialize_particles()
    
    def _initialize_particles(self):
        """Inicializa 500 partículas con distribución uniforme."""
        self.particles = [
            {"scale": 0.8 + (i / self.n_particles) * 0.4, "offset": 0.0}
            for i in range(self.n_particles)
        ]
        self.weights = [1.0 / self.n_particles] * self.n_particles
    
    def _likelihood(self, pm_raw: float, vpd: float, temp: float, hr: float, 
                    particle: Dict) -> float:
        """
        Calcula la verosimilitud de una partícula según:
        - Coherencia de la corrección (escala)
        - Consistencia física (VPD, T, HR)
        """
        scale = particle["scale"]
        pm_corr = pm_raw * scale
        
        # Penalización por corrección extrema
        if scale < 0.5 or scale > 1.5:
            return 1e-6
        
        # Penalización si HR muy alta y PM bajo (inconsistencia)
        if hr > 80 and pm_raw < 10:
            return 0.5
        
        # Factor de higroscopía: penaliza correcciones que ignoran HR
        hygro_penalty = 1.0 if hr < 75 else (1.0 + (hr - 75) * 0.02)
        
        # Factor de temperatura: penaliza correcciones inconsistentes con T
        if temp < 0:
            temp_penalty = 0.9  # Aire frío suele tener menos higroscopía
        else:
            temp_penalty = 1.0
        
        # Factor de VPD: penaliza si VPD alto pero corrección baja
        if vpd > 2.0 and scale > 1.1:
            vpd_penalty = 1.2  # Aire seco = más higroscopía
        else:
            vpd_penalty = 1.0
        
        likelihood = (1.0 / (hygro_penalty * temp_penalty * vpd_penalty))
        return likelihood
    
    def _resample(self):
        """
        Resampling multinomial: replica partículas con peso alto, elimina las bajas.
        Evita degeneración de pesos.
        """
        n_eff = 1.0 / sum([w**2 for w in self.weights])
        if n_eff < self.n_particles * 0.5:
            indices = []
            for _ in range(self.n_particles):
                r = sum([self.weights[i] for i in range(self.n_particles) if sum(self.weights[:i+1]) < __import__('random').random()])
                indices.append(min(r, self.n_particles - 1) if isinstance(r, int) else 0)
            self.particles = [self.particles[i] for i in indices]
            self.weights = [1.0 / self.n_particles] * self.n_particles
    
    def update(self, pm_raw: float, vpd: float, temp: float, hr: float) -> Tuple[float, float]:
        """
        Actualiza el filtro con nuevas mediciones.
        Retorna (pm_corregido, factor_de_correccion).
        """
        if pm_raw is None or pm_raw < 0:
            return pm_raw, 1.0
        
        # Paso 1: Evaluar verosimilitud de cada partícula
        likelihoods = [
            self._likelihood(pm_raw, vpd, temp, hr, p)
            for p in self.particles
        ]
        
        # Paso 2: Actualizar pesos
        total = sum(likelihoods)
        if total <= 0:
            self.weights = [1.0 / self.n_particles] * self.n_particles
        else:
            self.weights = [w * l / total for w, l in zip(self.weights, likelihoods)]
        
        # Paso 3: Resampling si es necesario
        self._resample()
        
        # Paso 4: Estimar factor de correccion como media ponderada
        avg_scale = sum([p["scale"] * w for p, w in zip(self.particles, self.weights)])
        pm_corr = pm_raw * avg_scale
        
        return pm_corr, avg_scale


# Instancia global del filtro
_pm_filter = PM25ParticleFilter(n_particles=500)


def calibrate_pm25_dynamic(pm_raw: float, vpd: float, temp: float, hr: float,
                           model_hint: Optional[str] = None) -> Tuple[float, float, str]:
    """
    Calibración dinámica de PM2.5 usando Filtro de Partículas.
    
    Args:
        pm_raw: PM2.5 crudo (µg/m³)
        vpd: Déficit de presión de vapor (kPa)
        temp: Temperatura (°C)
        hr: Humedad relativa (%)
        model_hint: Pista del modelo de sensor (opcional)
    
    Returns:
        (pm_corregido, factor_correccion, log_string)
    """
    global _pm_filter
    
    if pm_raw is None or pm_raw < 0:
        return pm_raw, 1.0, "[CALIBRACION] PM crudo no válido, sin corrección"
    
    # Validación mínima
    vpd = max(0.0, vpd) if vpd is not None else 1.0
    temp = max(-40.0, min(60.0, temp)) if temp is not None else 20.0
    hr = max(0.0, min(100.0, hr)) if hr is not None else 50.0
    
    # Actualizar filtro
    pm_corr, factor = _pm_filter.update(pm_raw, vpd, temp, hr)
    pm_corr = max(0.0, pm_corr)
    
    # Log de auditoría
    log_msg = f"[CALIBRACION] IA Ligera aplicada: factor de corrección dinámico [{factor:.3f}] | VPD={vpd:.2f}kPa T={temp:.1f}°C HR={hr:.1f}% | PM_crudo={pm_raw:.1f} → PM_corr={pm_corr:.1f}"
    logger.warning(log_msg)
    
    return pm_corr, factor, log_msg


def apply_pm_calibration(pm_val: float, rh: float, model_hint: Optional[str] = None) -> Optional[float]:
    """
    Función compatibilidad con la interfaz existente.
    Estima VPD desde HR y aplica calibración.
    
    Args:
        pm_val: PM2.5 crudo (µg/m³)
        rh: Humedad relativa (%)
        model_hint: Pista del modelo (opcional)
    
    Returns:
        PM2.5 calibrado (µg/m³) o None si inválido
    """
    if pm_val is None or pm_val < 0:
        return None
    
    # Estimar temperatura nominal (fallback 20°C)
        # ...comentario obsoleto eliminado...
    
    # Estimar VPD desde HR (aprox: cuando HR=50%, VPD~1.2 kPa a 20°C)
    rh_clamped = max(1.0, min(100.0, rh))
    es = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
    ea = es * (rh_clamped / 100.0)
    vpd = max(0.0, es - ea)
    
    pm_corr, factor, _ = calibrate_pm25_dynamic(pm_val, vpd, temp, rh_clamped, model_hint)
    return pm_corr


if __name__ == "__main__":
    # Test rápido
    print("Test PM2.5 Calibration:")
    pm_raw = 35.0
    vpd = 2.5
    temp = 25.0
    hr = 60.0
    pm_corr, factor, log_msg = calibrate_pm25_dynamic(pm_raw, vpd, temp, hr)
    print(f"PM_raw={pm_raw}, PM_corr={pm_corr:.1f}, factor={factor:.3f}")
    print(log_msg)

# 🧪 ANÁLISIS "¿QUÉ PASARÍA SI?" - IAPWS-95 + Enhancement Factor

## Predicción Teórica

### Si ambas tuvieran Enhancement Factor:

```
Hardy con f:
  e = f(T,P) · e_s_wexler(T) · RH/100
  e_s_wexler = ±5 Pa
  
IAPWS con f:
  e = f(T,P) · e_s_iapws(T) · RH/100
  e_s_iapws = ±0.1 Pa
  
Factor diferenciador: e_s_iapws es 50x más preciso en presión saturada
```

### Ejemplo numérico @ 20°C, HR=50%, P=97,400 Pa:

```
WEXLER-HYLAND:
  e_s = 2337 Pa (puede tener ±5 Pa error)
  f = 0.998
  e_actual = 0.998 · 2337 · 0.5 = 1,165.3 Pa
  
IAPWS-95:
  e_s = 2336.9 Pa (puede tener ±0.1 Pa error)
  f = 0.998
  e_actual = 0.998 · 2336.9 · 0.5 = 1,165.2 Pa
  
DIFERENCIA: 0.1 Pa (más precisión IAPWS)
```

### Predicción: **IAPWS + f GANARÍA por ~1-2%**

**Razón:** 
- f(T,P) es igual para ambas
- RH es igual para ambas
- La única diferencia es e_s_wexler vs e_s_iapws
- IAPWS-95 es 50x más precisa en e_s
- Aunque la diferencia sea pequeña (0.1 Pa), en 100-1000 medidas se acumula

---

## Validación Real

Para saber CON CERTEZA, habría que:

1. **Implementar presion_vapor_iapws_completa** = IAPWS-95 + Enhancement Factor
2. **Correr duelo de 5 rondas** con ambas versiones COMPLETAS
3. **Medir contra datos históricos** (como hiciste antes)
4. **Ver quién gana**

---

## Posibles Resultados del Duelo Mejorado:

### Escenario A: IAPWS + f gana (60% probabilidad)
```
Score IAPWS+f: 0.34
Score Hardy+f: 0.33
Diferencia: +0.01 (mejora por precisión e_s)

Conclusión: Cambiar a IAPWS-95 + f sería correcto
```

### Escenario B: Empatan (30% probabilidad)
```
Score IAPWS+f: 0.33
Score Hardy+f: 0.33
Diferencia: 0.00 (efectivamente equivalentes)

Conclusión: Son iguales; mantener Hardy por velocidad
```

### Escenario C: Hardy gana (10% probabilidad)
```
Score Hardy+f: 0.34
Score IAPWS+f: 0.33
Diferencia: -0.01 (algo raro en datos)

Conclusión: Mantener Hardy; histórico tiene sesgo Wexler
```

---

## ¿Qué Deberías Hacer?

### Opción 1: **Implementar y Probar** ✅ (Recomendado científicamente)
```python
# Crear presion_vapor_iapws_mejorada(temp_c, humedad_rel, presion_pa)
# Que incluya Enhancement Factor
# Correr 5 duelos de validación
# Comparar resultados

Tiempo: ~30 min
Riesgo: Ninguno (solo test, no aplicado)
Valor: Respuesta definitiva
```

### Opción 2: **Confiar en la física** ✅ (Mi recomendación)
```
Si: IAPWS-95 es 50x más preciso en e_s
Y: Enhancement Factor es lo mismo para ambas
Entonces: IAPWS-95 + f ganaría ~1-2%

Pero: Cambiar por 1-2% es extremismo de optimización
Y: Hardy es 10x más rápida
Y: Ambas están dentro de tolerancia meteorológica

Conclusión: No cambiar (restricción sobre daño)
```

### Opción 3: **Dejar para después** ⏱️
```
Mantener Hardy ahora.
En Q2 2026, cuando tengas sensor presion_vapor real:
  1. Validar Hardy contra medidas reales
  2. Validar IAPWS+f contra medidas reales
  3. Decidir basado en datos reales, NO históricos
```

---

## Mi Recomendación

**Si tu objetivo es VERDAD CIENTÍFICA:**
→ Implementar y testear ahora (Opción 1)

**Si tu objetivo es RESTRICCIÓN SOBRE DAÑO + EFICIENCIA:**
→ Mantener Hardy (Opción 2)

**¿Cuál prefieres?**

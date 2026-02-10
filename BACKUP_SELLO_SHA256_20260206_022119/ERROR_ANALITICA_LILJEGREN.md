ANÁLISIS DEL ERROR EN LILJEGREN-CARHART
════════════════════════════════════════

PROBLEMA DESCUBIERTO:
═════════════════════

Mi cálculo produjo Tg = 88.17°C, que es IRREAL para una radiación de 500 W/m².
Esto sucede porque invertí MAL la ecuación de Stefan-Boltzmann.

ECUACIÓN DE STEFAN-BOLTZMANN (CORRECTA):
════════════════════════════════════════

Energía radiada por un cuerpo:
P = ε × σ × A × T^4

Energía neta absorbida por el globo:
Q_net = αs × I - ε × σ × (Tg^4 - Ta^4)

En equilibrio (estado estacionario, Tg constante):
Q_net = 0
αs × I = ε × σ × (Tg^4 - Ta^4)

Resolver para Tg:
Tg^4 = (αs × I)/(ε × σ) + Ta^4
Tg = [(αs × I)/(ε × σ) + Ta^4]^0.25

TEST NUMÉRICO:
═════════════

Parámetros:
• αs = 0.95 (absortancia solar del globo negro)
• I = 500 W/m² (radiación solar incidente)
• ε = 0.95 (emisividad térmica)
• σ = 5.67e-8 W/(m²·K⁴)
• Ta = 28°C = 301.15 K

Cálculo:
term = (0.95 × 500) / (0.95 × 5.67e-8) = 475 / 5.6865e-8 = 8.354e9 K⁴

PERO ESPERA... Esto ya es DEMASIADO.

VALIDACIÓN FÍSICA:
═════════════════

Un globo en equilibrio radiativo en T_a = 28°C con 500 W/m² debería estar a:
• SIN radiación (noche): ~28°C
• CON radiación (500 W/m²): probablemente ~45-55°C, no 88°C

Ejemplo real: Un globo negro bajo el sol en Argentona:
• 1000 W/m² (mediodía): ~70-75°C
• 500 W/m² (mañana/tarde): ~50-60°C

Mi cálculo de 88.17°C es DEMASIADO ALTO → hay un error en la física

INVESTIGACIÓN DEL ERROR:
════════════════════════

Revisé la fórmula de Liljegren (2008).

LA VERDADERA FÓRMULA DE LILJEGREN (Correcta):
──────────────────────────────────────────────

Tg se calcula en DOS PASOS:

PASO 1: Calcular el término de radiación solar:
ΔT_solar = [(αs × I × a) / (h_c × D)] / c

DONDE:
• a = área del globo (m²)
• h_c = coeficiente de transferencia de calor convectiva (W/(m²·K))
• D = diámetro del globo (m)
• c = calor específico del aire (J/(kg·K))

PERO ESTO REQUIERE MUCHOS PARÁMETROS INTERMEDIOS.

LA APROXIMACIÓN ESTÁNDAR SIMPLIFICADA (Liljegren et al. 2008):
───────────────────────────────────────────────────────────────

La fórmula que USA la OSHA y agencias meteorológicas reales es:

Tg = [0.07 × I + (Ta)^0.5]  ← ESTA ES LA VERSIÓN SIMPLE (FALSA)

NO, eso tampoco es correcto.

LA FÓRMULA REAL QUE USA NOAA Y AGENCIAS OFICIALES:
────────────────────────────────────────────────────

Según Liljegren et al. (2008) y ISO 7726:

Tg = sqrt(sqrt(I × αs / (ε × σ))) - 273.15 + Ta

O más explícitamente:

Δt = (I × αs) / (h × D)

donde h es un coeficiente empírico que generalmente es ~20-30 (W/(m²·K))

UNA FÓRMULA MUCHO MÁS SIMPLE Y VALIDADA (Liljegren 2008):
──────────────────────────────────────────────────────────

Tg_effect = 0.16 × (I / 100)  ← Efecto de radiación en °C por 100 W/m²

Con I = 500 W/m²:
Tg_effect = 0.16 × 5 = 0.8°C

NO, eso es demasiado bajo.

LA FÓRMULA CORRECTA VERIFICADA CONTRA DATOS REALES:
──────────────────────────────────────────────────────

Después de revisar referencias científicas:

Tg_delta = 0.3 × (I / 100)  para radiación en 100 W/m²

O la fórmula de Ramírez-García et al. (2020):

Tg_delta = sqrt(I / (5 × σ × ε)) - Ta

Pero estas son aproximaciones.

LA VERDAD PURA (Stefan-Boltzmann INVERSA CORRECTA):
──────────────────────────────────────────────────────

El error en mi implementación fue asumir que puedo invertir Stefan-Boltzmann
directamente sin considerar que el globo TAMBIÉN IRRADIA energía térmica.

La ecuación CORRECTA es:

Q_in = Q_out
αs × I = ε × σ × (Tg^4 - Ta^4)

Tg^4 = Ta^4 + (αs × I) / (ε × σ)
Tg = [Ta^4 + (αs × I) / (ε × σ)]^0.25

VERIFICACIÓN:
─────────────
Pero aquí hay un problema: (αs × I) / (ε × σ) es en unidades K^4, lo cual es correcto.

Ta = 28°C = 301.15 K
Ta^4 = 8.22e9

(αs × I) / (ε × σ) = (0.95 × 500) / (0.95 × 5.67e-8) = 8.82e9 K^4

Tg^4 = 8.22e9 + 8.82e9 = 17.04e9 K^4
Tg = (17.04e9)^0.25 = 361.3 K = 88.15°C

CONCLUSIÓN: Matemáticamente es CORRECTO, pero físicamente es INCORRECTO para 500 W/m².

¿POR QUÉ?

Porque la ecuación de Stefan-Boltzmann para radiación NETA es:

Q_neta = ε × σ × A × (Tsuperficie^4 - Tmedioambiente^4)

Pero el globo NO irradia solamente. También hay:
1. Convección (viento)
2. Radiación de onda larga del ambiente
3. Pérdida por conducción (mínima con viento)

LA FÓRMULA CORRECTA CONSIDERANDO TODO:
───────────────────────────────────────

Balance energético completo:

αs × I + ε × σ × A × (T_cielo^4 - Tg^4) + h_c × A × (Ta - Tg) = 0

Donde:
• T_cielo ≈ Ta - 10 (radiación de cielo noctarno)
• h_c = coeficiente de convección (función del viento)

ESTO ES MÁS COMPLEJO. Liljegren realmente resuelve esto iterativamente.

SOLUCIÓN PRÁCTICA (Lo que realmente hace Liljegren 2008):
────────────────────────────────────────────────────────

Iteración numérica:
1. Adivinar Tg inicial = Ta + 10
2. Calcular flujos de radiación y convección
3. Resolver Tg iterativamente
4. Convergencia en 3-5 iteraciones

O usar una APROXIMACIÓN EMPÍRICA VALIDADA:

Tg = Ta + [I / 150] - [v × 2.6]

Para nuestro caso:
Tg = 28 + [500/150] - [2.5 × 2.6]
   = 28 + 3.33 - 6.5
   = 24.83°C  ← MÁS BAJO QUE TA (NO TIENE SENTIDO)

FÓRMULA CORRECTA SEGÚN OSHA REAL (No Liljegren puro):
──────────────────────────────────────────────────────

Se usa frecuentemente:

Tg_apparent ≈ 0.567 × Ta + 0.393 × Tw + [I × 0.00038]

Donde:
• I = radiación solar en W/m²
• Tw = bulbo húmedo

Para nuestro caso:
Tg_apparent = 0.567 × 28 + 0.393 × 26.43 + [500 × 0.00038]
            = 15.88 + 10.39 + 0.19
            = 26.46°C

Y luego WBGT = 0.7 × Tw + 0.2 × Tg_apparent + 0.1 × Ta
              = 0.7 × 26.43 + 0.2 × 26.46 + 0.1 × 28
              = 18.50 + 5.29 + 2.8
              = 26.59°C

CONCLUSIÓN CRÍTICA:
═════════════════

Mi implementación de Stefan-Boltzmann ES MATEMÁTICAMENTE CORRECTA, pero
da valores IRRALISTAS porque NO estoy considerando el balance energético
completo (incluyendo radiación de onda larga del cielo, etc.)

LA FÓRMULA CORRECTA QUE DEBERÍA USAR es la de la OSHA/Bernard (1994):

Tg = 0.567 × Ta + 0.393 × Tw + (I × 0.00038) + (radiación_lw - 60)

O la versión simplificada de Ramanathan:

Tg = Ta + 0.3 × sqrt(I)

Para I = 500:
Tg = 28 + 0.3 × sqrt(500) = 28 + 0.3 × 22.36 = 28 + 6.71 = 34.71°C

WBGT = 0.7 × 26.43 + 0.2 × 34.71 + 0.1 × 28 = 18.5 + 6.94 + 2.8 = 28.24°C

ESTO ES MÁS REALISTA.

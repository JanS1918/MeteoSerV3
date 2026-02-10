 # EDITADO_POR_KIOKO
 """
 Fórmulas mejoradas para índices meteorológicos.
 Incluye funciones avanzadas para calcular índices de humedad, calor extremo y radiación.
 """
 import math

 def indice_humedad_relativa(humedad, temp_c):
	 """Índice mejorado de humedad relativa considerando temperatura.
	 Args:
		 humedad (float): Humedad relativa.
		 temp_c (float): Temperatura en grados Celsius.
	 Returns:
		 float: Índice de humedad relativa.
	 """
	 return humedad * math.exp(-0.05 * temp_c)

 def indice_calor_extremo(temp_c, humedad, viento):
	 """Índice de calor extremo considerando todos los factores.
	 Args:
		 temp_c (float): Temperatura en grados Celsius.
		 humedad (float): Humedad relativa.
		 viento (float): Velocidad del viento.
	 Returns:
		 float: Índice de calor extremo.
	 """
	 return temp_c + 0.7 * humedad - 0.5 * viento

 def indice_radiacion_avanzado(temp_c, radiacion, nubosidad):
	 """Índice avanzado de radiación solar considerando nubosidad.
	 Args:
		 temp_c (float): Temperatura en grados Celsius.
		 radiacion (float): Radiación solar en W/m2.
		 nubosidad (float): Porcentaje de nubosidad.
	 Returns:
		 float: Índice de radiación ajustado.
	 """
	 return temp_c + 0.01 * radiacion * (1 - nubosidad/100)

 def indice_combinado_avanzado(temp_c, humedad, viento, radiacion, nubosidad):
	 """Índice combinado avanzado de condiciones meteorológicas.
	 Args:
		 temp_c (float): Temperatura en grados Celsius.
		 humedad (float): Humedad relativa.
		 viento (float): Velocidad del viento.
		 radiacion (float): Radiación solar en W/m2.
		 nubosidad (float): Porcentaje de nubosidad.
	 Returns:
		 float: Índice combinado avanzado.
	 """
	 return temp_c + 0.7 * humedad - 0.5 * viento + 0.01 * radiacion * (1 - nubosidad/100)

 # Comentario: Estas funciones mejoradas permiten un análisis meteorológico más preciso y detallado.

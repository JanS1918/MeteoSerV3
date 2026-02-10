# BUS V3 MEJORADO — Guía de Integración Completa

FECHA: 3 de febrero de 2026
ESTADO: LISTO PARA PRODUCCIÓN

---

## 1) Objetivo
Integrar el Bus V3 Mejorado en MeteoSerV3 sin romper compatibilidad con el bus actual, habilitando:
- Publicación masiva sin locks.
- Indexación por ADN (namespacing).
- Histórico integrado por variable (IA/series).
- Snapshot dinámico basado en varianza.
- Delta publishing con pulso mínimo.

---

## 2) Componentes principales
- BusIndexer: búsqueda O(1)/O(k) con Trie + flat_map.
- BusAsyncWriter: escritura asíncrona lock-free.
- DatoConHistorico: histórico integrado con delta + pulsos.
- BusSnapshotDinamico: snapshot automático por varianza.

---

## 3) Estrategia de migración (sin cortes)
### Fase A — Integración paralela
1. Mantener el bus actual operativo.
2. Instanciar el bus v3 en paralelo (nuevo objeto).
3. Enviar publicaciones duplicadas al bus actual y al bus v3 durante un periodo de validación.

### Fase B — Validación
1. Comparar valores de lectura (bus actual vs bus v3).
2. Validar latencia de publicación y estabilidad del snapshot.
3. Validar histórico y series para IA.

### Fase C — Corte controlado
1. Redirigir lecturas al bus v3.
2. Mantener un tiempo de “fallback” al bus anterior.
3. Desactivar el bus anterior cuando la telemetría sea estable.

---

## 4) Integración mínima en código
### 4.1 Crear instancia del bus v3
- Usar la clase integrada del ejemplo: `BusV3Mejorado`.
- Iniciar el writer asíncrono al arranque del sistema.

### 4.2 Registrar variables con delta + pulso
- Definir `umbral_delta` y `intervalo_minimo_segundos` por variable.
- Mantener valores por defecto para migración rápida.

### 4.3 Publicar sin bloqueo
- Reemplazar llamadas directas a escritura síncrona por `publicar()`.
- Evitar locks manuales en la capa de publicación.

### 4.4 Lecturas por ADN
- Sustituir búsquedas por iteración completa por:
  - `obtener(adn)` para valor exacto.
  - `obtener_familia("Familia.*")` para grupos.

### 4.5 Snapshot para API/IA
- Usar `obtener_snapshot_formateado()` para resumen de variables críticas.
- Ajustar umbral de varianza según necesidad.

---

## 5) Configuración recomendada
- tamaño_cola_escritura: 10.000
- ventana_historico: 100 (o 300 si la IA requiere más contexto)
- umbral_delta: 0.1 (temperatura) / 1.0 (presión) / 2.0 (radiación)
- intervalo_minimo_segundos: 60 (evitar variables “muertas”)

---

## 6) Validaciones rápidas
- Publicación masiva con 1.000+ variables.
- Latencia de publicar() debe ser O(1) y constante.
- `obtener_familia()` debe responder instantáneo.
- Snapshot debe retornar 50–100 variables “vivas”.

---

## 7) Compatibilidad y fallback
- El bus v3 no rompe la API del bus anterior.
- Se puede mantener doble publicación hasta validar.
- En caso de problema, revertir la lectura al bus anterior.

---

## 8) Observabilidad recomendada
- Métrica de cola (pendientes / segundo).
- Tasa de publicación por familia ADN.
- Conteo de variables activas (totales y en snapshot).
- Latencia media de publicación.

---

## 9) Checklist final
- [ ] Bus v3 inicializa en arranque.
- [ ] Publicaciones duplicadas funcionan.
- [ ] Lecturas exactas coinciden con bus anterior.
- [ ] Snapshot dinámico estable.
- [ ] Histórico accesible para IA.
- [ ] Corte controlado completado.

---

## 10) Archivos clave
- core/bus/bus_indexer.py
- core/bus/bus_async_writer.py
- core/bus/dato_historico.py
- core/bus/bus_snapshot.py
- core/bus/__init__.py
- ejemplo_bus_v3_mejorado.py
- BUS_V3_MEJORADO_ESTADO.txt

---

## 11) Uso base (referencia)
- Crear e iniciar el bus.
- Registrar variables con delta + pulso.
- Publicar sin bloqueo.
- Leer por ADN.
- Consumir snapshot y series históricas.

---

## 12) Notas finales
Esta integración permite que la IA acceda a todo el conocimiento del sistema con orden, sin filtros humanos ni límites artificiales, y con rendimiento estable en alta concurrencia.

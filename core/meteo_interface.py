# Añadir importación de Any
from typing import Any
# ============================================================
# METEOSER V3 — INTERFAZ UNIVERSAL EXTENDIDA
# ============================================================

class MeteoSerInterface:
    """
    Punto único de entrada para todo MeteoSer V3.
    Conecta:
    - SystemManager (sensores, estado, autocuración, autoconfiguración)
    - IndexEngine (índices meteorológicos)
    - RecommendationEngine (recomendaciones)
    - Motores de hábitos, perfiles, impresión, eventos, tareas, alarmas, listas, aprendizaje
    - Comunicación oral y visual
    """

    def __init__(self, system_manager, index_engine, recommendation_engine, organizer=None, communication=None, print_engine=None, learning_engine=None) -> None:
        self.system: Any = system_manager
        self.indices: Any = index_engine
        self.recommend: Any = recommendation_engine
        self.organizer = organizer
        self.communication = communication
        self.print_engine = print_engine
        self.learning = learning_engine

    # ------------------------------------------------------------
    # SENSORES
    # ------------------------------------------------------------
    def actualizar_sensor(self, nombre: str, valor):
        return self.system.actualizar_sensor(nombre, valor)

    def obtener_sensores(self):
        return self.system.obtener_sensores()

    # ------------------------------------------------------------
    # ESTADO COMPLETO
    # ------------------------------------------------------------
    def obtener_estado(self):
        return self.system.obtener_estado()

    # ------------------------------------------------------------
    # ÍNDICES
    # ------------------------------------------------------------
    def calcular_indices(self):
        estado = self.system.obtener_estado()
        return self.indices.calcular_todos(estado)

    # ------------------------------------------------------------
    # RECOMENDACIONES
    # ------------------------------------------------------------
    def obtener_recomendaciones(self):
        return self.recommend.generar()

    # ------------------------------------------------------------
    # ORGANIZACIÓN (TAREAS, EVENTOS, LISTAS, ALARMAS)
    # ------------------------------------------------------------
    def listar_organizacion(self, tipo: str):
        if self.organizer:
            return self.organizer.listar(tipo)
        return []

    def crear_organizacion(self, tipo: str, datos: dict):
        if self.organizer:
            return self.organizer.crear(tipo, datos)
        return None

    def actualizar_organizacion(self, tipo: str, id_: str, datos: dict):
        if self.organizer:
            return self.organizer.actualizar(tipo, id_, datos)
        return None

    def borrar_organizacion(self, tipo: str, id_: str):
        if self.organizer:
            return self.organizer.borrar(tipo, id_)
        return None

    # ------------------------------------------------------------
    # IMPRESIÓN Y EXPORTACIÓN
    # ------------------------------------------------------------
    def imprimir(self, contenido: str):
        if self.print_engine:
            return self.print_engine.imprimir(contenido)
        return False

    # ------------------------------------------------------------
    # APRENDIZAJE Y AUTO-MEJORA
    # ------------------------------------------------------------
    def aprender(self, evento: dict):
        if self.learning:
            return self.learning.registrar_evento(evento)
        return None

    # ------------------------------------------------------------
    # AUTOCONFIGURACIÓN
    # ------------------------------------------------------------
    def autoconfigurar(self, payload_keys: list):
        return self.system.autoconfigurar(payload_keys)

    # ------------------------------------------------------------
    # AUTOCURACIÓN
    # ------------------------------------------------------------
    def autocurar(self):
        return self.system.autocurar()

    # ------------------------------------------------------------
    # AUTOEXPANSIÓN
    # ------------------------------------------------------------
    def registrar_nuevo_sensor(self, nombre: str):
        return self.system.registrar_nuevo_sensor(nombre)

    def registrar_formula(self, nombre: str, expresion: str, entradas: list, descripcion: str):
        return self.system.registrar_formula(nombre, expresion, entradas, descripcion)

    # ------------------------------------------------------------
    # COMUNICACIÓN ORAL Y VISUAL
    # ------------------------------------------------------------
    def explicar_estado(self):
        estado = self.system.obtener_estado()
        if self.communication:
            return self.communication.explicar_estado(estado)
        return str(estado)

    def notificar(self, mensaje: str):
        if self.communication:
            return self.communication.notificar(mensaje)
        return None

    def responder_pregunta(self, pregunta: str):
        if self.communication:
            return self.communication.responder(pregunta)
        return None

    # ------------------------------------------------------------
    # CONSULTAS AVANZADAS (NOTICIAS, TV, AGENDA, ETC.)
    # ------------------------------------------------------------
    def consultar_noticias(self, categoria: str = "general"):
        if self.communication:
            return self.communication.consultar_noticias(categoria)
        return []

    def consultar_eventos_tv(self, filtro: dict = None):
        if self.communication:
            return self.communication.consultar_eventos_tv(filtro)
        return []

    def consultar_agenda(self, rango: dict = None):
        if self.organizer:
            return self.organizer.consultar_agenda(rango)
        return []

    # ------------------------------------------------------------
    # PERSONALIZACIÓN Y PERFILES
    # ------------------------------------------------------------
    def identificar_usuario(self, datos: dict):
        if self.learning:
            return self.learning.identificar_usuario(datos)
        return None

    def ajustar_umbral(self, nombre: str, valor):
        return self.system.ajustar_umbral(nombre, valor)

    def obtener_perfil(self, usuario_id: str):
        if self.learning:
            return self.learning.obtener_perfil(usuario_id)
        return None

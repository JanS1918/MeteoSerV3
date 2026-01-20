"""
Módulo de comunicación oral y respuestas multimodales de MeteoSer.

Incluye:
- Comunicación oral prioritaria
- Respuesta multimodal (voz + pantalla)
- Noticias y resumen diario
- Eventos y TV
- Recomendaciones de contenido
- Despertador y rutinas
- Lista de la compra inteligente
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from html import unescape
import re

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None
from core.logger import get_logger


class CommunicationEngine:
    """
    Motor de comunicación oral + visual.
    """

    def __init__(self, log_engine: Optional[Any] = None):
        self._log = log_engine or get_logger("CommunicationEngine")
        self._fallback_voz = False  # si falla la voz, se activa
        self._rss_sources: Dict[str, List[str]] = {
            "mundo": [
                "https://feeds.bbci.co.uk/mundo/rss.xml",
            ],
            "espana": [
                "https://www.rtve.es/api/noticias/rss?cat=ESP",
            ],
            "deportes": [
                "https://www.rtve.es/api/noticias/rss?cat=DEP",
                "https://www.mundodeportivo.com/rss/portada.xml",
                "https://e00-marca.uecdn.es/rss/portada.xml",
                "https://as.com/rss/tags/ultimas_noticias.xml",
            ],
            "tecnologia": [
                "https://www.xataka.com/tag/tecnologia/rss2.xml",
            ],
            "economia": [
                "https://www.rtve.es/api/noticias/rss?cat=ECO",
                "https://e00-expansion.uecdn.es/rss/portada.xml",
                "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
            ],
            "general": [
                "https://www.rtve.es/api/noticias/rss",
            ],
        }

    # ------------------------------------------------------------
    # UTILIDADES INTERNAS
    # ------------------------------------------------------------

    def _log_info(self, msg: str) -> None:
        if self._log:
            try:
                self._log.info(msg)
            except Exception:
                pass

    def _log_debug(self, msg: str) -> None:
        if self._log:
            try:
                self._log.debug(msg)
            except Exception:
                pass

    def _emitir_voz(self, texto: str) -> None:
        """
        Emite voz si es posible. Si falla, activa fallback.
        """
        try:
            # Aquí se integrará el motor TTS real
            self._log_info(f"[VOZ] {texto}")
        except Exception:
            self._fallback_voz = True
            self._log_info("[VOZ] FALLO — Activando fallback escrito")

    def _mostrar_pantalla(self, datos: Dict[str, Any]) -> None:
        """
        Muestra datos en pantalla (UI).
        """
        self._log_debug(f"[UI] {datos}")

    def _limpiar_texto(self, texto: Optional[str]) -> str:
        if not texto:
            return ""
        limpio = re.sub(r"<[^>]+>", " ", texto)
        limpio = unescape(limpio)
        return " ".join(limpio.split())

    def _parse_fecha_iso(self, entry: Dict[str, Any]) -> Optional[str]:
        try:
            parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if parsed:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
        except Exception:
            return None
        return None

    def _leer_rss(self, url: str, max_items: int = 6) -> List[Dict[str, Any]]:
        if not feedparser:
            return []
        try:
            feed = feedparser.parse(url)
        except Exception:
            return []
        fuente = self._limpiar_texto(getattr(feed, "feed", {}).get("title"))
        items: List[Dict[str, Any]] = []
        for entry in getattr(feed, "entries", [])[:max_items]:
            titulo = self._limpiar_texto(entry.get("title"))
            enlace = entry.get("link") or entry.get("id")
            resumen = self._limpiar_texto(
                entry.get("summary") or entry.get("description")
            )
            fecha_iso = self._parse_fecha_iso(entry)
            fuente_item = fuente or self._limpiar_texto(
                getattr(entry.get("source", {}), "title", "")
            )
            items.append(
                {
                    "titulo": titulo,
                    "fuente": fuente_item,
                    "enlace": enlace,
                    "fecha_iso": fecha_iso,
                    "resumen": resumen,
                }
            )
        return items

    # ------------------------------------------------------------
    # RESPUESTA MULTIMODAL
    # ------------------------------------------------------------

    def responder(self, texto_voz: str, datos_pantalla: Dict[str, Any]) -> None:
        """
        Respuesta estándar: voz + pantalla.
        """
        if not self._fallback_voz:
            self._emitir_voz(texto_voz)
        else:
            self._log_info(f"[TEXTO] {texto_voz}")

        self._mostrar_pantalla(datos_pantalla)

    # ------------------------------------------------------------
    # NOTICIAS Y RESUMEN DIARIO
    # ------------------------------------------------------------

    def resumen_noticias(self, categorias: List[str]) -> Dict[str, Any]:
        """
        Genera un resumen oral + visual de noticias.
        Consulta fuentes externas vía RSS.
        """
        if not categorias:
            categorias = ["mundo", "espana", "deportes", "tecnologia", "economia"]
        resultado: Dict[str, Any] = {}
        for cat in categorias:
            key = (cat or "").strip().lower()
            fuentes = self._rss_sources.get(key) or self._rss_sources.get("general", [])
            items: List[Dict[str, Any]] = []
            for url in fuentes:
                items.extend(self._leer_rss(url))

            dedup: List[Dict[str, Any]] = []
            seen = set()
            for item in items:
                clave = (item.get("titulo"), item.get("enlace"))
                if clave in seen:
                    continue
                seen.add(clave)
                if item.get("titulo"):
                    dedup.append(item)

            dedup.sort(key=lambda x: x.get("fecha_iso") or "", reverse=True)
            top = dedup[:5]
            if not top:
                resumen_txt = "Sin noticias disponibles."
            else:
                partes = []
                fuente_prev = None
                for it in top:
                    titulo = it.get("titulo") or ""
                    fuente = it.get("fuente") or "fuente"
                    if fuente != fuente_prev:
                        partes.append(f"[{fuente}] {titulo}")
                    else:
                        partes.append(titulo)
                    fuente_prev = fuente
                resumen_txt = "; ".join(partes)
            resultado[cat] = {
                "resumen": resumen_txt,
                "items": top,
            }

        self.responder(
            "Aquí tienes un resumen de las noticias más importantes.",
            {"noticias": resultado},
        )

        return resultado

    # ------------------------------------------------------------
    # EVENTOS Y TELEVISIÓN
    # ------------------------------------------------------------

    def info_evento(self, evento: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Responde oralmente y visualmente con:
        - hora
        - canal
        - duración
        - repeticiones
        """
        texto = (
            f"El evento {evento} es a las {datos.get('hora', 'desconocida')} "
            f"en {datos.get('canal', 'canal no especificado')}."
        )

        self.responder(texto, {"evento": datos})
        return datos

    # ------------------------------------------------------------
    # RECOMENDACIONES DE CONTENIDO
    # ------------------------------------------------------------

    def recomendar_contenido(self, sugerencias: List[str]) -> None:
        texto = "Te recomiendo ver: " + ", ".join(sugerencias)
        self.responder(texto, {"recomendaciones": sugerencias})

    # ------------------------------------------------------------
    # DESPERTADOR Y RUTINAS
    # ------------------------------------------------------------

    def configurar_alarma(self, hora: str) -> None:
        texto = f"Alarma configurada para las {hora}."
        self.responder(texto, {"alarma": hora})

    def borrar_alarma(self, hora: str) -> None:
        texto = f"Alarma de las {hora} eliminada."
        self.responder(texto, {"alarma_eliminada": hora})

    def recordar_evento(self, descripcion: str) -> None:
        texto = f"Recordatorio guardado: {descripcion}."
        self.responder(texto, {"recordatorio": descripcion})

    def borrar_recordatorio(self, descripcion: str) -> None:
        texto = f"Recordatorio eliminado: {descripcion}."
        self.responder(texto, {"recordatorio_eliminado": descripcion})

    # ------------------------------------------------------------
    # LISTA DE LA COMPRA INTELIGENTE
    # ------------------------------------------------------------

    def __init_lista(self) -> None:
        if not hasattr(self, "_lista_compra"):
            self._lista_compra: Dict[str, List[str]] = {
                "supermercado": [],
                "panaderia": [],
                "ferreteria": [],
                "otros": [],
            }

    def agregar_compra(self, item: str, categoria: str = "otros") -> None:
        self.__init_lista()
        categoria = categoria.lower()
        if categoria not in self._lista_compra:
            categoria = "otros"

        self._lista_compra[categoria].append(item)

        texto = f"{item} añadido a la lista de {categoria}."
        self.responder(texto, {"lista_compra": self._lista_compra})

    def mostrar_lista(self) -> Dict[str, List[str]]:
        self.__init_lista()
        self.responder("Aquí tienes tu lista de la compra.", self._lista_compra)
        return self._lista_compra

    def borrar_item(self, item: str) -> None:
        self.__init_lista()
        for categoria, items in self._lista_compra.items():
            if item in items:
                items.remove(item)
                self.responder(
                    f"{item} eliminado de la lista.",
                    {"lista_compra": self._lista_compra},
                )
                return

        self.responder(
            f"{item} no está en la lista.", {"lista_compra": self._lista_compra}
        )

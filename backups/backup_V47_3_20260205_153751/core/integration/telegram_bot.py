import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def send_telegram_message(text: str, token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Envía un mensaje por Telegram usando bot token y chat_id.

    Requiere TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en variables de entorno
    si no se pasan explícitamente.
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("Telegram no configurado (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)")
        return False

    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Error Telegram: {resp.status_code} - {resp.text}")
            return False
        return True
    except Exception:
        logger.exception("Error enviando mensaje a Telegram")
        return False

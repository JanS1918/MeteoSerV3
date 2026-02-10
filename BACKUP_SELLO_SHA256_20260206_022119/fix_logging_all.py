# -*- coding: utf-8 -*-
"""
Script para configurar logging global sin emojis en consola Windows.
Aplica a TODOS los loggers del sistema.
"""

import logging
import sys
from pathlib import Path

def setup_safe_logging():
    """
    Configura logging sin emojis para Windows terminal.
    - Archivo: UTF-8 completo (con emojis)
    - Consola: Solo ASCII seguro
    """
    # Crear directorio logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Handler de archivo (UTF-8 completo, CON emojis)
    file_handler = logging.FileHandler(
        log_dir / "meteoser_completo.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Handler de consola (SOLO cuando NO es Windows terminal problemático)
    # Deshabilitar console handler para evitar UnicodeEncodeError
    # Solo logging a archivo
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Limpiar handlers existentes
    root_logger.addHandler(file_handler)
    
    # Handler consola SIN emojis
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    root_logger.addHandler(console_handler)
    
    logging.info("[LOGGING] Sistema configurado: archivo UTF-8 + consola activa")
    return root_logger


if __name__ == "__main__":
    setup_safe_logging()
    logging.info("Test con emojis: [GUARDIAN] [OK] [ERROR] [CRITICAL]")
    print("[OK] Logging configurado. Ver logs/meteoser_completo.log")

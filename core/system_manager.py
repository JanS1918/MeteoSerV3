from .logger import get_logger

logger = get_logger("SystemManager")

class SystemManager:
    def start(self):
        logger.info("System started")

    def stop(self):
        logger.info("System stopped")
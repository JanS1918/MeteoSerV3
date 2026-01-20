import logging


class LogEngine:
    """
    Logger simple para motores internos.
    Provee método log(nivel, mensaje).
    """

    def __init__(self, name: str = "meteoser") -> None:
        self._logger: logging.Logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def log(self, level: str, msg: str) -> None:
        level = (level or "info").lower()
        if level == "debug":
            self._logger.debug(msg)
        elif level == "warning":
            self._logger.warning(msg)
        elif level == "error":
            self._logger.error(msg)
        else:
            self._logger.info(msg)

    def get_logger(self) -> logging.Logger:
        return self._logger

from ..logger import get_logger

logger = get_logger("API")


def handle_request(data):
    logger.info(f"Handling request: {data}")
    return {"result": "ok"}

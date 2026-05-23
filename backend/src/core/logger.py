from loguru import logger

logger.remove()
logger.configure(extra={"log_id": "-"})
logger.add(
    "logs/app.log",
    format="{time} | {level} | {extra[log_id]} | {message}",
    level="INFO",
    rotation="10 MB",
    enqueue=True,
)